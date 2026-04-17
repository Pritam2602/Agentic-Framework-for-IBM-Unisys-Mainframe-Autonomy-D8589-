"""
Mock ePortal - Unisys MCP Simulation Server

A realistic FastAPI simulation of a Unisys ePortal system exposing:
- REST APIs for data access (/api/unisys/*)
- Schema discovery endpoints (/schema/*)
- MCP tool discovery (/mcp/tools)
- Federation metadata (/api/unisys/federation-metadata)

Aligned with AWS CardDemo (Customer, Account, Card, Transaction entities)

Run: uvicorn mock_eportal.app:app --port 8001 --reload
"""

from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Allow `python mock_eportal/app.py` in addition to module-based startup.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mock_eportal.routers import api_router, mcp_router, schema_router

# ================================================================
# APPLICATION
# ================================================================

app = FastAPI(
    title="Unisys ePortal Simulation (CardDemo Aligned)",
    description=(
        "Mock ePortal simulating Unisys MCP mainframe systems. "
        "Provides REST APIs, schema discovery, and MCP tool manifests "
        "for the Data Federation Platform. "
        "ALIGNED WITH AWS CardDemo entities: Customer, Account, Card, Transaction"
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
        "federation_standard": "AWS CardDemo",
        "status": "online",
        "entities": ["customer", "account", "card", "transaction"],
        "endpoints": {
            "data": "/api/unisys/{customer,account,card,transaction}",
            "schema": "/schema/{customer,account,card,transaction}",
            "mcp": "/mcp/tools",
            "federation-metadata": "/api/unisys/federation-metadata",
            "docs": "/docs",
        },
        "relationship_model": "1:1:1 between Customer, Account, Card; 1:* to Transaction",
        "documentation": "See /docs or /redoc for full API documentation",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "eportal-simulation",
        "platform": "Unisys MCP",
        "federation_standard": "AWS CardDemo",
        "data_loaded": True,
        "entities_available": {
            "customer": "Represents account holders",
            "account": "Represents financial accounts (1:1 with Customer)",
            "card": "Represents credit/debit cards (1:1 with Account)",
            "transaction": "Represents account transactions (1:* with Account)",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mock_eportal.app:app", host="0.0.0.0", port=8001, reload=False)
