"""Entity relationship graph — discovers cross-system entity links from the mapping catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schemas import EntityRelationship

ROOT = Path(__file__).resolve().parents[1]
ENTITY_MAPPING_PATH = ROOT / "mock_eportal" / "entity_mapping.json"

SYSTEM_OWNERSHIP: Dict[str, str] = {
    "transaction": "ibm",
    "account": "ibm",
    "customer": "ibm",
    "shopping": "unisys",
    "merchant": "unisys",
    "loyalty": "unisys",
}

RELATIONSHIP_CATALOG: List[Dict[str, Any]] = [
    {
        "source_entity": "transaction",
        "target_entity": "shopping",
        "source_system": "ibm",
        "target_system": "unisys",
        "join_key": "customerId",
        "relationship_type": "enrichment",
        "confidence": 0.95,
        "reasoning": (
            "IBM CardDemo transactions carry all financial amounts. Unisys shopping "
            "records mirror those amounts and add behavioral context (merchant, category, "
            "loyalty, browsing, cart status). They join on customerId."
        ),
    },
    {
        "source_entity": "account",
        "target_entity": "shopping",
        "source_system": "ibm",
        "target_system": "unisys",
        "join_key": "customerId",
        "relationship_type": "reference",
        "confidence": 0.80,
        "reasoning": (
            "IBM account records reference a customerId that can be used to look up "
            "Unisys shopping behavioral data for the same customer."
        ),
    },
    {
        "source_entity": "customer",
        "target_entity": "shopping",
        "source_system": "ibm",
        "target_system": "unisys",
        "join_key": "customerId",
        "relationship_type": "enrichment",
        "confidence": 0.90,
        "reasoning": (
            "Customer records in IBM can be enriched with Unisys shopping behavior "
            "to build a 360° customer profile."
        ),
    },
]


def _load_entity_mapping() -> Dict[str, Any]:
    try:
        with ENTITY_MAPPING_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def build_entity_graph(intent_entities: List[str]) -> List[EntityRelationship]:
    """Return all cross-system relationships relevant to the given intent entities."""
    mapping = _load_entity_mapping()
    relevant: List[EntityRelationship] = []
    seen: set[str] = set()

    for rel in RELATIONSHIP_CATALOG:
        src = rel["source_entity"]
        tgt = rel["target_entity"]
        key = f"{src}:{tgt}"

        if src in intent_entities or tgt in intent_entities:
            if key not in seen:
                seen.add(key)

                enriched_reasoning = rel["reasoning"]
                for ent in mapping.get("entities", []):
                    if ent.get("unisys_name") == tgt or ent.get("entity_name", "").lower() == tgt:
                        enriched_reasoning += (
                            f" Field mapping note: {ent.get('spend_note', '')}"
                        )
                        break

                relevant.append(EntityRelationship(**{**rel, "reasoning": enriched_reasoning}))

    if not relevant:
        inferred = _infer_relationships(intent_entities)
        relevant.extend(inferred)

    return relevant


def _infer_relationships(intent_entities: List[str]) -> List[EntityRelationship]:
    """Fallback: infer plausible relationships even for unknown entity combinations."""
    ibm_entities = [e for e in intent_entities if SYSTEM_OWNERSHIP.get(e) == "ibm"]
    unisys_entities = [e for e in intent_entities if SYSTEM_OWNERSHIP.get(e) == "unisys"]

    if ibm_entities and unisys_entities:
        return [
            EntityRelationship(
                source_entity=ibm_entities[0],
                target_entity=unisys_entities[0],
                source_system="ibm",
                target_system="unisys",
                join_key="customerId",
                relationship_type="enrichment",
                confidence=0.65,
                reasoning=(
                    f"Inferred: IBM entity '{ibm_entities[0]}' and Unisys entity "
                    f"'{unisys_entities[0]}' likely share customerId as a common join key."
                ),
            )
        ]
    return []


def resolve_join_key(relationships: List[EntityRelationship]) -> Optional[str]:
    """Return the most common join key across all relationships."""
    if not relationships:
        return None
    counts: Dict[str, int] = {}
    for rel in relationships:
        counts[rel.join_key] = counts.get(rel.join_key, 0) + 1
    return max(counts, key=counts.get)
