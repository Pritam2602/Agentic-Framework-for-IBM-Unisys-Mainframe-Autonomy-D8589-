"""Federated business view catalog and recommendation engine."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .schemas import EntityRelationship, FederatedView


def _term_tokens(values: set[str]) -> set[str]:
    tokens = set(values)
    for value in values:
        tokens.update(token for token in re.split(r"[^a-z0-9_]+", value) if token)
    return tokens

VIEW_CATALOG: List[Dict[str, Any]] = [
    {
        "view_id": "customer_spend_enriched",
        "name": "Customer Spend with Behavioral Context",
        "description": (
            "Combines IBM transaction amounts (financial truth) with Unisys merchant, "
            "category, loyalty, browsing, and cart data to give a 360° spending view per customer."
        ),
        "entities_involved": ["transaction", "shopping"],
        "systems_involved": ["ibm", "unisys"],
        "join_key": "customerId",
        "ibm_fields": ["transactionId", "customerId", "amount", "date", "transactionType"],
        "unisys_fields": [
            "merchant", "category", "loyaltyPoints",
            "browsingSessionMinutes", "cartStatus", "merchantCategory",
        ],
        "business_value": (
            "Enables product managers and analysts to understand not just HOW MUCH a "
            "customer spends but WHERE and HOW — unlocking loyalty segmentation, "
            "cart abandonment insights, and category-level marketing."
        ),
        "trigger_entities": {"transaction", "shopping"},
        "trigger_metrics": {"total_spend", "average_spend", "transaction_count"},
        "trigger_tasks": {"fetch", "analyze", "compare"},
    },
    {
        "view_id": "merchant_category_spend",
        "name": "Spend by Merchant and Category",
        "description": (
            "Aggregates IBM spend amounts grouped by Unisys merchant and category — "
            "showing where customers spend money by business type."
        ),
        "entities_involved": ["transaction", "shopping"],
        "systems_involved": ["ibm", "unisys"],
        "join_key": "customerId",
        "ibm_fields": ["customerId", "amount", "date"],
        "unisys_fields": ["merchant", "category", "merchantCategory"],
        "business_value": (
            "Reveals top merchants and spending categories per customer, enabling "
            "targeted offers, co-brand partnerships, and product cross-sell."
        ),
        "trigger_entities": {"shopping", "transaction"},
        "trigger_metrics": {"total_spend", "average_spend"},
        "trigger_tasks": {"analyze", "compare"},
    },
    {
        "view_id": "loyalty_spend_correlation",
        "name": "Loyalty Points vs Spend Correlation",
        "description": (
            "Correlates IBM spend amounts with Unisys loyalty points to reveal how "
            "much loyalty value customers accumulate relative to their spend."
        ),
        "entities_involved": ["transaction", "shopping"],
        "systems_involved": ["ibm", "unisys"],
        "join_key": "customerId",
        "ibm_fields": ["customerId", "amount", "date"],
        "unisys_fields": ["loyaltyPoints", "merchant", "category"],
        "business_value": (
            "Helps loyalty program managers assess engagement — are high-spend "
            "customers accumulating proportional loyalty rewards?"
        ),
        "trigger_entities": {"shopping", "transaction"},
        "trigger_metrics": {"total_spend"},
        "trigger_tasks": {"analyze", "reconcile"},
    },
    {
        "view_id": "cart_conversion_analysis",
        "name": "Cart Conversion and Spend Impact",
        "description": (
            "Joins IBM spend data with Unisys cart status (completed/abandoned) to "
            "understand how cart decisions translate into actual financial impact."
        ),
        "entities_involved": ["transaction", "shopping"],
        "systems_involved": ["ibm", "unisys"],
        "join_key": "customerId",
        "ibm_fields": ["customerId", "amount", "date", "transactionType"],
        "unisys_fields": ["cartStatus", "merchant", "category", "browsingSessionMinutes"],
        "business_value": (
            "Quantifies cart abandonment's revenue impact — which merchants and "
            "categories have the highest abandonment and what is the lost spend potential."
        ),
        "trigger_entities": {"shopping"},
        "trigger_metrics": None,
        "trigger_tasks": {"analyze", "compare"},
    },
    {
        "view_id": "browsing_to_spend_funnel",
        "name": "Browsing Behaviour to Spend Conversion",
        "description": (
            "Correlates Unisys browsing session minutes with IBM spend amounts to reveal "
            "whether longer browsing sessions translate to higher spend."
        ),
        "entities_involved": ["transaction", "shopping"],
        "systems_involved": ["ibm", "unisys"],
        "join_key": "customerId",
        "ibm_fields": ["customerId", "amount", "date"],
        "unisys_fields": ["browsingSessionMinutes", "cartStatus", "merchant"],
        "business_value": (
            "Guides UX and marketing investment — if browsing time drives spend, "
            "improve product discovery; if not, optimise checkout conversion."
        ),
        "trigger_entities": {"shopping"},
        "trigger_metrics": {"average_spend"},
        "trigger_tasks": {"analyze"},
    },
]


def _score_view(view_def: Dict[str, Any], intent: Dict[str, Any]) -> float:
    score = 0.0
    intent_entities = set(intent.get("entities", []))
    intent_metric = intent.get("metric")
    intent_task = intent.get("task", "")
    intent_attributes = {str(attr).lower() for attr in intent.get("attributes", [])}
    intent_terms = _term_tokens({
        *{str(entity).lower() for entity in intent_entities},
        *intent_attributes,
        str(intent_metric or "").lower(),
        str(intent_task or "").lower(),
    })
    requires_federation = intent.get("requires_federation", False)

    trigger_entities: set = view_def.get("trigger_entities", set())
    trigger_metrics = view_def.get("trigger_metrics") or set()
    trigger_tasks: set = view_def.get("trigger_tasks", set())

    entity_overlap = len(intent_entities & trigger_entities)
    score += entity_overlap * 0.35

    if intent_metric and intent_metric in trigger_metrics:
        score += 0.25

    if intent_task in trigger_tasks:
        score += 0.20

    unisys_fields = {str(field).lower() for field in view_def.get("unisys_fields", [])}
    if intent_terms & {"reward", "rewards", "loyalty", "loyaltypoints", "points"}:
        if view_def.get("view_id") == "loyalty_spend_correlation":
            score += 0.30
        elif "loyaltypoints" in unisys_fields:
            score += 0.10

    if requires_federation:
        score += 0.15

    both_systems = {"ibm", "unisys"}
    if intent_entities & {"transaction", "account"} and intent_entities & {"shopping"}:
        score += 0.05

    return round(min(score, 1.0), 3)


def _recommendation_reason(view_def: Dict[str, Any], score: float, intent: Dict[str, Any]) -> str:
    if score >= 0.7:
        return (
            f"High relevance: intent entities {intent.get('entities')} directly "
            f"align with this view's join pattern ({view_def['join_key']}) and "
            f"the requested metric '{intent.get('metric')}' is served by this view."
        )
    elif score >= 0.4:
        return (
            f"Moderate relevance: partial entity match — this view adds "
            f"{', '.join(view_def['unisys_fields'][:3])} enrichment that may answer "
            f"the {intent.get('task', 'fetch')} task."
        )
    else:
        return (
            "Low relevance: included as a candidate; the intent does not strongly "
            "target this view's entities but federation context is active."
        )


def recommend_views(
    relationships: List[EntityRelationship],
    intent: Dict[str, Any],
    top_n: int = 3,
) -> List[FederatedView]:
    scored: List[tuple[float, Dict[str, Any]]] = []
    intent_terms = _term_tokens({
        *{str(entity).lower() for entity in intent.get("entities", [])},
        *{str(attr).lower() for attr in intent.get("attributes", [])},
        str(intent.get("metric") or "").lower(),
        str(intent.get("task") or "").lower(),
    })
    loyalty_intent = bool(intent_terms & {"reward", "rewards", "loyalty", "loyaltypoints", "points"})

    for view_def in VIEW_CATALOG:
        score = _score_view(view_def, intent)
        scored.append((score, view_def))

    scored.sort(
        key=lambda x: (
            x[0],
            1 if loyalty_intent and x[1]["view_id"] == "loyalty_spend_correlation" else 0,
        ),
        reverse=True,
    )

    results: List[FederatedView] = []
    for score, view_def in scored[:top_n]:
        reason = _recommendation_reason(view_def, score, intent)
        results.append(
            FederatedView(
                view_id=view_def["view_id"],
                name=view_def["name"],
                description=view_def["description"],
                entities_involved=view_def["entities_involved"],
                systems_involved=view_def["systems_involved"],
                join_key=view_def["join_key"],
                ibm_fields=view_def["ibm_fields"],
                unisys_fields=view_def["unisys_fields"],
                business_value=view_def["business_value"],
                applicability_score=score,
                recommended=score >= 0.4,
                recommendation_reason=reason,
            )
        )

    return results


def get_all_views() -> List[FederatedView]:
    """Return every view in the catalog with neutral scoring."""
    return [
        FederatedView(
            view_id=v["view_id"],
            name=v["name"],
            description=v["description"],
            entities_involved=v["entities_involved"],
            systems_involved=v["systems_involved"],
            join_key=v["join_key"],
            ibm_fields=v["ibm_fields"],
            unisys_fields=v["unisys_fields"],
            business_value=v["business_value"],
            applicability_score=1.0,
            recommended=True,
            recommendation_reason="Full catalog listing.",
        )
        for v in VIEW_CATALOG
    ]
