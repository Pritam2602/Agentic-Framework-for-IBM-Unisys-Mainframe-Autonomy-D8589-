"""
Unisys ePortal MCP Server — Model Context Protocol interface.

Exposes Unisys shopping behavior data as MCP tools and resources
so that LLM agents can discover and query them via the standard
MCP protocol over SSE transport.

IMPORTANT CONTEXT FOR LLM AGENTS:
    IBM CardDemo transactions ALREADY include all financial amounts,
    including shopping.  The Unisys ePortal provides *behavioral
    enrichment* (merchant, category, loyalty, browsing patterns)
    on top of the same transactions.  Do NOT sum IBM + Unisys amounts
    to get "total spend" — IBM's amount IS the total.  Use Unisys data
    for context, not for additional dollar values.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import os as _os

# Prevent MCP's pydantic-settings from reading the project-level .env
# (which contains unrelated API keys like OPENAI_API_KEY / GOOGLE_API_KEY).
_os.environ.setdefault("FASTMCP_ENV_FILE", "")

from mcp.server.fastmcp import FastMCP

# ================================================================
# DATA PATHS
# ================================================================

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "unisys"
SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
ENTITY_MAPPING = Path(__file__).resolve().parent / "entity_mapping.json"

# ================================================================
# MCP SERVER
# ================================================================

mcp = FastMCP(
    "Unisys-ePortal",
    instructions=(
        "Unisys ePortal provides shopping **behavioral enrichment** data "
        "for credit-card customers. IBM CardDemo already holds all financial "
        "transaction amounts (including shopping). The amounts in this system "
        "mirror IBM amounts — do NOT double-count them. Use this data for "
        "merchant info, category breakdown, loyalty points, browsing behavior, "
        "and cart status — NOT for additional spend totals."
    ),
    host="0.0.0.0",
    port=8001,
)


# ================================================================
# HELPERS
# ================================================================

def _load_json(path: Path) -> list | dict:
    """Load JSON while tolerating UTF-8 BOM-encoded files."""
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def _shopping_data() -> list[dict]:
    """Load all shopping records from disk."""
    data_file = DATA_DIR / "shopping.json"
    if data_file.exists():
        return _load_json(data_file)
    return []


# ================================================================
# TOOLS  (callable actions for the LLM)
# ================================================================

@mcp.tool()
def get_shopping_data(
    customerId: Optional[int] = None,
    date: Optional[str] = None,
) -> str:
    """Retrieve Unisys shopping behavior data.

    NOTE: The 'amount' field here mirrors the IBM CardDemo transaction
    amount.  IBM transactions ALREADY include all spending (including
    shopping).  Do NOT add Unisys amounts on top of IBM amounts to
    compute total spend — that would double-count.

    Use this data for behavioral enrichment: merchant names, categories,
    loyalty points, browsing duration, and cart status.

    Args:
        customerId: Filter by customer ID (optional).
        date: Filter by shopping date in YYYY-MM-DD format (optional).

    Returns:
        JSON string of matching shopping records with source metadata.
    """
    records = _shopping_data()

    if customerId is not None:
        records = [r for r in records if int(r["customerId"]) == customerId]
    if date is not None:
        records = [r for r in records if r["date"] == date]

    result = {
        "source": "unisys",
        "entity": "shopping",
        "count": len(records),
        "note": (
            "Amounts mirror IBM CardDemo transactions. "
            "Do NOT sum with IBM amounts — IBM already includes shopping spend."
        ),
        "data": records,
    }
    return json.dumps(result, indent=2)




# ================================================================
# RESOURCES  (read-only data for the LLM)
# ================================================================

@mcp.resource("schema://shopping")
def shopping_schema() -> str:
    """Shopping entity schema — field definitions, join keys, and mapping info."""
    schema_file = SCHEMA_DIR / "shopping_schema.json"
    if schema_file.exists():
        return json.dumps(_load_json(schema_file), indent=2)
    return json.dumps({"error": "Schema not found"})


@mcp.resource("eportal://entity-mapping")
def entity_mapping() -> str:
    """Entity mapping — how Unisys entities relate to IBM entities."""
    if ENTITY_MAPPING.exists():
        return json.dumps(_load_json(ENTITY_MAPPING), indent=2)
    return json.dumps({"error": "Entity mapping not found"})


@mcp.resource("eportal://health")
def health_check() -> str:
    """Health status of the Unisys ePortal MCP server."""
    return json.dumps({
        "status": "healthy",
        "service": "eportal-mcp-server",
        "platform": "Unisys MCP",
        "protocol": "Model Context Protocol (SSE)",
        "role": "shopping-data-provider",
        "data_loaded": len(_shopping_data()) > 0,
        "entities_available": {
            "shopping": "Behavioral enrichment data for card shopping events",
        },
    })


# ================================================================
# FASTAPI REST LAYER  (Swagger docs for humans)
# ================================================================

from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse

api = FastAPI(
    title="Unisys ePortal",
    version="2.0.0",
    description=(
        "**Unisys ePortal** — shopping behavioral enrichment data.\n\n"
        "This server exposes the same data in **two ways**:\n\n"
        "| Channel | URL | For |\n"
        "|---|---|---|\n"
        "| **REST + Swagger** | `/docs` | Humans — browse & test endpoints |\n"
        "| **MCP over SSE** | `/sse` | LLM Agents — tool discovery & invocation |\n\n"
        "**Note:** IBM CardDemo transactions already include all financial "
        "amounts. Unisys provides *behavioral enrichment* only (merchant, "
        "category, loyalty, browsing). Do NOT double-count."
    ),
)


@api.get("/", include_in_schema=False)
async def root():
    """Redirect browser visitors to Swagger docs."""
    return RedirectResponse(url="/docs")


@api.get("/health", tags=["System"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "eportal-mcp-server",
        "platform": "Unisys MCP",
    }


@api.get("/api/shopping", tags=["Shopping Data"])
async def api_get_shopping_data(
    customerId: Optional[int] = Query(None, description="Filter by customer ID"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
):
    """Retrieve Unisys shopping behavior data (REST mirror of MCP tool).

    The 'amount' field mirrors the IBM CardDemo transaction amount.
    IBM transactions ALREADY include all spending — do NOT double-count.

    Use this data for: merchant names, categories, loyalty points,
    browsing duration, and cart status.
    """
    return json.loads(get_shopping_data(customerId=customerId, date=date))


@api.get("/api/schema/shopping", tags=["Schema & Metadata"])
async def api_shopping_schema():
    """Return the shopping entity schema."""
    return json.loads(shopping_schema())


@api.get("/api/entity-mapping", tags=["Schema & Metadata"])
async def api_entity_mapping():
    """Return the entity mapping between Unisys and IBM systems."""
    return json.loads(entity_mapping())


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    import uvicorn

    # Mount MCP SSE app under /sse for LLM agents
    sse_app = mcp.sse_app()
    api.mount("/", sse_app)

    uvicorn.run(api, host="0.0.0.0", port=8001)

