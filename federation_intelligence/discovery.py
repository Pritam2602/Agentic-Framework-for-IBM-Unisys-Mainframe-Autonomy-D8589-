"""Capability discovery for IBM + Unisys federation data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
UNISYS_SCHEMA_DIR = ROOT / "mock_eportal" / "schema"
UNISYS_DATA_DIR = ROOT / "data" / "unisys"


RELATED_CAPABILITY_HINTS: Dict[str, List[Dict[str, Any]]] = {
    "shopping": [
        {
            "entity": "loyalty",
            "status": "available",
            "reason": "Shopping records include loyaltyPoints.",
            "evidence_fields": ["loyaltyPoints"],
        },
        {
            "entity": "cart",
            "status": "available",
            "reason": "Shopping records include cartStatus.",
            "evidence_fields": ["cartStatus"],
        },
        {
            "entity": "browsing",
            "status": "available",
            "reason": "Shopping records include browsingSessionMinutes.",
            "evidence_fields": ["browsingSessionMinutes"],
        },
        {
            "entity": "merchant_category",
            "status": "available",
            "reason": "Shopping records include merchantCategory and category.",
            "evidence_fields": ["merchantCategory", "category"],
        },
        {
            "entity": "inventory",
            "status": "not_found",
            "reason": (
                "No inventory schema, dataset, stock quantity, SKU, or product availability "
                "fields are present in the current Unisys mock ePortal data."
            ),
            "evidence_fields": [],
        },
    ]
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def _available_unisys_entities() -> List[Dict[str, Any]]:
    entities: List[Dict[str, Any]] = []
    for schema_path in sorted(UNISYS_SCHEMA_DIR.glob("*_schema.json")):
        schema = _load_json(schema_path)
        entity = str(schema.get("entity") or schema_path.stem.replace("_schema", ""))
        fields = schema.get("fields") or []
        data_file = UNISYS_DATA_DIR / f"{entity}.json"
        records = _load_json(data_file) if data_file.exists() else []
        entities.append(
            {
                "system": "unisys",
                "entity": entity,
                "schema": str(schema_path.relative_to(ROOT)),
                "dataset": str(data_file.relative_to(ROOT)) if data_file.exists() else None,
                "fields": fields,
                "record_count": len(records) if isinstance(records, list) else 0,
                "join_key": schema.get("join_key"),
                "maps_to": schema.get("maps_to"),
                "read_supported": True,
                "write_supported": entity == "shopping",
                "writable_fields": schema.get("writable_fields", []),
            }
        )
    return entities


def _intent_terms(intent: Dict[str, Any]) -> set[str]:
    terms = set()
    for key in ("entities", "attributes"):
        value = intent.get(key) or []
        if isinstance(value, list):
            terms.update(str(item).lower() for item in value)
    for key in ("metric", "task", "aggregation"):
        value = intent.get(key)
        if value:
            terms.add(str(value).lower())
    for value in list(terms):
        terms.update(token for token in re.split(r"[^a-z0-9_]+", value) if token)
    return terms


def discover_capabilities(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Return grounded capability discovery from local schemas and datasets."""
    entities = _available_unisys_entities()
    entity_names = {entity["entity"] for entity in entities}
    terms = _intent_terms(intent)

    related: List[Dict[str, Any]] = []
    if "shopping" in entity_names or "shopping" in terms:
        related.extend(RELATED_CAPABILITY_HINTS["shopping"])

    requested_missing = []
    for term in terms:
        if term in {"inventory", "stock", "sku", "product_availability"}:
            requested_missing.append(
                {
                    "entity": "inventory",
                    "status": "not_found",
                    "reason": "Inventory was explicitly requested but no current schema/dataset exposes it.",
                }
            )

    available_field_index = {
        entity["entity"]: entity["fields"]
        for entity in entities
    }

    return {
        "mode": "schema_and_dataset_discovery",
        "available_entities": entities,
        "available_field_index": available_field_index,
        "related_capabilities": related,
        "requested_missing_capabilities": requested_missing,
        "discovery_notes": [
            "Discovery is grounded in current ePortal schemas and local datasets.",
            "Reward/loyalty questions are supported because loyaltyPoints exists in shopping records.",
            "Inventory cannot be inferred as available until a schema, endpoint, or dataset is added.",
        ],
    }
