"""Federation Intelligence Agent — identifies entity relationships and recommends federated views."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from .entity_graph import build_entity_graph, resolve_join_key
from .executor import execute_view
from .schemas import (
    EntityRelationship,
    FederationIntelligenceOutput,
    FederationPlan,
    FederatedView,
    LineageRecord,
)
from .view_recommender import recommend_views


_IBM_LINEAGE_TEMPLATE: List[Dict[str, str]] = [
    {"field": "transactionId", "source_system": "ibm", "source_entity": "transaction", "transformation": None},
    {"field": "customerId", "source_system": "ibm", "source_entity": "transaction", "transformation": "join key — also present in Unisys"},
    {"field": "amount", "source_system": "ibm", "source_entity": "transaction", "transformation": "financial authority — do NOT add Unisys amount"},
    {"field": "date", "source_system": "ibm", "source_entity": "transaction", "transformation": "maps to Unisys 'date' field"},
    {"field": "transactionType", "source_system": "ibm", "source_entity": "transaction", "transformation": None},
]

_UNISYS_LINEAGE_TEMPLATE: List[Dict[str, str]] = [
    {"field": "merchant", "source_system": "unisys", "source_entity": "shopping", "transformation": "behavioral enrichment"},
    {"field": "category", "source_system": "unisys", "source_entity": "shopping", "transformation": "behavioral enrichment"},
    {"field": "merchantCategory", "source_system": "unisys", "source_entity": "shopping", "transformation": "behavioral enrichment"},
    {"field": "loyaltyPoints", "source_system": "unisys", "source_entity": "shopping", "transformation": "behavioral enrichment"},
    {"field": "browsingSessionMinutes", "source_system": "unisys", "source_entity": "shopping", "transformation": "behavioral enrichment"},
    {"field": "cartStatus", "source_system": "unisys", "source_entity": "shopping", "transformation": "behavioral enrichment"},
]


def _extract_customer_id(intent: Dict[str, Any]) -> Optional[int]:
    filters = intent.get("filters", {})
    conditions = filters.get("conditions", [])
    for cond in conditions:
        if cond.get("field") in ("customerId", "customer_id"):
            try:
                return int(cond["value"])
            except (TypeError, ValueError):
                pass
    return None


def _extract_date(intent: Dict[str, Any]) -> Optional[str]:
    filters = intent.get("filters", {})
    for cond in filters.get("conditions", []):
        if cond.get("field") == "date":
            return str(cond["value"])
    time_range = filters.get("time_range")
    if time_range:
        return time_range.get("start")
    return None


def _build_lineage(top_view: Optional[FederatedView]) -> List[LineageRecord]:
    lineage: List[LineageRecord] = []
    for item in _IBM_LINEAGE_TEMPLATE:
        lineage.append(LineageRecord(**item))
    for item in _UNISYS_LINEAGE_TEMPLATE:
        lineage.append(LineageRecord(**item))
    return lineage


def _build_federation_plan(
    relationships: List[EntityRelationship],
    top_view: Optional[FederatedView],
) -> FederationPlan:
    join_key = resolve_join_key(relationships) or "customerId"
    enrichment_fields = (
        top_view.unisys_fields
        if top_view
        else ["merchant", "category", "loyaltyPoints", "browsingSessionMinutes", "cartStatus"]
    )

    steps = [
        "1. Resolve IBM intent entities -> fetch transaction records via IBM CardDemo dataset",
        "2. Resolve Unisys intent entities -> query ePortal shopping API via MCP",
        f"3. Join IBM transactions + Unisys shopping on '{join_key}' (left join - keep all IBM records)",
        "4. Assert financial authority: use IBM 'amount' as total_spend - NEVER sum Unisys amounts",
        f"5. Attach Unisys enrichment fields: {', '.join(enrichment_fields[:4])} ...",
        "6. Compute federation metrics (category analysis, loyalty summary, cart analysis, browsing)",
        "7. Record lineage for every output field",
        "8. Apply governance controls and emit audit record",
    ]

    return FederationPlan(
        primary_source="ibm",
        enrichment_source="unisys",
        join_strategy="left",
        join_key=join_key,
        financial_authority=(
            "IBM CardDemo is the authoritative source for all financial amounts. "
            "Unisys ePortal shopping amounts mirror IBM and must NOT be summed with IBM figures."
        ),
        enrichment_fields=enrichment_fields,
        execution_steps=steps,
        double_counting_guard=(
            "Unisys 'amount' == IBM 'transactionAmount'. "
            "total_spend = SUM(IBM amounts) only. Unisys contributes zero dollars to the total."
        ),
    )


def _compute_confidence(
    relationships: List[EntityRelationship],
    context: Dict[str, Any],
    top_view: Optional[FederatedView],
) -> float:
    scores = [r.confidence for r in relationships]
    rel_score = sum(scores) / len(scores) if scores else 0.5

    ctx_score = float(context.get("resolution_confidence", 0.7))
    view_score = top_view.applicability_score if top_view else 0.5

    return round((rel_score * 0.4) + (ctx_score * 0.35) + (view_score * 0.25), 3)


def _build_reasoning(
    relationships: List[EntityRelationship],
    top_view: Optional[FederatedView],
    intent: Dict[str, Any],
    executed: bool,
) -> str:
    task = intent.get("task", "fetch")
    entities = intent.get("entities", [])
    metric = intent.get("metric", "")

    rel_summary = "; ".join(
        f"{r.source_system}.{r.source_entity} → {r.target_system}.{r.target_entity} "
        f"via {r.join_key} ({r.relationship_type})"
        for r in relationships[:2]
    )

    view_name = top_view.name if top_view else "no single best view"

    exec_note = (
        "Federation was executed and results are included in this response."
        if executed
        else "Federation was not executed (no customerId filter found or execute=False)."
    )

    return (
        f"Intent: {task} on entities {entities}"
        f"{f' for metric {metric}' if metric else ''}. "
        f"Entity relationships discovered: {rel_summary or 'none'}. "
        f"Top recommended view: '{view_name}'. "
        f"IBM CardDemo is the financial authority; Unisys ePortal adds behavioral enrichment only. "
        f"{exec_note}"
    )


def run(
    intent: Dict[str, Any],
    context: Dict[str, Any],
    execute: bool = True,
) -> FederationIntelligenceOutput:
    """Entry point for the Federation Intelligence Agent."""

    intent_entities: List[str] = intent.get("entities", [])
    requires_federation: bool = intent.get("requires_federation", False)

    if not intent_entities and not requires_federation:
        intent_entities = ["transaction", "shopping"]

    relationships = build_entity_graph(intent_entities)

    views = recommend_views(relationships, intent, top_n=5)
    top_view = views[0] if views else None

    federation_plan = _build_federation_plan(relationships, top_view)
    lineage = _build_lineage(top_view)

    federated_result: Optional[Dict[str, Any]] = None
    executed = False

    if execute:
        customer_id = _extract_customer_id(intent)
        if customer_id is not None:
            date = _extract_date(intent)
            view_id = top_view.view_id if top_view else "customer_spend_enriched"
            federated_result = execute_view(view_id, customer_id, date)
            executed = True

    confidence = _compute_confidence(relationships, context, top_view)
    reasoning = _build_reasoning(relationships, top_view, intent, executed)

    governance = {
        "audit_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "sources_accessed": ["IBM CardDemo", "Unisys ePortal"],
        "join_key": federation_plan.join_key,
        "financial_authority": "IBM CardDemo",
        "enrichment_authority": "Unisys ePortal",
        "double_counting_protected": True,
        "federation_executed": executed,
        "overall_confidence": confidence,
        "entity_relationships_count": len(relationships),
        "views_evaluated": len(views),
    }

    return FederationIntelligenceOutput(
        entity_relationships=relationships,
        recommended_views=views,
        top_view=top_view,
        federation_plan=federation_plan,
        federated_result=federated_result,
        lineage=lineage,
        governance=governance,
        overall_confidence=confidence,
        reasoning=reasoning,
    )
