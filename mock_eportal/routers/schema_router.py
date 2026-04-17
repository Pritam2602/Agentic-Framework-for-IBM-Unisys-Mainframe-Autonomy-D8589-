"""
schema_router.py - Schema discovery endpoints for Unisys ePortal
Aligned with AWS CardDemo entity schemas
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from mock_eportal.utils import load_json_file

router = APIRouter(prefix="/schema", tags=["schema"])

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def _load_schema(entity: str) -> dict:
    """Load schema JSON for an entity."""
    schema_file = SCHEMA_DIR / f"{entity}_schema.json"
    if not schema_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Schema not found for entity: {entity}",
        )
    return load_json_file(schema_file)


@router.get("/customer")
async def get_customer_schema():
    """Get schema definition for customer entity (CardDemo Customer)."""
    return _load_schema("customer")


@router.get("/account")
async def get_account_schema():
    """Get schema definition for account entity (CardDemo Account)."""
    return _load_schema("account")


@router.get("/card")
async def get_card_schema():
    """Get schema definition for card entity (CardDemo Card)."""
    return _load_schema("card")


@router.get("/transaction")
async def get_transaction_schema():
    """Get schema definition for transaction entity (CardDemo Transaction)."""
    return _load_schema("transaction")


@router.get("/all")
async def get_all_schemas():
    """Get all available schemas (CardDemo entities)."""
    schemas = {}
    for entity in ["customer", "account", "card", "transaction"]:
        try:
            schemas[entity] = _load_schema(entity)
        except HTTPException:
            pass
    return {
        "source": "unisys_eportal",
        "federation_standard": "AWS CardDemo",
        "schemas": schemas,
        "count": len(schemas),
        "relationship_model": "1:1:1 between Customer, Account, and Card; 1:* to Transaction",
    }


@router.get("/entity-relationships")
async def get_entity_relationships():
    """Get CardDemo entity relationship model."""
    return {
        "standard": "AWS CardDemo",
        "constraint": "1:1:1 Relationship",
        "entities": {
            "Customer": {
                "description": "Account holder / customer",
                "related_to": ["Account"],
                "multiplicity": "1:1",
            },
            "Account": {
                "description": "Financial account",
                "related_to": ["Customer", "Card", "Transaction"],
                "multiplicity": "1:1 to Customer, 1:1 to Card, 1:* to Transaction",
            },
            "Card": {
                "description": "Credit/Debit card",
                "related_to": ["Customer", "Account"],
                "multiplicity": "1:1 to both",
            },
            "Transaction": {
                "description": "Financial transaction",
                "related_to": ["Account"],
                "multiplicity": "Many:1 to Account",
            },
        },
    }
