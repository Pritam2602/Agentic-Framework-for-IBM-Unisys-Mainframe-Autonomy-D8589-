"""Execution Agent API endpoints."""

from fastapi import APIRouter, HTTPException

from execution_agent import ExecutionAgent, ExecutionAgentRequest, ExecutionAgentResponse

router = APIRouter(prefix="/api/execution", tags=["execution"])


@router.post("/run", response_model=ExecutionAgentResponse)
async def run_execution_agent(request: ExecutionAgentRequest):
    """Execute a Planner Agent JSON using the LLM-backed Execution Agent."""
    try:
        agent = ExecutionAgent()
        return agent.run(
            planner_json=request.planner_json,
            intent=request.intent,
            context=request.context,
            dry_run=request.dry_run,
            mode=request.mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health")
async def execution_health():
    """Execution Agent health check."""
    return {
        "status": "healthy",
        "service": "execution-agent",
        "mode": "safe_mock",
        "llm_backed": True,
    }
