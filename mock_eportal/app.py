"""
Mock ePortal - Unisys MCP Simulation Server

A realistic FastAPI simulation of a Unisys ePortal system exposing:
- REST APIs for data access (/api/unisys/*)
- Schema discovery endpoints (/schema/*)
- MCP tool discovery (/mcp/tools)

Run: uvicorn mock_eportal.app:app --port 8001 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mock_eportal.routers import api_router, schema_router, mcp_router

# ================================================================
# APPLICATION
# ================================================================

app = FastAPI(
    title="Unisys ePortal Simulation",
    description=(
        "Mock ePortal simulating Unisys MCP mainframe systems. "
        "Provides REST APIs, schema discovery, and MCP tool manifests "
        "for the Data Federation Platform."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ================================================================
# CORS
# ================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# INCLUDE ROUTERS
# ================================================================

app.include_router(api_router)
app.include_router(schema_router)
app.include_router(mcp_router)

# ================================================================
# ROOT / HEALTH
# ================================================================

@app.get("/")
async def root():
    return {
        "service": "Unisys ePortal Simulation",
        "version": "1.0.0",
        "platform": "Unisys MCP",
        "status": "online",
        "endpoints": {
            "data": "/api/unisys/{payroll,customer,transaction}",
            "schema": "/schema/{payroll,customer,transaction}",
            "mcp": "/mcp/tools",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "eportal-simulation",
        "platform": "Unisys MCP",
        "data_loaded": True
    }
