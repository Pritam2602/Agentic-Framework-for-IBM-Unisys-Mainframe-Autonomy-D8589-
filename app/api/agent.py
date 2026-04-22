"""
Agent API endpoints — REBUILT for correct architecture

OLD (WRONG):
  User Query → IntentParser → CapabilityMatcher → CommandSelector → ExecutionPlanner
  (Mixed intent understanding with Zowe command generation)

NEW (CORRECT):
  User Query → Intent Agent (WHAT) → Context Resolution Agent (WHERE) → Response
  (Strict separation of concerns — no command generation at this layer)

The Planner Agent (HOW) and Execution Agents (RUN) are downstream.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from datetime import datetime
import asyncio
import json

from app.models.schemas import (
    AgentQueryRequest, AgentResponse, AgentStatusModel,
    AgentExecutionModel, AgentConfigModel, CanonicalOutput, TraceEvent
)

# NEW: Import the correct agents
from intent_agent import IntentAgent
from intent_agent.config import build_llm_model
from context_resolution_agent import ContextResolutionAgent

router = APIRouter(prefix="/api/agent", tags=["agent"])


# ================================================================
# AGENT INITIALIZATION
# ================================================================

def _get_intent_agent() -> IntentAgent:
    """Initialize the Intent Agent with LLM model"""
    model = build_llm_model()
    return IntentAgent(model=model)


def _get_context_agent() -> ContextResolutionAgent:
    """Initialize the Context Resolution Agent"""
    return ContextResolutionAgent()


# ================================================================
# MAIN PIPELINE ENDPOINT
# ================================================================

@router.post("/execute", response_model=AgentResponse)
async def execute_agent_query(request: AgentQueryRequest):
    """
    Execute the agent pipeline: Intent → Context Resolution

    This replaces the old ReasoningEngine pipeline that incorrectly
    mapped queries directly to Zowe commands.

    Flow:
    1. Intent Agent parses user query → structured intent JSON
    2. Context Resolution Agent resolves WHERE data exists
    3. Response includes both intent and context for the Planner

    NOTE: This does NOT execute commands. The Planner Agent (future)
    will consume this output to decide HOW to execute.
    """
    try:
        trace_events: List[dict] = []

        # ---- Stage 1: Intent Parsing ----
        trace_events.append(TraceEvent(
            timestamp=datetime.now(),
            stage="intent_parsing",
            message=f"Parsing user query: '{request.query}'"
        ).model_dump(mode="json"))

        intent_agent = _get_intent_agent()
        intent = intent_agent.run(request.query)
        intent_dict = intent.model_dump()

        trace_events.append(TraceEvent(
            timestamp=datetime.now(),
            stage="intent_parsing",
            message=(
                f"Intent resolved: task={intent.task}, "
                f"entities={intent.entities}, systems={intent.systems}, "
                f"metric={intent.metric}, aggregation={intent.aggregation}, "
                f"confidence={intent.confidence_score:.2f}"
            ),
            metadata=intent_dict
        ).model_dump(mode="json"))

        # ---- Stage 2: Context Resolution ----
        trace_events.append(TraceEvent(
            timestamp=datetime.now(),
            stage="capability_matching",
            message="Resolving data context across IBM and Unisys systems"
        ).model_dump(mode="json"))

        context_agent = _get_context_agent()
        context = context_agent.resolve(intent_dict)
        context_dict = context.model_dump()

        trace_events.append(TraceEvent(
            timestamp=datetime.now(),
            stage="capability_matching",
            message=(
                f"Context resolved: systems={context.systems_checked}, "
                f"confidence={context.resolution_confidence:.2f}"
            ),
            metadata=context_dict
        ).model_dump(mode="json"))

        # ---- Stage 3: Build Response ----
        # The canonical output contains both intent + context for the Planner
        pipeline_result = {
            "intent": intent_dict,
            "context": context_dict,
            "pipeline_stage": "context_resolved",
            "next_stage": "planner_agent",
            "status": "ready_for_planning"
        }

        canonical_output = CanonicalOutput(type="json", data=pipeline_result)

        # Build human-readable summary
        ibm_info = ""
        if context.ibm:
            ibm_info = f"IBM: program={context.ibm.program}, dataset={context.ibm.dataset}"
        unisys_info = ""
        if context.unisys:
            unisys_info = f"Unisys: api={context.unisys.api}, fields={len(context.unisys.fields)}"

        system_summary = ", ".join(filter(None, [ibm_info, unisys_info]))

        natural_response = (
            f"Understood your request: '{request.query}'\n"
            f"Task: {intent.task} | Entities: {', '.join(intent.entities)}\n"
            f"Output: {intent.output_mode}"
            f"{f' | Metric: {intent.metric}' if intent.metric else ''}"
            f"{f' | Aggregation: {intent.aggregation}' if intent.aggregation else ''}\n"
            f"Data locations resolved: {system_summary}\n"
            f"Confidence: intent={intent.confidence_score:.0%}, "
            f"context={context.resolution_confidence:.0%}\n"
            f"Status: Ready for Planner Agent"
        )

        if context.warnings:
            natural_response += f"\nWarnings: {'; '.join(context.warnings)}"

        trace_events.append(TraceEvent(
            timestamp=datetime.now(),
            stage="execution_planning",
            message="Pipeline complete — context resolved, ready for Planner Agent",
            metadata={"warnings": context.warnings}
        ).model_dump(mode="json"))

        return AgentResponse(
            natural_response=natural_response,
            canonical_output=canonical_output,
            execution_trace=trace_events
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
# STREAMING ENDPOINT
# ================================================================

@router.get("/reasoning-stream")
async def reasoning_stream():
    """Stream reasoning steps via Server-Sent Events"""
    async def generate_events():
        steps = [
            ("intent_parsing", "Analyzing user query to extract structured intent"),
            ("intent_parsing", "Identified: task=fetch, entities=[payroll], systems=[ibm, unisys]"),
            ("capability_matching", "Resolving IBM context: COBOL catalog → JCL metadata → Zowe commands"),
            ("capability_matching", "Resolving Unisys context: MCP tools → schema discovery"),
            ("execution_planning", "Context resolved — ready for Planner Agent"),
            ("result_collection", "Pipeline complete: intent + context available for downstream agents"),
        ]

        for stage, message in steps:
            trace = TraceEvent(
                timestamp=datetime.now(),
                stage=stage,
                message=message
            )
            data = json.dumps(trace.model_dump(), default=str)
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(generate_events(), media_type="text/event-stream")


# ================================================================
# STATUS / CONFIG ENDPOINTS (Unchanged)
# ================================================================

@router.get("/status", response_model=AgentStatusModel)
async def get_agent_status():
    """Get current agent status"""
    return AgentStatusModel(
        id="federation-agent-001",
        name="Data Federation Agent",
        status="online",
        capabilities=[
            "Intent Parsing",
            "Context Resolution (IBM)",
            "Context Resolution (Unisys)",
            "MCP Tool Discovery",
            "COBOL Catalog Lookup",
            "JCL Metadata Resolution",
        ],
        uptime=864000000,
        tasksCompleted=1547,
        lastActivity=datetime.now()
    )


@router.get("/executions", response_model=List[AgentExecutionModel])
async def get_agent_executions():
    """Get recent pipeline executions"""
    return [
        AgentExecutionModel(
            id="exec-001",
            taskId="task-1001",
            command="Intent → Context Resolution (payroll, ibm+unisys)",
            status="completed",
            startTime=datetime.now(),
            endTime=datetime.now(),
            result={"entities_resolved": ["ibm:payroll", "unisys:payroll"], "confidence": 0.85}
        ),
        AgentExecutionModel(
            id="exec-002",
            taskId="task-1002",
            command="Intent → Context Resolution (transaction, ibm)",
            status="completed",
            startTime=datetime.now(),
            endTime=datetime.now(),
            result={"entities_resolved": ["ibm:transaction"], "confidence": 0.90}
        )
    ]


@router.get("/config", response_model=AgentConfigModel)
async def get_agent_config():
    """Get agent configuration"""
    return AgentConfigModel(
        environment="Federation Platform v1.0",
        version="2.0.0",
        maxConcurrentTasks=10,
        timeout=300000,
        retryPolicy={"maxRetries": 3, "backoffMs": 5000}
    )
