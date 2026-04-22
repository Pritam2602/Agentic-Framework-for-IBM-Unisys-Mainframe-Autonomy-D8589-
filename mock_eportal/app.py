"""Unisys ePortal shopping-data provider for the federation demo."""

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
    title="Unisys ePortal Shopping Provider",
    description=(
        "Unisys ePortal exposes generated shopping behavior derived from "
        "IBM CardDemo transaction data. It provides data only; federation "
        "and spend aggregation belong outside ePortal."
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
        "role": "data_provider",
        "status": "online",
        "entities": ["shopping"],
        "endpoints": {
            "data": "/api/unisys/shopping",
            "schema": "/schema/shopping",
            "mcp": "/mcp/tools",
            "federation-metadata": "/api/unisys/federation-metadata",
            "docs": "/docs",
        },
        "maps_to": "IBM transactions",
        "join_key": "customerId",
        "documentation": "See /docs or /redoc for full API documentation",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "eportal-simulation",
        "platform": "Unisys MCP",
        "role": "shopping-data-provider",
        "data_loaded": True,
        "entities_available": {
            "shopping": "Generated Unisys behavioral data for card shopping events",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mock_eportal.app:app", host="0.0.0.0", port=8001, reload=False)
