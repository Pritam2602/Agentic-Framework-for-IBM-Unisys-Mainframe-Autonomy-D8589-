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
from typing import Any, Optional

import os as _os

# Prevent MCP's pydantic-settings from reading the project-level .env
# (which contains unrelated API keys like OPENAI_API_KEY / GOOGLE_API_KEY).
_os.environ.setdefault("FASTMCP_ENV_FILE", "")

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

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


def _inventory_data() -> list[dict]:
    """Load all inventory records from disk."""
    data_file = DATA_DIR / "inventory.json"
    if data_file.exists():
        return _load_json(data_file)
    return []


def _write_shopping_data(records: list[dict]) -> None:
    data_file = DATA_DIR / "shopping.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with data_file.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)
        f.write("\n")


WRITABLE_SHOPPING_FIELDS = {
    "loyaltyPoints",
    "browsingSessionMinutes",
    "cartStatus",
    "merchantCategory",
}


def _capability_discovery() -> dict[str, Any]:
    shopping_schema = _load_json(SCHEMA_DIR / "shopping_schema.json")
    inventory_schema_path = SCHEMA_DIR / "inventory_schema.json"
    inventory_schema = _load_json(inventory_schema_path) if inventory_schema_path.exists() else None
    fields = shopping_schema.get("fields", [])
    related = list(shopping_schema.get("related_capability_discovery", []))
    if inventory_schema:
        related = [
            item for item in related
            if item.get("entity") != "inventory"
        ]
        related.append(
            {
                "entity": "inventory",
                "status": "available",
                "evidence_fields": [
                    "sku",
                    "merchant",
                    "category",
                    "merchantCategory",
                    "stockQuantity",
                    "availabilityStatus",
                ],
                "record_count": len(_inventory_data()),
            }
        )

    available_entities = [
        {
            "entity": "shopping",
            "fields": fields,
            "record_count": len(_shopping_data()),
            "read_supported": True,
            "write_supported": True,
            "writable_fields": shopping_schema.get("writable_fields", []),
        }
    ]
    if inventory_schema:
        available_entities.append(
            {
                "entity": "inventory",
                "fields": inventory_schema.get("fields", []),
                "record_count": len(_inventory_data()),
                "read_supported": True,
                "write_supported": False,
                "filter_fields": inventory_schema.get("filter_fields", []),
            }
        )

    return {
        "source": "unisys",
        "mode": "schema_and_dataset_discovery",
        "available_entities": available_entities,
        "related_capabilities": related,
        "discovery_notes": [
            "Reward points are available through loyaltyPoints.",
            "Inventory availability is available through inventory schema/data when present.",
        ],
    }


def _update_shopping_enrichment(
    customerId: int,
    date: str,
    merchant: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    safe_updates = {
        key: value
        for key, value in updates.items()
        if value is not None and key in WRITABLE_SHOPPING_FIELDS
    }
    if not safe_updates:
        return {
            "status": "rejected",
            "reason": "No writable enrichment fields were provided.",
            "writable_fields": sorted(WRITABLE_SHOPPING_FIELDS),
        }

    records = _shopping_data()
    for record in records:
        if (
            int(record.get("customerId")) == customerId
            and record.get("date") == date
            and str(record.get("merchant", "")).lower() == merchant.lower()
        ):
            before = dict(record)
            record.update(safe_updates)
            _write_shopping_data(records)
            return {
                "status": "updated",
                "record_key": {
                    "customerId": customerId,
                    "date": date,
                    "merchant": merchant,
                },
                "updated_fields": safe_updates,
                "before": before,
                "after": record,
                "governance_note": "Only Unisys enrichment fields were updated; IBM financial amounts remain authoritative.",
            }

    return {
        "status": "not_found",
        "record_key": {
            "customerId": customerId,
            "date": date,
            "merchant": merchant,
        },
    }


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


@mcp.tool()
def get_inventory_data(
    merchant: Optional[str] = None,
    category: Optional[str] = None,
    sku: Optional[str] = None,
    availabilityStatus: Optional[str] = None,
) -> str:
    """Retrieve Unisys inventory availability data.

    Inventory is related to shopping behavior by merchant, category, and
    merchantCategory. It is operational context, not financial authority.
    """
    records = _inventory_data()

    if merchant is not None:
        records = [
            r for r in records
            if str(r.get("merchant", "")).lower() == merchant.lower()
        ]
    if category is not None:
        records = [
            r for r in records
            if str(r.get("category", "")).lower() == category.lower()
        ]
    if sku is not None:
        records = [
            r for r in records
            if str(r.get("sku", "")).lower() == sku.lower()
        ]
    if availabilityStatus is not None:
        records = [
            r for r in records
            if str(r.get("availabilityStatus", "")).lower() == availabilityStatus.lower()
        ]

    result = {
        "source": "unisys",
        "entity": "inventory",
        "count": len(records),
        "note": "Inventory provides product availability context related to shopping merchants/categories.",
        "data": records,
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def discover_eportal_capabilities() -> str:
    """Discover what related Unisys ePortal data is currently available."""
    return json.dumps(_capability_discovery(), indent=2)


@mcp.tool()
def update_shopping_enrichment(
    customerId: int,
    date: str,
    merchant: str,
    loyaltyPoints: Optional[int] = None,
    browsingSessionMinutes: Optional[int] = None,
    cartStatus: Optional[str] = None,
    merchantCategory: Optional[str] = None,
) -> str:
    """Update writable Unisys shopping enrichment fields for a single event.

    This intentionally does not update amount. IBM CardDemo remains the
    financial authority; Unisys updates are limited to behavioral enrichment.
    """
    return json.dumps(
        _update_shopping_enrichment(
            customerId=customerId,
            date=date,
            merchant=merchant,
            updates={
                "loyaltyPoints": loyaltyPoints,
                "browsingSessionMinutes": browsingSessionMinutes,
                "cartStatus": cartStatus,
                "merchantCategory": merchantCategory,
            },
        ),
        indent=2,
    )




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


@mcp.resource("schema://inventory")
def inventory_schema() -> str:
    """Inventory entity schema - product availability and stock context."""
    schema_file = SCHEMA_DIR / "inventory_schema.json"
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
            "inventory": "Product availability and stock context related to shopping behavior",
        },
    })


@mcp.resource("eportal://capability-discovery")
def capability_discovery() -> str:
    """Discover available and missing related ePortal capabilities."""
    return json.dumps(_capability_discovery(), indent=2)


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


class ShoppingCreateRequest(BaseModel):
    customerId: int
    merchant: str
    amount: float
    date: str
    category: str
    loyaltyPoints: int = 0
    browsingSessionMinutes: int = 0
    cartStatus: str = "completed"
    merchantCategory: str = "unknown"


class ShoppingUpdateRequest(BaseModel):
    customerId: int
    date: str
    merchant: str
    updates: dict[str, Any] = Field(
        description="Writable fields only: loyaltyPoints, browsingSessionMinutes, cartStatus, merchantCategory"
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


@api.get("/api/inventory", tags=["Inventory Data"])
async def api_get_inventory_data(
    merchant: Optional[str] = Query(None, description="Filter by merchant"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    availabilityStatus: Optional[str] = Query(None, description="Filter by availability status"),
):
    """Retrieve Unisys inventory availability data."""
    return json.loads(
        get_inventory_data(
            merchant=merchant,
            category=category,
            sku=sku,
            availabilityStatus=availabilityStatus,
        )
    )


@api.get("/api/schema/shopping", tags=["Schema & Metadata"])
async def api_shopping_schema():
    """Return the shopping entity schema."""
    return json.loads(shopping_schema())


@api.get("/api/schema/inventory", tags=["Schema & Metadata"])
async def api_inventory_schema():
    """Return the inventory entity schema."""
    return json.loads(inventory_schema())


@api.get("/api/entity-mapping", tags=["Schema & Metadata"])
async def api_entity_mapping():
    """Return the entity mapping between Unisys and IBM systems."""
    return json.loads(entity_mapping())


@api.get("/api/capabilities", tags=["Schema & Metadata"])
async def api_capabilities():
    """Return grounded capability discovery for ePortal data."""
    return _capability_discovery()


@api.post("/api/shopping", tags=["Shopping Data"])
async def api_create_shopping_event(request: ShoppingCreateRequest):
    """Create a Unisys shopping enrichment event.

    This is a feasible write path for use case demos. It stores Unisys
    enrichment/context data only; IBM remains the financial source of truth.
    """
    record = request.model_dump()
    records = _shopping_data()
    records.append(record)
    _write_shopping_data(records)
    return {
        "status": "created",
        "record": record,
        "governance_note": "Created Unisys enrichment record; IBM financial amounts remain authoritative.",
    }


@api.patch("/api/shopping/enrichment", tags=["Shopping Data"])
async def api_update_shopping_enrichment(request: ShoppingUpdateRequest):
    """Update writable enrichment fields on an existing shopping event."""
    unsafe_fields = sorted(set(request.updates) - WRITABLE_SHOPPING_FIELDS)
    updates = {
        key: value
        for key, value in request.updates.items()
        if key in WRITABLE_SHOPPING_FIELDS
    }
    if not updates:
        return {
            "status": "rejected",
            "reason": "No writable enrichment fields were provided.",
            "rejected_fields": unsafe_fields,
            "writable_fields": sorted(WRITABLE_SHOPPING_FIELDS),
        }

    result = _update_shopping_enrichment(
        customerId=request.customerId,
        date=request.date,
        merchant=request.merchant,
        updates=updates,
    )
    if unsafe_fields:
        result["rejected_fields"] = unsafe_fields
    return result


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    import uvicorn

    # Mount MCP SSE app under /sse for LLM agents
    sse_app = mcp.sse_app()
    api.mount("/", sse_app)

    uvicorn.run(api, host="0.0.0.0", port=8001)
