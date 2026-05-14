"""
app/api/pipeline.py - Full Pipeline API with observability.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.observability import (
    PipelineTelemetry,
    build_domain_metrics,
    observability_store,
)
from app.observability.langsmith_tracing import trace_context
from app.observability.metrics import record_pipeline_metrics
from app.observability.reasoning import build_stage_reasoning
from intent_agent.config import build_llm_model


router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    """Request for full pipeline execution."""

    user_query: str
    enable_llm: bool = True


class PipelineResponse(BaseModel):
    """Full pipeline response across the agent architecture."""

    intent: Dict[str, Any]
    context: Dict[str, Any]
    planner_json: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    normalization: Optional[Dict[str, Any]] = None
    federation_intelligence: Optional[Dict[str, Any]] = None
    pipeline_stage: str
    next_stage: str
    summary: str
    request_id: str
    total_duration_ms: float
    stage_timings: Dict[str, float]
    stage_reasoning: Dict[str, List[str]]
    pipeline_status: str
    errors: List[Dict[str, Any]]
    observability: Dict[str, Any]


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest, http_request: Request):
    """
    Run the full pipeline with stage timings, request correlation, and domain checks.
    """

    request_id = getattr(http_request.state, "request_id", None) or f"pipe-{uuid.uuid4().hex[:12]}"
    telemetry = PipelineTelemetry(request_id=request_id, user_query=request.user_query)
    errors: List[Dict[str, Any]] = []

    intent_dict: Dict[str, Any] = {}
    context_dict: Dict[str, Any] = {}
    planner_json: Optional[Dict[str, Any]] = None
    execution_dict: Optional[Dict[str, Any]] = None
    normalization_dict: Optional[Dict[str, Any]] = None
    fed_dict: Optional[Dict[str, Any]] = None

    try:
        with trace_context("pipeline.run", request_id=request_id, query=request.user_query):
            from intent_agent import IntentAgent

            with telemetry.stage("intent", query_length=len(request.user_query), llm_enabled=request.enable_llm) as stage:
                model = build_llm_model() if request.enable_llm else None
                intent_agent = IntentAgent(model=model)
                intent = intent_agent.run(request.user_query)
                intent_dict = intent.model_dump()
                stage.update(
                    {
                        "task": intent.task,
                        "entities": intent.entities,
                        "confidence": intent.confidence_score,
                        "requires_federation": intent.requires_federation,
                    }
                )

            from context_resolution_agent import ContextResolutionAgent

            with telemetry.stage("context_resolution", llm_enabled=request.enable_llm) as stage:
                context_agent = ContextResolutionAgent(enable_llm=request.enable_llm)
                context = await context_agent.resolve_async(intent_dict)
                context_dict = context.model_dump()
                stage.update(
                    {
                        "systems_checked": context.systems_checked,
                        "entities_resolved": context.entities_resolved,
                        "confidence": context.resolution_confidence,
                        "warnings": len(context.warnings),
                    }
                )

            from planner_agent import PlannerAgent

            with telemetry.stage("planner", llm_enabled=request.enable_llm) as stage:
                planner_agent = PlannerAgent(enable_llm=request.enable_llm)
                planner_result = planner_agent.run(
                    intent=intent_dict,
                    context=context_dict,
                    use_llm=request.enable_llm,
                    mode="safe_mock",
                )
                planner_json = planner_result.canonical_output
                stage.update(
                    {
                        "status": planner_result.status,
                        "steps": len(planner_result.plan.steps),
                        "warnings": len(planner_result.warnings),
                    }
                )

            from execution_agent import ExecutionAgent

            with telemetry.stage("execution", llm_enabled=request.enable_llm) as stage:
                execution_agent = ExecutionAgent(enable_llm=request.enable_llm)
                execution_result = execution_agent.run(
                    planner_json=planner_json,
                    intent=intent_dict,
                    context=context_dict,
                    dry_run=False,
                    mode="safe_mock",
                )
                execution_dict = execution_result.model_dump(mode="json")
                stage.update(
                    {
                        "status": execution_result.status,
                        "steps_executed": len(execution_result.step_results),
                        "step_results": len(execution_result.step_results),
                        "warnings": len(execution_result.warnings),
                    }
                )

            from normalization_agent import NormalizationAgent

            with telemetry.stage("normalization", llm_enabled=request.enable_llm) as stage:
                normalization_agent = NormalizationAgent(enable_llm=request.enable_llm)
                normalization_result = normalization_agent.run(
                    execution_output=execution_dict,
                    intent=intent_dict,
                    context=context_dict,
                    use_llm=request.enable_llm,
                )
                normalization_dict = normalization_result.model_dump(mode="json")
                stage.update(
                    {
                        "total_records": normalization_result.summary.total_records,
                        "ibm_records": normalization_result.summary.ibm_records,
                        "unisys_records": normalization_result.summary.unisys_records,
                        "warnings": len(normalization_result.summary.warnings),
                    }
                )

            from federation_intelligence import run_federation_intelligence

            with telemetry.stage("federation_intelligence", llm_enabled=request.enable_llm) as stage:
                fed_result = run_federation_intelligence(
                    intent=intent_dict,
                    context=context_dict,
                    normalized_output=normalization_dict,
                    execute=True,
                    enable_llm=request.enable_llm,
                )
                fed_dict = fed_result.model_dump()
                stage.update(
                    {
                        "relationships": len(fed_result.entity_relationships),
                        "views_evaluated": len(fed_result.recommended_views),
                        "confidence": fed_result.overall_confidence,
                        "suggested_explorations": len(fed_result.suggested_explorations),
                        "llm_refinement": fed_result.governance.get("llm_refinement"),
                    }
                )

        assert planner_json is not None
        assert execution_dict is not None
        assert normalization_dict is not None
        assert fed_dict is not None

        domain_metrics = build_domain_metrics(
            intent=intent_dict,
            context=context_dict,
            execution=execution_dict,
            normalization=normalization_dict,
            federation=fed_dict,
        )
        observability = telemetry.finish(
            status="success",
            domain_metrics=domain_metrics,
            errors=errors,
        )
        observability_store.record_run(observability)
        record_pipeline_metrics(observability)

        stage_reasoning = build_stage_reasoning(
            intent=intent_dict,
            context=context_dict,
            planner=planner_json,
            execution=execution_dict,
            normalization=normalization_dict,
            federation=fed_dict,
        )

        summary = _build_summary(
            request_id=request_id,
            user_query=request.user_query,
            intent=intent_dict,
            context=context_dict,
            planner_json=planner_json,
            execution=execution_dict,
            normalization=normalization_dict,
            federation=fed_dict,
        )

        return PipelineResponse(
            intent=intent_dict,
            context=context_dict,
            planner_json=planner_json,
            execution=execution_dict,
            normalization=normalization_dict,
            federation_intelligence=fed_dict,
            pipeline_stage="consumer_ready",
            next_stage="consumer_layer",
            summary=summary,
            request_id=request_id,
            total_duration_ms=observability["duration_ms"],
            stage_timings={
                stage["stage"]: stage["duration_ms"]
                for stage in observability["stages"]
            },
            stage_reasoning=stage_reasoning,
            pipeline_status="success",
            errors=errors,
            observability=observability,
        )

    except Exception as exc:
        errors.append(
            {
                "stage": telemetry.failed_stage or "pipeline",
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
        )
        observability = telemetry.finish(status="failed", errors=errors)
        observability_store.record_run(observability)
        record_pipeline_metrics(observability)
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Pipeline execution failed: {exc}",
                "request_id": request_id,
                "failed_stage": observability.get("failed_stage"),
                "errors": errors,
            },
        )


def _build_summary(
    request_id: str,
    user_query: str,
    intent: Dict[str, Any],
    context: Dict[str, Any],
    planner_json: Dict[str, Any],
    execution: Dict[str, Any],
    normalization: Dict[str, Any],
    federation: Dict[str, Any],
) -> str:
    ibm = context.get("ibm") or {}
    unisys = context.get("unisys") or {}
    ibm_summary = ""
    if ibm:
        ibm_summary = f"IBM: {ibm.get('program') or 'N/A'} -> {ibm.get('dataset') or 'N/A'}"
    unisys_summary = ""
    if unisys:
        unisys_summary = f"Unisys: {unisys.get('api') or 'N/A'}"

    top_view = federation.get("top_view") or {}
    discovery = federation.get("capability_discovery", {})
    related = discovery.get("related_capabilities", [])
    available_related = [
        item.get("entity")
        for item in related
        if item.get("status") == "available"
    ]
    missing_related = [
        item.get("entity")
        for item in related
        if item.get("status") != "available"
    ]
    system_parts = [part for part in [ibm_summary, unisys_summary] if part]
    plan_steps = ((planner_json.get("plan") or {}).get("steps") or planner_json.get("steps") or [])
    normalized_summary = normalization.get("summary") or {}
    metric_part = f" | Metric: {intent.get('metric')}" if intent.get("metric") else ""
    aggregation_part = f" | Aggregation: {intent.get('aggregation')}" if intent.get("aggregation") else ""

    return (
        f"Request ID: {request_id}\n"
        f"Query: {user_query}\n"
        f"Intent: {intent.get('task')} on {', '.join(intent.get('entities') or [])} "
        f"(confidence: {_percent(intent.get('confidence_score'))})\n"
        f"Output: {intent.get('output_mode')}"
        f"{metric_part}"
        f"{aggregation_part}"
        f"{' | Federation required' if intent.get('requires_federation') else ''}\n"
        f"Context: {' | '.join(system_parts) or 'No systems resolved'} "
        f"(confidence: {_percent(context.get('resolution_confidence'))})\n"
        f"Planning: {planner_json.get('status', 'ready')} | Steps: {len(plan_steps)}\n"
        f"Execution: {execution.get('status')} | "
        f"Normalized records: {normalized_summary.get('total_records', 0)}\n"
        f"Federation: {len(federation.get('entity_relationships') or [])} relationships found | "
        f"Top view: '{top_view.get('name') or top_view.get('view_id') or 'N/A'}' | "
        f"Confidence: {_percent(federation.get('overall_confidence'))}\n"
        f"Discovery: suggested follow-ups are available in the Federation panel | "
        f"metadata signals: {', '.join(available_related) or 'none'} | "
        f"unavailable: {', '.join(missing_related) or 'none'}"
    )


def _percent(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.0%}"
    return "N/A"


@router.get("/health")
async def pipeline_health():
    """Pipeline health check."""
    return {
        "status": "healthy",
        "service": "federation-pipeline",
        "stages": {
            "intent_agent": "ready",
            "context_resolution_agent": "ready",
            "federation_intelligence": "ready",
            "planner_agent": "ready",
            "execution_agents": "ready",
            "normalization_agent": "ready",
        },
    }
