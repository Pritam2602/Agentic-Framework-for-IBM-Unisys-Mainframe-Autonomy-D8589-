"""Planner Agent API endpoints."""

from fastapi import APIRouter, HTTPException

from planner_agent import PlannerAgent, PlannerAgentRequest, PlannerAgentResponse

router = APIRouter(prefix="/api/planner", tags=["planner"])


@router.post("/run", response_model=PlannerAgentResponse)
async def run_planner_agent(request: PlannerAgentRequest):
    """Create an execution plan from intent and resolved context."""
    try:
        agent = PlannerAgent(enable_llm=request.use_llm)
        return agent.run(
            intent=request.intent,
            context=request.context,
            use_llm=request.use_llm,
            mode=request.mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health")
async def planner_health():
    """Planner Agent health check."""
    return {
        "status": "healthy",
        "service": "planner-agent",
        "llm_backed": True,
        "role": "planning-layer",
        "output": "execution_plan",
    }
