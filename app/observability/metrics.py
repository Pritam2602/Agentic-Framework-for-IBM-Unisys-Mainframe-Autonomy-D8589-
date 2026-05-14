"""Prometheus metrics for pipeline observability."""

from __future__ import annotations

from typing import Any, Dict


try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover - fallback for environments without prometheus-client
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    PROMETHEUS_AVAILABLE = False

    class _NoopMetric:
        def labels(self, **_: Any) -> "_NoopMetric":
            return self

        def inc(self, *_: Any, **__: Any) -> None:
            return None

        def observe(self, *_: Any, **__: Any) -> None:
            return None

        def set(self, *_: Any, **__: Any) -> None:
            return None

    def Counter(*_: Any, **__: Any) -> _NoopMetric:
        return _NoopMetric()

    def Gauge(*_: Any, **__: Any) -> _NoopMetric:
        return _NoopMetric()

    def Histogram(*_: Any, **__: Any) -> _NoopMetric:
        return _NoopMetric()

    def generate_latest() -> bytes:
        return b""


pipeline_runs_total = Counter(
    "communicator_pipeline_runs_total",
    "Total pipeline runs",
    ["status"],
)
pipeline_duration_seconds = Histogram(
    "communicator_pipeline_duration_seconds",
    "End-to-end pipeline duration",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)
stage_duration_seconds = Histogram(
    "communicator_stage_duration_seconds",
    "Pipeline stage duration",
    ["stage", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)
intent_confidence_score = Gauge(
    "communicator_intent_confidence_score",
    "Latest intent confidence score",
)
context_confidence_score = Gauge(
    "communicator_context_confidence_score",
    "Latest context confidence score",
)
federation_confidence_score = Gauge(
    "communicator_federation_confidence_score",
    "Latest federation confidence score",
)
join_key_match_rate = Gauge(
    "communicator_join_key_match_rate",
    "Latest join key match rate",
)
amount_authority_violations_total = Counter(
    "communicator_amount_authority_violations_total",
    "Amount authority violations",
)
governance_violations_total = Counter(
    "communicator_governance_violations_total",
    "Governance violations",
)
llm_fallback_total = Counter(
    "communicator_llm_fallback_total",
    "LLM fallback events",
    ["stage"],
)
llm_tokens_total = Counter(
    "communicator_llm_tokens_total",
    "LLM tokens used",
    ["stage", "model", "kind"],
)
llm_cost_usd_total = Counter(
    "communicator_llm_cost_usd_total",
    "Estimated LLM cost in USD",
    ["stage", "model"],
)
records_normalized_total = Counter(
    "communicator_records_normalized_total",
    "Normalized records by source",
    ["source"],
)


def record_pipeline_metrics(run: Dict[str, Any]) -> None:
    status = str(run.get("status", "unknown"))
    pipeline_runs_total.labels(status=status).inc()
    pipeline_duration_seconds.observe(float(run.get("duration_ms") or 0) / 1000)
    for stage in run.get("stages", []):
        stage_duration_seconds.labels(
            stage=str(stage.get("stage")),
            status=str(stage.get("status")),
        ).observe(float(stage.get("duration_ms") or 0) / 1000)

    domain = run.get("domain_metrics") or {}
    _set_if_number(intent_confidence_score, domain.get("intent_confidence"))
    _set_if_number(context_confidence_score, domain.get("context_confidence"))
    _set_if_number(federation_confidence_score, domain.get("federation_confidence"))
    _set_if_number(join_key_match_rate, domain.get("join_key_match_rate"))

    violations = int(domain.get("amount_authority_violations") or 0)
    if violations:
        amount_authority_violations_total.inc(violations)
    governance = int(domain.get("governance_violations") or 0)
    if governance:
        governance_violations_total.inc(governance)
    if domain.get("llm_fallback"):
        llm_fallback_total.labels(stage="pipeline").inc()

    records = domain.get("records") or {}
    for source in ("ibm", "unisys"):
        count = int(records.get(source) or 0)
        if count:
            records_normalized_total.labels(source=source).inc(count)


def record_llm_metrics(usage: Dict[str, Any]) -> None:
    stage = str(usage.get("stage") or "unknown")
    model = str(usage.get("model") or "unknown")
    llm_tokens_total.labels(stage=stage, model=model, kind="input").inc(
        int(usage.get("input_tokens") or 0)
    )
    llm_tokens_total.labels(stage=stage, model=model, kind="output").inc(
        int(usage.get("output_tokens") or 0)
    )
    llm_tokens_total.labels(stage=stage, model=model, kind="total").inc(
        int(usage.get("total_tokens") or 0)
    )
    llm_cost_usd_total.labels(stage=stage, model=model).inc(
        float(usage.get("estimated_cost_usd") or 0.0)
    )


def _set_if_number(metric: Any, value: Any) -> None:
    if isinstance(value, (int, float)):
        metric.set(value)


def metrics_response() -> tuple[bytes, str]:
    if not PROMETHEUS_AVAILABLE:
        from app.observability import observability_store

        summary = observability_store.summary()
        pipeline = summary["pipeline"]
        lines = [
            "# HELP communicator_pipeline_runs_total Total pipeline runs retained by status.",
            "# TYPE communicator_pipeline_runs_total counter",
            f'communicator_pipeline_runs_total{{status="success"}} {pipeline["successful_runs"]}',
            f'communicator_pipeline_runs_total{{status="failed"}} {pipeline["failed_runs"]}',
            "# HELP communicator_pipeline_duration_ms Average retained pipeline duration in milliseconds.",
            "# TYPE communicator_pipeline_duration_ms gauge",
            f'communicator_pipeline_duration_ms {pipeline["average_duration_ms"]}',
            "# HELP communicator_pipeline_success_rate Retained pipeline success rate.",
            "# TYPE communicator_pipeline_success_rate gauge",
            f'communicator_pipeline_success_rate {pipeline["success_rate"]}',
        ]
        for stage, value in summary["stage_averages_ms"].items():
            lines.append(f'communicator_stage_duration_ms{{stage="{stage}"}} {value}')
        return ("\n".join(lines) + "\n").encode("utf-8"), CONTENT_TYPE_LATEST

    return generate_latest(), CONTENT_TYPE_LATEST
