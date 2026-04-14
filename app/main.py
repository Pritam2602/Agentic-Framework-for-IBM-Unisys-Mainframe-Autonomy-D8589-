"""
COMMUNICATOR - Mainframe Agent Platform
FastAPI backend application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import asyncio
from pathlib import Path

# Import new modular Intent Agent
from intent_agent import IntentAgent

from app.catalog.catalog_service import CatalogService
from app.models.schemas import *

# Import Intent API router
from app.api.intent import router as intent_router
from app.api.catalog import router as catalog_router

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

# -------------------------------------------------------------------
# Services
# -------------------------------------------------------------------

catalog_service = CatalogService()

# Initialize LLM model
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0
    )
except Exception as e:
    print(f"LLM initialization failed: {e}")
    model = None

# Initialize IntentAgent with new modular structure
intent_agent = IntentAgent(model=model)

# Store last execution trace
last_execution_trace = []

# -------------------------------------------------------------------
# Include API Routers
# -------------------------------------------------------------------

app.include_router(intent_router)
app.include_router(catalog_router)

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
    return {
        "status": "healthy",
        "intent-agent": "ready",
        "llm-model": "enabled" if model else "disabled"
    }



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
        print("Catalog error:", e)
        return []


