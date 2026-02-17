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

# Minimal mock data
MOCK_COMMANDS = [
    {"id": "cmd-001", "name": "LISTCAT", "type": "query", "family": "DATASET", 
     "preconditions": ["RACF_AUTH"], "outputType": "JSON", 
     "description": "List catalog entries", "createdAt": "2024-01-15T00:00:00", "updatedAt": "2024-02-01T00:00:00"},
    {"id": "cmd-002", "name": "SUBMIT_JOB", "type": "batch", "family": "JOB",
     "preconditions": ["JOB_AUTH"], "outputType": "STREAM",
     "description": "Submit JCL job", "createdAt": "2024-01-20T00:00:00", "updatedAt": "2024-01-28T00:00:00"},
]

MOCK_JOBS = [
    {"id": "job-001", "name": "PAYROLL_BATCH", "scope": "enterprise", "mainframe": "ZPROD01",
     "type": "JCL", "accessLevel": "restricted", "status": "active", "lastRun": "2024-02-09T03:00:00"},
]

MOCK_WORKFLOWS = [
    {"id": "wf-001", "name": "ETL_PIPELINE", "scope": "enterprise", "mainframe": "ZPROD01",
     "type": "WORKFLOW", "accessLevel": "admin", "status": "active", "lastRun": "2024-02-10T00:00:00",
     "steps": 5, "dependencies": ["DATASET.EXTRACT"]},
]

MOCK_DATASETS = [
    {"id": "ds-001", "name": "PROD.MASTER.DATA", "scope": "enterprise", "mainframe": "ZPROD01",
     "type": "DATASET", "accessLevel": "read-only", "size": "2.4 GB", "records": 1500000},
]

@app.get("/")
async def root():
    return {"service": "COMMUNICATOR", "version": "1.0.0", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# CATALOG ENDPOINTS  
@app.get("/api/catalog/commands")
async def get_commands():
    return MOCK_COMMANDS

@app.get("/api/catalog/jobs")
async def get_jobs():
    return MOCK_JOBS

@app.get("/api/catalog/workflows")
async def get_workflows():
    return MOCK_WORKFLOWS

@app.get("/api/catalog/datasets")
async def get_datasets():
    return MOCK_DATASETS

@app.get("/api/catalog/stats")
async def get_stats():
    return {
        "totalCommands": len(MOCK_COMMANDS),
        "totalJobs": len(MOCK_JOBS),
        "totalWorkflows": len(MOCK_WORKFLOWS),
        "totalDatasets": len(MOCK_DATASETS),
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
