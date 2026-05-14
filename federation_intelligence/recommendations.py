"""Discovery recommendations for conversational follow-up exploration."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate


logger = logging.getLogger(__name__)


DISCOVERY_RECOMMENDATION_SYSTEM_PROMPT = """
You are a Discovery Recommendation Agent for an enterprise IBM + Unisys data
federation assistant.

Your job is to suggest useful next explorations after the current answer.
These are conversational follow-up actions, not data that was already fetched.

Use only the grounded intent, context, and capability metadata provided.
Do not claim that a related capability was executed in the current answer.
If inventory is related, phrase it as an exploration unless the current intent
explicitly asks for inventory.

Return STRICT JSON only:
{{
  "suggested_explorations": [
    {{
      "id": "short_snake_case_id",
      "title": "short button label",
      "prompt": "natural language follow-up query",
      "reason": "one concise business reason",
      "related_entity": "entity_or_capability",
      "relationship": "source -> relationship -> target",
      "confidence": 0.0
    }}
  ]
}}

Rules:
- Return 3 to 5 suggestions.
- Prefer suggestions that help the user discover what else is possible.
- Keep titles under 32 characters.
- Keep prompts executable as standalone user queries.
- Confidence must be between 0.0 and 0.95.
- Do not invent unsupported systems or fields.
- Do not output markdown.
"""


def _customer_prompt_suffix(intent: Dict[str, Any]) -> str:
    filters = intent.get("filters") or {}
    for condition in filters.get("conditions") or []:
        if str(condition.get("field", "")).lower() == "customerid":
            value = condition.get("value")
            if value not in (None, ""):
                return f" for customer {value}"
    return ""


def _fallback_recommendations(
    intent: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Small deterministic safety net when the LLM is unavailable."""
    entities = {str(entity).lower() for entity in intent.get("entities", [])}
    attributes = {str(attribute).lower() for attribute in intent.get("attributes", [])}
    requested_inventory = bool(
        entities & {"inventory"}
        or attributes & {"inventory", "inventory_data", "stock", "stock_data", "sku"}
    )
    customer_suffix = _customer_prompt_suffix(intent)

    recommendations: List[Dict[str, Any]] = []

    fraud_intent = bool(
        attributes & {"fraud_risk"}
        or entities & {"fraud", "risk"}
    )

    if "shopping" in entities:
        if not requested_inventory:
            recommendations.append(
                {
                    "id": "explore_inventory",
                    "title": "View Inventory Insights",
                    "prompt": "Check related inventory availability for the shopping merchants and categories.",
                    "reason": "Shopping data contains merchant and category signals that can guide inventory exploration.",
                    "related_entity": "inventory",
                    "relationship": "shopping -> merchant/category -> inventory",
                    "confidence": 0.72,
                }
            )

        recommendations.extend(
            [
                {
                    "id": "analyze_rewards",
                    "title": "Analyze Reward Points",
                    "prompt": f"Analyze loyalty reward points versus IBM spend{customer_suffix}.",
                    "reason": "Shopping records include loyaltyPoints and IBM provides authoritative spend.",
                    "related_entity": "loyalty",
                    "relationship": "shopping + transaction -> rewards",
                    "confidence": 0.88,
                },
                {
                    "id": "merchant_analytics",
                    "title": "View Merchant Analytics",
                    "prompt": f"Compare merchant spending patterns and category-wise shopping behavior{customer_suffix}.",
                    "reason": "Merchant, category, and observed shopping behavior are already available.",
                    "related_entity": "merchant_category",
                    "relationship": "shopping -> merchant -> category",
                    "confidence": 0.9,
                },
                {
                    "id": "cart_conversion",
                    "title": "Inspect Cart Conversion",
                    "prompt": f"Analyze cart status, abandoned carts, and browsing-to-spend behavior{customer_suffix}.",
                    "reason": "Shopping records include cartStatus and browsingSessionMinutes.",
                    "related_entity": "cart",
                    "relationship": "shopping -> cart/browsing",
                    "confidence": 0.84,
                },
            ]
        )
        if not fraud_intent:
            recommendations.append(
                {
                    "id": "fraud_risk_check",
                    "title": "Check Fraud / Risk Signals",
                    "prompt": f"Run fraud and risk assessment{customer_suffix} using IBM transactions and Unisys behavior.",
                    "reason": (
                        "IBM transactions can be cross-checked with Unisys cart status, "
                        "browsing time, and observed amount to detect suspicious charges."
                    ),
                    "related_entity": "fraud_risk",
                    "relationship": "transaction -> shopping (behavioral validation)",
                    "confidence": 0.82,
                }
            )

    if fraud_intent:
        recommendations.extend(
            [
                {
                    "id": "fraud_high_value_outliers",
                    "title": "List High-Value Outliers",
                    "prompt": f"List transactions whose amount is at least three times the average{customer_suffix}.",
                    "reason": "High-value outliers vs the customer's baseline are a primary fraud signal.",
                    "related_entity": "transaction",
                    "relationship": "transaction -> customer baseline",
                    "confidence": 0.86,
                },
                {
                    "id": "fraud_abandoned_cart_charge",
                    "title": "Inspect Abandoned-Cart Charges",
                    "prompt": f"Show IBM charges that occurred on dates with only abandoned/wishlisted Unisys carts{customer_suffix}.",
                    "reason": "Charges without supporting completed-cart behavior look suspicious.",
                    "related_entity": "shopping",
                    "relationship": "transaction -> shopping.cartStatus",
                    "confidence": 0.84,
                },
                {
                    "id": "fraud_missing_context",
                    "title": "Find Charges Without Behavior",
                    "prompt": f"Show high-value IBM transactions with no matching Unisys shopping events{customer_suffix}.",
                    "reason": "Material charges with no behavioral evidence are common fraud indicators.",
                    "related_entity": "transaction",
                    "relationship": "transaction -> shopping (date join)",
                    "confidence": 0.8,
                },
            ]
        )

    if "inventory" in entities or requested_inventory:
        recommendations.extend(
            [
                {
                    "id": "low_stock",
                    "title": "Find Low-Stock Products",
                    "prompt": "Show low-stock inventory items by merchant and category.",
                    "reason": "Inventory data can be filtered by availabilityStatus and category.",
                    "related_entity": "inventory",
                    "relationship": "inventory -> availabilityStatus",
                    "confidence": 0.86,
                },
                {
                    "id": "inventory_shopping_link",
                    "title": "Link Inventory To Shopping Demand",
                    "prompt": "Compare shopping category interest with inventory availability.",
                    "reason": "Inventory and shopping share merchant/category context.",
                    "related_entity": "shopping",
                    "relationship": "inventory -> merchant/category -> shopping",
                    "confidence": 0.78,
                },
            ]
        )

    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for recommendation in recommendations:
        if recommendation["id"] in seen:
            continue
        seen.add(recommendation["id"])
        unique.append(recommendation)

    return unique[:5]


def _compact_capability_discovery(capability_discovery: Dict[str, Any]) -> Dict[str, Any]:
    related = capability_discovery.get("related_capabilities") or []
    return {
        "mode": capability_discovery.get("mode"),
        "related_capabilities": [
            {
                "entity": item.get("entity"),
                "status": item.get("status"),
                "discovery_type": item.get("discovery_type"),
                "confidence": item.get("confidence"),
                "source": item.get("source"),
                "relationship": item.get("relationship"),
                "reason": item.get("reason"),
            }
            for item in related
            if isinstance(item, dict)
        ],
        "discovery_notes": capability_discovery.get("discovery_notes", [])[:5],
    }


def _clean_recommendation(item: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    title = str(item.get("title") or "").strip()
    prompt = str(item.get("prompt") or "").strip()
    reason = str(item.get("reason") or "").strip()
    if not title or not prompt or not reason:
        return None

    raw_confidence = item.get("confidence", 0.7)
    try:
        confidence = float(raw_confidence)
    except (TypeError, ValueError):
        confidence = 0.7

    confidence = round(min(max(confidence, 0.0), 0.95), 2)
    recommendation_id = str(item.get("id") or "").strip()
    if not recommendation_id:
        recommendation_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    if not recommendation_id:
        recommendation_id = f"suggestion_{index + 1}"

    return {
        "id": recommendation_id,
        "title": title[:48],
        "prompt": prompt,
        "reason": reason,
        "related_entity": str(item.get("related_entity") or item.get("entity") or "").strip() or None,
        "relationship": str(item.get("relationship") or "").strip() or None,
        "confidence": confidence,
    }


def _parse_llm_recommendations(text: str) -> List[Dict[str, Any]]:
    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("No JSON object found in recommendation response")

    data = json.loads(json_match.group())
    raw_items = data.get("suggested_explorations", [])
    if not isinstance(raw_items, list):
        raise ValueError("suggested_explorations must be a list")

    cleaned: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        recommendation = _clean_recommendation(item, index)
        if recommendation is None or recommendation["id"] in seen:
            continue
        seen.add(recommendation["id"])
        cleaned.append(recommendation)
        if len(cleaned) == 5:
            break

    if not cleaned:
        raise ValueError("No valid recommendations returned")
    return cleaned


def build_discovery_recommendations(
    intent: Dict[str, Any],
    capability_discovery: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    model: Any = None,
    enable_llm: bool = True,
) -> List[Dict[str, Any]]:
    """Suggest related explorations without executing them.

    The primary path is LLM based so recommendations are generated from the
    current user intent and metadata context instead of a static entity map.
    A small deterministic fallback keeps the UI usable when the LLM is disabled
    or unavailable.
    """
    if not enable_llm or model is None:
        return _fallback_recommendations(intent)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", DISCOVERY_RECOMMENDATION_SYSTEM_PROMPT),
            ("user", "{recommendation_request}"),
        ]
    )
    request = {
        "intent": intent,
        "context_summary": {
            "systems_checked": (context or {}).get("systems_checked"),
            "entities_resolved": (context or {}).get("entities_resolved"),
            "is_federation": (context or {}).get("is_federation"),
            "resolution_confidence": (context or {}).get("resolution_confidence"),
        },
        "capability_discovery": _compact_capability_discovery(capability_discovery),
        "product_behavior": (
            "Answer the current request first. Suggestions are optional follow-up "
            "queries and must not imply the related capability was already fetched."
        ),
    }

    try:
        chain = prompt | model
        result = chain.invoke({"recommendation_request": json.dumps(request, default=str)})
        return _parse_llm_recommendations(result.content)
    except Exception as exc:
        logger.warning("[Discovery Recommendation] LLM generation failed: %s", exc)
        return _fallback_recommendations(intent)
