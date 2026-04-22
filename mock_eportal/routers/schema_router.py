"""Schema discovery endpoint for Unisys ePortal shopping data."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from mock_eportal.utils import load_json_file

router = APIRouter(prefix="/schema", tags=["schema"])

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"


def _load_schema(entity: str) -> dict:
    schema_file = SCHEMA_DIR / f"{entity}_schema.json"
    if not schema_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Schema not found for entity: {entity}",
        )
    return load_json_file(schema_file)


@router.get("/shopping")
async def get_shopping_schema():
    return _load_schema("shopping")


@router.get("/all")
async def get_all_schemas():
    shopping_schema = _load_schema("shopping")
    return {
        "source": "unisys",
        "schemas": {
            "shopping": shopping_schema,
        },
        "count": 1,
    }
