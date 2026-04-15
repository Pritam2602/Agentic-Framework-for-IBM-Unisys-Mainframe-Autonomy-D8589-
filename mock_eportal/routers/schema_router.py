"""
schema_router.py - Schema discovery endpoints for Unisys ePortal
"""

import json
from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/schema", tags=["schema"])

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def _load_schema(entity: str) -> dict:
    """Load schema JSON for an entity"""
    schema_file = SCHEMA_DIR / f"{entity}_schema.json"
    if not schema_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Schema not found for entity: {entity}"
        )
    with open(schema_file, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/payroll")
async def get_payroll_schema():
    """Get schema definition for payroll entity"""
    return _load_schema("payroll")


@router.get("/customer")
async def get_customer_schema():
    """Get schema definition for customer entity"""
    return _load_schema("customer")


@router.get("/transaction")
async def get_transaction_schema():
    """Get schema definition for transaction entity"""
    return _load_schema("transaction")


@router.get("/all")
async def get_all_schemas():
    """Get all available schemas"""
    schemas = {}
    for entity in ["payroll", "customer", "transaction"]:
        try:
            schemas[entity] = _load_schema(entity)
        except HTTPException:
            pass
    return {
        "source": "unisys_eportal",
        "schemas": schemas,
        "count": len(schemas)
    }
