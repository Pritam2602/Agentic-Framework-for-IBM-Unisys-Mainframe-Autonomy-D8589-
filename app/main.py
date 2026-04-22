"""
COMMUNICATOR - Data Federation Agent Platform
FastAPI backend application

Architecture:
  Intent Agent (WHAT) → Context Resolution Agent (WHERE) → Planner Agent (HOW)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

# Import new modular Intent Agent
from intent_agent import IntentAgent
from intent_agent.config import build_llm_model

from app.catalog.catalog_service import CatalogService
from app.models.schemas import *

# Import API routers
from app.api.intent import router as intent_router
from app.api.catalog import router as catalog_router
from app.api.agent import router as agent_router
from app.api.context import router as context_router
from app.api.pipeline import router as pipeline_router

# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------

app = FastAPI(
    title="COMMUNICATOR - Data Federation Platform",
    description=(
        "AI-driven Data Federation Platform integrating IBM Mainframe "
        "and Unisys MCP systems through an agentic architecture."
    ),
    version="2.0.0"
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

# -------------------------------------------------------------------
# Services
# -------------------------------------------------------------------

catalog_service = CatalogService()

# Initialize LLM model
model = build_llm_model()

# Initialize IntentAgent with new modular structure
intent_agent = IntentAgent(model=model)

# -------------------------------------------------------------------
# Include API Routers
# -------------------------------------------------------------------

app.include_router(intent_router)
app.include_router(catalog_router)
app.include_router(agent_router)
app.include_router(context_router)
app.include_router(pipeline_router)

# -------------------------------------------------------------------
# Root / Health
# -------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "COMMUNICATOR - Data Federation Platform",
        "version": "2.0.0",
        "status": "online",
        "architecture": {
            "intent_agent": "active",
            "context_resolution_agent": "active",
            "planner_agent": "planned",
            "execution_agents": "planned",
        },
        "endpoints": {
            "intent": "/api/intent/extract",
            "context": "/api/context/resolve",
            "pipeline": "/api/pipeline/run",
            "agent": "/api/agent/execute",
            "catalog": "/api/catalog/commands",
            "docs": "/docs",
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "intent_agent": "ready",
        "context_resolution_agent": "ready",
        "llm_model": "enabled" if model else "disabled"
    }


# -------------------------------------------------------------------
# Catalog Endpoints (kept for backward compatibility)
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
        print("Catalog error:", e)
        return []
