"""
app/api/pipeline.py - Full Pipeline API (Intent → Context in one call)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    """Request for full pipeline execution"""
    user_query: str
    enable_llm: bool = True


class PipelineResponse(BaseModel):
    """Full pipeline response with intent + context"""
    intent: Dict[str, Any]
    context: Dict[str, Any]
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
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                model = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0
                )
            except Exception:
                model = None
        else:
            model = None

        intent_agent = IntentAgent(model=model)
        intent = intent_agent.run(request.user_query)
        intent_dict = intent.model_dump()

        # Step 2: Context Resolution Agent
        from context_resolution_agent import ContextResolutionAgent

        context_agent = ContextResolutionAgent()
        context = context_agent.resolve(intent_dict)
        context_dict = context.model_dump()

        # Build summary
        ibm_summary = ""
        if context.ibm:
            ibm_summary = f"IBM: {context.ibm.program or 'N/A'} → {context.ibm.dataset or 'N/A'}"
        unisys_summary = ""
        if context.unisys:
            unisys_summary = f"Unisys: {context.unisys.api or 'N/A'}"
        
        system_parts = [s for s in [ibm_summary, unisys_summary] if s]
        summary = (
            f"Query: {request.user_query}\n"
            f"Intent: {intent.task} on {', '.join(intent.entities)} "
            f"(confidence: {intent.confidence_score:.0%})\n"
            f"Context: {' | '.join(system_parts) or 'No systems resolved'} "
            f"(confidence: {context.resolution_confidence:.0%})"
        )

        return PipelineResponse(
            intent=intent_dict,
            context=context_dict,
            pipeline_stage="context_resolved",
            next_stage="planner_agent",
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
            "planner_agent": "not_implemented",
            "execution_agents": "not_implemented",
        }
    }
