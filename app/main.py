"""
COMMUNICATOR - Mainframe Agent Platform
FastAPI backend application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import asyncio
import json
from datetime import datetime
from pathlib import Path

from intent_agent.core import IntentAgent, init_model
from app.catalog.catalog_service import CatalogService
from app.models.schemas import *

# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------

app = FastAPI(
    title="COMMUNICATOR",
    description="AI-driven Mainframe Agent Platform",
    version="1.0.0"
)

# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "intent_agent" / "capability_catalog.json"

# -------------------------------------------------------------------
# Services
# -------------------------------------------------------------------

catalog_service = CatalogService()

# Initialize LLM model
model = init_model("gemini")

# Initialize IntentAgent
intent_agent = IntentAgent(
    catalog_path=str(CATALOG_PATH),
    model=model
)

# Store last execution trace
last_execution_trace = []

# -------------------------------------------------------------------
# Root / Health
# -------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "COMMUNICATOR",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# -------------------------------------------------------------------
# Catalog Endpoints
# -------------------------------------------------------------------

@app.get("/api/catalog/commands")
async def get_commands():
    try:
        return catalog_service.get_all_commands()
    except Exception as e:
        print("Catalog error:", e)
        return []


@app.get("/api/catalog/jobs")
async def get_jobs():
    try:
        return catalog_service.get_all_jobs()
    except Exception as e:
        print("Jobs error:", e)
        return []


@app.get("/api/catalog/workflows")
async def get_workflows():
    try:
        return catalog_service.get_all_workflows()
    except Exception as e:
        print("Workflow error:", e)
        return []


@app.get("/api/catalog/datasets")
async def get_datasets():
    try:
        return catalog_service.get_all_datasets()
    except Exception as e:
        print("Dataset error:", e)
        return []


@app.get("/api/catalog/stats")
async def get_stats():

    try:

        commands = catalog_service.get_all_commands()
        jobs = catalog_service.get_all_jobs()
        workflows = catalog_service.get_all_workflows()
        datasets = catalog_service.get_all_datasets()

        return {
            "totalCommands": len(commands),
            "totalJobs": len(jobs),
            "totalWorkflows": len(workflows),
            "totalDatasets": len(datasets),
            "lastUpdated": datetime.now().isoformat()
        }

    except Exception as e:

        print("Stats error:", e)

        return {
            "totalCommands": 0,
            "totalJobs": 0,
            "totalWorkflows": 0,
            "totalDatasets": 0,
            "lastUpdated": datetime.now().isoformat()
        }


# -------------------------------------------------------------------
# Agent Execution
# -------------------------------------------------------------------

@app.post("/api/agent/execute")
async def execute_agent(request: AgentQueryRequest):

    global last_execution_trace

    try:

        result = intent_agent.run(request.query)

        trace = [
            TraceEvent(
                timestamp=datetime.now(),
                stage="intent_parsing",
                message=f"Intent: {result.intent}"
            ),
            TraceEvent(
                timestamp=datetime.now(),
                stage="command_selection",
                message=f"Command: {result.zowe_command}"
            ),
        ]

        last_execution_trace = trace

        response = AgentResponse(
            natural_response=f"Intent: {result.intent}\nCommand: {result.zowe_command}",
            canonical_output=CanonicalOutput(
                type="json",
                data=result.model_dump()
            ),
            execution_trace=trace
        )

        return response

    except Exception as e:

        print("Agent error:", e)

        trace = [
            TraceEvent(
                timestamp=datetime.now(),
                stage="execution",
                message=str(e)
            )
        ]

        return AgentResponse(
            natural_response=f"Error: {str(e)}",
            canonical_output=CanonicalOutput(
                type="json",
                data={"error": str(e)}
            ),
            execution_trace=trace
        )


# -------------------------------------------------------------------
# Reasoning Stream
# -------------------------------------------------------------------

@app.get("/api/agent/reasoning-stream")
async def reasoning_stream():

    async def generate():

        if last_execution_trace:

            for event in last_execution_trace:

                data = json.dumps(event.model_dump(), default=str)

                yield f"data: {data}\n\n"

                await asyncio.sleep(0.5)

        else:

            event = TraceEvent(
                timestamp=datetime.now(),
                stage="waiting",
                message="Waiting for agent query..."
            )

            data = json.dumps(event.model_dump(), default=str)

            yield f"data: {data}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# -------------------------------------------------------------------
# Agent Status
# -------------------------------------------------------------------

@app.get("/api/agent/status")
async def get_agent_status():

    return {
        "id": "intent-agent-001",
        "name": "IBM z/OS IntentAgent",
        "status": "online",
        "model": "gemini",
        "catalogCommands": 30,
        "lastActivity": datetime.now().isoformat()
    }


# -------------------------------------------------------------------
# Run Server
# -------------------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )