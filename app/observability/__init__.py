"""Observability utilities for COMMUNICATOR."""

from __future__ import annotations

import datetime as _dt
import contextvars
import time
from collections import Counter, deque
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from .live import publish_event
from .otel import trace_span


MAX_RUNS = 100
TARGET_PIPELINE_MS = 2000.0
TARGET_JOIN_MATCH_RATE = 0.99

_current_llm_stage: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_llm_stage",
    default="llm.invoke",
)


def utc_now_iso() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def perf_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def get_current_llm_stage() -> str:
    """Return the active pipeline stage for nested LLM calls."""
    return _current_llm_stage.get()


class PipelineTelemetry:
    """Collect stage observations for a single pipeline request."""

    def __init__(self, request_id: str, user_query: str) -> None:
        self.request_id = request_id
        self.user_query = user_query
        self.started_at = utc_now_iso()
        self._start = time.perf_counter()
        self.stages: List[Dict[str, Any]] = []
        self.failed_stage: Optional[str] = None

    @contextmanager
    def stage(self, name: str, **metadata: Any) -> Iterator[Dict[str, Any]]:
        stage_data: Dict[str, Any] = dict(metadata)
        start = time.perf_counter()
        try:
            publish_event(
                {
                    "type": "stage_started",
                    "request_id": self.request_id,
                    "stage": name,
                    "timestamp": utc_now_iso(),
                    "metadata": stage_data,
                }
            )
            from .langsmith_tracing import trace_context

            with trace_span(f"pipeline.{name}", request_id=self.request_id, **metadata):
                with trace_context(f"pipeline.{name}", request_id=self.request_id, **metadata):
                    token = _current_llm_stage.set(name)
                    try:
                        yield stage_data
                    finally:
                        _current_llm_stage.reset(token)
        except Exception as exc:
            self.failed_stage = name
            stage = {
                "stage": name,
                "status": "failed",
                "duration_ms": perf_ms(start),
                "metadata": stage_data,
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }
            self.stages.append(stage)
            publish_event(
                {
                    "type": "stage_failed",
                    "request_id": self.request_id,
                    "timestamp": utc_now_iso(),
                    **stage,
                }
            )
            raise
        else:
            stage = {
                "stage": name,
                "status": "success",
                "duration_ms": perf_ms(start),
                "metadata": stage_data,
            }
            self.stages.append(stage)
            publish_event(
                {
                    "type": "stage_completed",
                    "request_id": self.request_id,
                    "timestamp": utc_now_iso(),
                    **stage,
                }
            )

    def finish(
        self,
        status: str,
        domain_metrics: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        total_duration = perf_ms(self._start)
        return {
            "request_id": self.request_id,
            "user_query": self.user_query,
            "started_at": self.started_at,
            "finished_at": utc_now_iso(),
            "status": status,
            "duration_ms": total_duration,
            "target_ms": TARGET_PIPELINE_MS,
            "latency_status": "pass" if total_duration <= TARGET_PIPELINE_MS else "warn",
            "failed_stage": self.failed_stage,
            "stages": self.stages,
            "domain_metrics": domain_metrics or {},
            "errors": errors or [],
        }


class ObservabilityStore:
    """In-memory run history and aggregate metrics."""

    def __init__(self) -> None:
        self._runs: deque[Dict[str, Any]] = deque(maxlen=MAX_RUNS)
        self._status_counts: Counter[str] = Counter()
        self._stage_failures: Counter[str] = Counter()

    def record_run(self, run: Dict[str, Any]) -> None:
        self._runs.appendleft(run)
        self._status_counts[str(run.get("status", "unknown"))] += 1
        failed_stage = run.get("failed_stage")
        if failed_stage:
            self._stage_failures[str(failed_stage)] += 1
        try:
            from .storage import save_pipeline_run

            save_pipeline_run(run)
        except Exception:
            pass
        publish_event({"type": "pipeline_finished", **run})

    def recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        runs = list(self._runs)[:limit]
        if runs:
            return runs
        try:
            from .storage import load_recent_pipeline_runs

            return load_recent_pipeline_runs(limit)
        except Exception:
            return []

    def summary(self) -> Dict[str, Any]:
        runs = list(self._runs)
        total = len(runs)
        successful = sum(1 for run in runs if run.get("status") == "success")
        failed = sum(1 for run in runs if run.get("status") == "failed")
        durations = [float(run.get("duration_ms") or 0) for run in runs]
        avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0
        latest = runs[0] if runs else None

        stage_totals: Dict[str, List[float]] = {}
        for run in runs:
            for stage in run.get("stages", []):
                stage_totals.setdefault(stage["stage"], []).append(float(stage.get("duration_ms") or 0))

        stage_averages = {
            stage: round(sum(values) / len(values), 2)
            for stage, values in stage_totals.items()
            if values
        }

        return {
            "service": "pipeline-observability",
            "status": "healthy",
            "retention": {"max_runs": MAX_RUNS, "stored_runs": total},
            "pipeline": {
                "total_runs": total,
                "successful_runs": successful,
                "failed_runs": failed,
                "success_rate": round(successful / total, 3) if total else 1.0,
                "average_duration_ms": avg_duration,
                "target_duration_ms": TARGET_PIPELINE_MS,
            },
            "stage_averages_ms": stage_averages,
            "stage_failures": dict(self._stage_failures),
            "latest_run": latest,
        }


observability_store = ObservabilityStore()


def build_domain_metrics(
    intent: Dict[str, Any],
    context: Dict[str, Any],
    execution: Optional[Dict[str, Any]],
    normalization: Optional[Dict[str, Any]],
    federation: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    records = (normalization or {}).get("records") or []
    ibm_customers = {
        str(record.get("customer_id"))
        for record in records
        if record.get("source_system") == "ibm" and record.get("customer_id") is not None
    }
    unisys_customers = {
        str(record.get("customer_id"))
        for record in records
        if record.get("source_system") == "unisys" and record.get("customer_id") is not None
    }
    if ibm_customers and unisys_customers:
        join_match_rate = len(ibm_customers & unisys_customers) / len(ibm_customers | unisys_customers)
    elif records:
        join_match_rate = 1.0
    else:
        join_match_rate = 0.0

    governance = (federation or {}).get("governance") or {}
    reconciliation = governance.get("amount_reconciliation") or {}
    amount_authority_violations = 0 if governance.get("double_counting_protected", True) else 1
    if reconciliation and "IBM amount for total_spend" not in str(reconciliation.get("rule", "")):
        amount_authority_violations += 1

    context_warnings = context.get("warnings") or []
    normalized_summary = (normalization or {}).get("summary") or {}
    normalized_warnings = normalized_summary.get("warnings") or []
    llm_fallback = any(
        "fallback" in str(item).lower()
        for item in [*context_warnings, *normalized_warnings, governance.get("llm_refinement")]
    )

    return {
        "intent_confidence": intent.get("confidence_score"),
        "context_confidence": context.get("resolution_confidence"),
        "federation_confidence": (federation or {}).get("overall_confidence"),
        "records": {
            "normalized_total": normalized_summary.get("total_records", 0),
            "ibm": normalized_summary.get("ibm_records", 0),
            "unisys": normalized_summary.get("unisys_records", 0),
        },
        "join_key_match_rate": round(join_match_rate, 3),
        "join_key_status": "pass" if join_match_rate >= TARGET_JOIN_MATCH_RATE else "warn",
        "amount_authority_violations": amount_authority_violations,
        "amount_authority_status": "pass" if amount_authority_violations == 0 else "fail",
        "governance_violations": amount_authority_violations,
        "llm_fallback": llm_fallback,
        "execution_status": (execution or {}).get("status"),
        "systems_checked": context.get("systems_checked", []),
        "entities": intent.get("entities", []),
    }
