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
from functools import lru_cache

# Import repository and service
from app.repository.catalog_repository import CatalogRepository
from app.catalog.catalog_service import CatalogService

app = FastAPI(
    title="COMMUNICATOR",
    description="AI-driven Mainframe Agent Platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import models  
from app.models.schemas import *

# Initialize catalog service
catalog_service = CatalogService()

# Cache the commands since they don't change often
_commands_cache = None
_jobs_cache = None
_workflows_cache = None
_datasets_cache = None

def get_cached_commands():
    global _commands_cache
    if _commands_cache is None:
        _commands_cache = catalog_service.get_all_commands()
    return _commands_cache

def get_cached_jobs():
    global _jobs_cache
    if _jobs_cache is None:
        _jobs_cache = catalog_service.get_all_jobs()
    return _jobs_cache

def get_cached_workflows():
    global _workflows_cache
    if _workflows_cache is None:
        _workflows_cache = catalog_service.get_all_workflows()
    return _workflows_cache

def get_cached_datasets():
    global _datasets_cache
    if _datasets_cache is None:
        _datasets_cache = catalog_service.get_all_datasets()
    return _datasets_cache

@app.get("/")
async def root():
    return {"service": "COMMUNICATOR", "version": "1.0.0", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# CATALOG ENDPOINTS - Now using real database
@app.get("/api/catalog/commands")
async def get_commands():
    """Get all commands from database"""
    try:
        commands = get_cached_commands()
        return commands
    except Exception as e:
        print(f"Error fetching commands: {e}")
        return []

@app.get("/api/catalog/jobs")
async def get_jobs():
    """Get all jobs from simulation data"""
    try:
        return get_cached_jobs()
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []

@app.get("/api/catalog/workflows")
async def get_workflows():
    """Get all workflows from simulation data"""
    try:
        return get_cached_workflows()
    except Exception as e:
        print(f"Error fetching workflows: {e}")
        return []

@app.get("/api/catalog/datasets")
async def get_datasets():
    """Get all datasets from simulation data"""
    try:
        return get_cached_datasets()
    except Exception as e:
        print(f"Error fetching datasets: {e}")
        return []

@app.get("/api/catalog/stats")
async def get_stats():
    """Get catalog statistics from actual data"""
    try:
        return {
            "totalCommands": len(get_cached_commands()),
            "totalJobs": len(get_cached_jobs()),
            "totalWorkflows": len(get_cached_workflows()),
            "totalDatasets": len(get_cached_datasets()),
            "lastUpdated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {
            "totalCommands": 0,
            "totalJobs": 0,
            "totalWorkflows": 0,
            "totalDatasets": 0,
            "lastUpdated": datetime.now().isoformat()
        }

# AGENT ENDPOINTS
@app.post("/api/agent/execute")
async def execute_agent(request: AgentQueryRequest):
    # Mock agent execution with proper structure
    trace = [
        TraceEvent(timestamp=datetime.now(), stage="intent_parsing", 
                  message="Analyzing user query"),
        TraceEvent(timestamp=datetime.now(), stage="capability_matching",
                  message="Matched capabilities: JCL Execution"),
        TraceEvent(timestamp=datetime.now(), stage="command_selection",
                  message="Selected 1 command(s)"),
        TraceEvent(timestamp=datetime.now(), stage="execution_planning",
                  message="Execution plan ready"),
        TraceEvent(timestamp=datetime.now(), stage="execution",
                  message="Executed command: SUBMIT_JOB"),
        TraceEvent(timestamp=datetime.now(), stage="result_collection",
                  message="Results collected successfully"),
    ]
    
    response = AgentResponse(
        natural_response=f"I processed your request: '{request.query}'. Found 23 results.",
        canonical_output=CanonicalOutput(
            type="json",
            data={"status": "completed", "records": 23, "execution_time_ms": 145}
        ),
        execution_trace=trace
    )
    return response

@app.get("/api/agent/reasoning-stream")
async def reasoning_stream():
    """SSE stream of reasoning events"""
    async def generate():
        messages = [
            ("intent_parsing", "Analyzing user request"),
            ("capability_matching", "Matching to capabilities"),
            ("command_selection", "Selecting commands"),
            ("execution_planning", "Planning execution"),
            ("execution", "Executing commands"),
            ("result_collection", "Collecting results"),
        ]
        for stage, msg in messages:
            event = TraceEvent(timestamp=datetime.now(), stage=stage, message=msg)
            data = json.dumps(event.model_dump(), default=str)
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/api/agent/status")
async def get_agent_status():
    return {
        "id": "agent-001", "name": "IBM z/OS Agent", "status": "online",
        "capabilities": ["JCL Execution", "Dataset Management"],
        "uptime": 864000000, "tasksCompleted": 1547, "lastActivity": datetime.now().isoformat()
    }

@app.get("/api/agent/executions")
async def get_executions():
    return [
        {"id": "exec-001", "taskId": "task-1001", "command": "LISTCAT",
         "status": "completed", "startTime": datetime.now().isoformat()}
    ]

@app.get("/api/agent/config")
async def get_config():
    return {
        "environment": "z/OS 2.5", "version": "3.2.1", "maxConcurrentTasks": 10,
        "timeout": 300000, "retryPolicy": {"maxRetries": 3, "backoffMs": 5000}
    }

# BANKING ENDPOINT (Minimal - full logic in separate module)
@app.post("/api/banking/loan/process")
async def process_loan(application: LoanApplicationRequest):
    # Simplified loan processing
    trace = [TraceEvent(timestamp=datetime.now(), stage="execution", message="Processing loan application")]
    
    eligible = application.age >= 21 and application.credit_score >= 650
    
    return {
        "application_id": "APP-12345",
        "status": "approved" if eligible else "rejected",
        "eligibility": {"eligible": eligible, "max_loan_amount": 250000.0, "recommended_term": 60},
        "execution_trace": [t.model_dump() for t in trace]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
