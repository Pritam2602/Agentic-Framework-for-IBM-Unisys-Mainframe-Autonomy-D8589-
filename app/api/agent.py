"""
Agent API endpoints with strict AgentResponse model
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
from app.agent.intent_parser import IntentParser
from app.agent.capability_matcher import CapabilityMatcher
from app.agent.command_selector import CommandSelector
from app.agent.execution_planner import ExecutionPlanner
from app.agent.reasoning_engine import ReasoningEngine
from app.catalog.catalog_service import CatalogService

router = APIRouter(prefix="/api/agent", tags=["agent"])
catalog_service = CatalogService()


def get_reasoning_engine() -> ReasoningEngine:
    """Initialize reasoning engine with dependencies"""
    commands = catalog_service.get_all_commands()
    capabilities = [
        "JCL Execution", "Dataset Management", "RACF Integration",
        "CICS Transaction Processing", "DB2 Query Execution"
    ]
    
    intent_parser = IntentParser()
    capability_matcher = CapabilityMatcher(capabilities)
    command_selector = CommandSelector(commands)
    execution_planner = ExecutionPlanner()
    
    return ReasoningEngine(intent_parser, capability_matcher, command_selector, execution_planner)


@router.post("/execute", response_model=AgentResponse)
async def execute_agent_query(request: AgentQueryRequest):
    """
    Execute agent query and return strict AgentResponse
    """
    try:
        reasoning_engine = get_reasoning_engine()
        
        # Process query through reasoning pipeline
        reasoning_result = reasoning_engine.process_query(request.query)
        
        # Mock execution
        mock_result = {"status": "completed", "records_found": 23, "execution_time_ms": 145}
        
        # Build canonical output
        canonical_output = CanonicalOutput(type="json", data=mock_result)
        
        # Build natural language response
        commands = reasoning_result.get("commands", [])
        command_names = [cmd["name"] for cmd in commands]
        natural_response = (
            f"I've processed your request: '{request.query}'. "
            f"Executed {len(commands)} command(s): {', '.join(command_names)}. "
            f"Found {mock_result['records_found']} results."
        )
        
        return AgentResponse(
            natural_response=natural_response,
            canonical_output=canonical_output,
            execution_trace=reasoning_result["execution_trace"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reasoning-stream")
async def reasoning_stream():
    """Stream reasoning logs via Server-Sent Events"""
    async def generate_events():
        messages = [
            ("intent_parsing", "Analyzing user request parameters"),
            ("capability_matching", "Checking user permissions for DATASET_CREATE"),
            ("command_selection", "User has required permissions"),
            ("execution_planning", "Proceeding with allocation on ZPROD01"),
            ("execution", "Executing ALLOC_DATASET command"),
            ("result_collection", "Dataset allocated: USER.NEW.DATASET")
        ]
        
        for stage, message in messages:
            trace = TraceEvent(timestamp=datetime.now(), stage=stage, message=message)
            data = json.dumps(trace.model_dump(), default=str)
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(generate_events(), media_type="text/event-stream")


@router.get("/status", response_model=AgentStatusModel)
async def get_agent_status():
    """Get current agent status"""
    return AgentStatusModel(
        id="ibm-agent-001", name="IBM z/OS Agent", status="online",
        capabilities=[
            "JCL Execution", "Dataset Management", "RACF Integration",
            "CICS Transaction Processing", "DB2 Query Execution"
        ],
        uptime=864000000, tasksCompleted=1547, lastActivity=datetime.now()
    )


@router.get("/executions", response_model=List[AgentExecutionModel])
async def get_agent_executions():
    """Get recent agent executions"""
    return [
        AgentExecutionModel(
            id="exec-001", taskId="task-1001", command="LISTCAT LEVEL(PROD.MASTER)",
            status="completed", startTime=datetime.now(), endTime=datetime.now(),
            result={"recordsFound": 234}
        ),
        AgentExecutionModel(
            id="exec-002", taskId="task-1002", command="SUBMIT JOB(PAYROLL)",
            status="running", startTime=datetime.now()
        )
    ]


@router.get("/config", response_model=AgentConfigModel)
async def get_agent_config():
    """Get agent configuration"""
    return AgentConfigModel(
        environment="z/OS 2.5", version="3.2.1", maxConcurrentTasks=10,
        timeout=300000, retryPolicy={"maxRetries": 3, "backoffMs": 5000}
    )
