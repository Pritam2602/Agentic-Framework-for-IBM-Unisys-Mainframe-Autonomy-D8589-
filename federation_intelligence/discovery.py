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
            "discovery_type": "related_capability",
            "confidence": 0.86,
            "source": "shopping.loyaltyPoints",
            "relationship": "shopping -> loyalty",
            "reason": "Shopping records include loyaltyPoints.",
            "evidence_fields": ["loyaltyPoints"],
        },
        {
            "entity": "cart",
            "status": "available",
            "discovery_type": "related_capability",
            "confidence": 0.84,
            "source": "shopping.cartStatus",
            "relationship": "shopping -> cart",
            "reason": "Shopping records include cartStatus.",
            "evidence_fields": ["cartStatus"],
        },
        {
            "entity": "browsing",
            "status": "available",
            "discovery_type": "related_capability",
            "confidence": 0.82,
            "source": "shopping.browsingSessionMinutes",
            "relationship": "shopping -> browsing",
            "reason": "Shopping records include browsingSessionMinutes.",
            "evidence_fields": ["browsingSessionMinutes"],
        },
        {
            "entity": "merchant_category",
            "status": "available",
            "discovery_type": "exact_match",
            "confidence": 0.94,
            "source": "shopping.merchant + shopping.category + shopping.merchantCategory",
            "relationship": "shopping -> merchant -> category",
            "reason": "Shopping records include merchantCategory and category.",
            "evidence_fields": ["merchantCategory", "category"],
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
    entity_by_name = {entity["entity"]: entity for entity in entities}
    terms = _intent_terms(intent)

    related: List[Dict[str, Any]] = []
    if "shopping" in entity_names or "shopping" in terms:
        related.extend(RELATED_CAPABILITY_HINTS["shopping"])
        inventory_entity = entity_by_name.get("inventory")
        if inventory_entity:
            inventory_fields = set(inventory_entity.get("fields", []))
            has_inventory_specific_fields = bool(
                inventory_fields & {"sku", "stockQuantity", "availabilityStatus", "warehouseLocation"}
            )
            related.append(
                {
                    "entity": "inventory",
                    "status": "available",
                    "discovery_type": "exact_match" if has_inventory_specific_fields else "inferred",
                    "confidence": 0.92 if has_inventory_specific_fields else 0.52,
                    "source": (
                        "inventory schema + inventory dataset"
                        if has_inventory_specific_fields
                        else "shopping merchant/category metadata"
                    ),
                    "relationship": "shopping -> merchantCategory -> inventory",
                    "reason": (
                        "Inventory schema and dataset expose SKU, stock quantity, availability status, "
                        "warehouse location, merchant, and category fields."
                        if has_inventory_specific_fields
                        else "Potential inventory capability inferred from merchant-category relationships."
                    ),
                    "evidence_fields": [
                        "sku",
                        "merchant",
                        "category",
                        "merchantCategory",
                        "stockQuantity",
                        "availabilityStatus",
                    ],
                    "record_count": inventory_entity.get("record_count", 0),
                }
            )
        else:
            related.append(
                {
                    "entity": "inventory",
                    "status": "not_found",
                    "discovery_type": "inferred",
                    "confidence": 0.52,
                    "source": "shopping merchant/category metadata",
                    "relationship": "shopping -> merchant -> possible inventory",
                    "reason": (
                        "Potential inventory-related capability inferred from merchant-category "
                        "relationships, but no inventory schema or dataset is currently available."
                    ),
                    "evidence_fields": [],
                }
            )

    requested_missing = []
    for term in terms:
        if term in {"inventory", "inventory_data", "stock", "stock_data", "sku", "product_availability"}:
            if "inventory" in entity_names:
                continue
            requested_missing.append(
                {
                    "entity": "inventory",
                    "status": "not_found",
                    "discovery_type": "weak_signal",
                    "confidence": 0.35,
                    "source": "user-requested attribute",
                    "relationship": "requested inventory -> no dataset",
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
            "Discovery confidence distinguishes exact datasets from inferred or weak metadata signals.",
        ],
        "discovery_graph": [
            {"from": "shopping", "to": "merchant", "relationship": "contains merchant behavior"},
            {"from": "merchant", "to": "merchant_category", "relationship": "classified by merchantCategory"},
            {"from": "merchant_category", "to": "inventory", "relationship": "maps to stock and availability context"},
            {"from": "shopping", "to": "loyalty", "relationship": "contains loyaltyPoints"},
            {"from": "shopping", "to": "cart", "relationship": "contains cartStatus"},
        ],
        "capability_recommendations": [
            {
                "capability": "merchant_analytics",
                "discovery_type": "exact_match",
                "confidence": 0.94,
                "reason": "Merchant, category, and observed shopping behavior are available.",
            },
            {
                "capability": "reward_optimization",
                "discovery_type": "related_capability",
                "confidence": 0.86,
                "reason": "Shopping data includes loyaltyPoints and can be correlated with IBM spend.",
            },
            {
                "capability": "inventory_availability",
                "discovery_type": "exact_match" if "inventory" in entity_names else "inferred",
                "confidence": 0.92 if "inventory" in entity_names else 0.52,
                "reason": (
                    "Inventory schema/data are onboarded."
                    if "inventory" in entity_names
                    else "Merchant-category metadata suggests a possible inventory relationship."
                ),
            },
        ],
    }
