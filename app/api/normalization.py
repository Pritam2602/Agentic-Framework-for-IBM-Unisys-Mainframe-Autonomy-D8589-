"""Normalization Agent API endpoints."""

from fastapi import APIRouter, HTTPException

from normalization_agent import (
    NormalizationAgent,
    NormalizationAgentRequest,
    NormalizationAgentResponse,
)

router = APIRouter(prefix="/api/normalization", tags=["normalization"])


@router.post("/run", response_model=NormalizationAgentResponse)
async def run_normalization_agent(request: NormalizationAgentRequest):
    """Normalize execution outputs into the common intermediate schema."""
    try:
        agent = NormalizationAgent()
        return agent.run(
            execution_output=request.execution_output,
            intent=request.intent,
            context=request.context,
            use_llm=request.use_llm,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health")
async def normalization_health():
    """Normalization Agent health check."""
    return {
        "status": "healthy",
        "service": "normalization-agent",
        "llm_backed": True,
        "canonical_schema": "common-intermediate-record-v1",
    }
