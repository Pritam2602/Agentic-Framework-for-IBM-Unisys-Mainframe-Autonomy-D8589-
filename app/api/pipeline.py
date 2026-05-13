"""
app/api/pipeline.py - Full Pipeline API (Intent → Context → Federation Intelligence)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from intent_agent.config import build_llm_model

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    """Request for full pipeline execution"""
    user_query: str
    enable_llm: bool = True


class PipelineResponse(BaseModel):
    """Full pipeline response across the agent architecture"""
    intent: Dict[str, Any]
    context: Dict[str, Any]
    planner_json: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    normalization: Optional[Dict[str, Any]] = None
    federation_intelligence: Optional[Dict[str, Any]] = None
    pipeline_stage: str
    next_stage: str
    summary: str


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Run the full pipeline: user query → intent → context resolution
    
    This is the primary API for the dashboard. It runs:
    1. Intent Agent: Parse natural language → structured intent
    2. Context Resolution Agent: Resolve WHERE data exists
    
    The output is ready for the Planner Agent (future).
    
    Usage:
        POST /api/pipeline/run
        { "user_query": "Show me payroll data for March 2026" }
    """
    try:
        # Step 1: Intent Agent
        from intent_agent import IntentAgent

        if request.enable_llm:
            model = build_llm_model()
        else:
            model = None

        intent_agent = IntentAgent(model=model)
        intent = intent_agent.run(request.user_query)
        intent_dict = intent.model_dump()

        # Step 2: Context Resolution Agent
        from context_resolution_agent import ContextResolutionAgent

        context_agent = ContextResolutionAgent(enable_llm=request.enable_llm)
        context = await context_agent.resolve_async(intent_dict)
        context_dict = context.model_dump()

        # Step 3: Planner Agent
        from planner_agent import PlannerAgent

        planner_agent = PlannerAgent(enable_llm=request.enable_llm)
        planner_result = planner_agent.run(
            intent=intent_dict,
            context=context_dict,
            use_llm=request.enable_llm,
            mode="safe_mock",
        )
        planner_json = planner_result.canonical_output

        # Step 4: Execution Agent
        from execution_agent import ExecutionAgent

        execution_agent = ExecutionAgent(enable_llm=request.enable_llm)
        execution_result = execution_agent.run(
            planner_json=planner_json,
            intent=intent_dict,
            context=context_dict,
            dry_run=False,
            mode="safe_mock",
        )
        execution_dict = execution_result.model_dump(mode="json")

        # Step 5: Normalization Agent
        from normalization_agent import NormalizationAgent

        normalization_agent = NormalizationAgent(enable_llm=request.enable_llm)
        normalization_result = normalization_agent.run(
            execution_output=execution_dict,
            intent=intent_dict,
            context=context_dict,
            use_llm=request.enable_llm,
        )
        normalization_dict = normalization_result.model_dump(mode="json")

        # Step 6: Federation Intelligence Layer consumes normalized output
        from federation_intelligence import run_federation_intelligence

        fed_result = run_federation_intelligence(
            intent=intent_dict,
            context=context_dict,
            normalized_output=normalization_dict,
            execute=True,
            enable_llm=request.enable_llm,
        )
        fed_dict = fed_result.model_dump()

        # Build summary
        ibm_summary = ""
        if context.ibm:
            ibm_summary = f"IBM: {context.ibm.program or 'N/A'} → {context.ibm.dataset or 'N/A'}"
        unisys_summary = ""
        if context.unisys:
            unisys_summary = f"Unisys: {context.unisys.api or 'N/A'}"

        top_view_name = fed_result.top_view.name if fed_result.top_view else "N/A"
        discovery = fed_dict.get("capability_discovery", {})
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
        system_parts = [s for s in [ibm_summary, unisys_summary] if s]
        summary = (
            f"Query: {request.user_query}\n"
            f"Intent: {intent.task} on {', '.join(intent.entities)} "
            f"(confidence: {intent.confidence_score:.0%})\n"
            f"Output: {intent.output_mode}"
            f"{f' | Metric: {intent.metric}' if intent.metric else ''}"
            f"{f' | Aggregation: {intent.aggregation}' if intent.aggregation else ''}"
            f"{' | Federation required' if intent.requires_federation else ''}\n"
            f"Context: {' | '.join(system_parts) or 'No systems resolved'} "
            f"(confidence: {context.resolution_confidence:.0%})\n"
            f"Planning: {planner_result.status} | "
            f"Steps: {len(planner_result.plan.steps)}\n"
            f"Execution: {execution_result.status} | "
            f"Normalized records: {normalization_result.summary.total_records}\n"
            f"Federation: {len(fed_result.entity_relationships)} relationships found | "
            f"Top view: '{top_view_name}' | "
            f"Confidence: {fed_result.overall_confidence:.0%}\n"
            f"Discovery: available related data: {', '.join(available_related) or 'none'} | "
            f"not found: {', '.join(missing_related) or 'none'}"
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
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@router.get("/health")
async def pipeline_health():
    """Pipeline health check"""
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
        }
    }
