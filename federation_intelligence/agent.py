"""Federation Intelligence Agent — identifies entity relationships and recommends federated views."""

from __future__ import annotations

import datetime
import json
import logging
import re
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from intent_agent.config import build_llm_model

from .discovery import discover_capabilities
from .entity_graph import build_entity_graph, resolve_join_key
from .executor import execute_view
from .recommendations import build_discovery_recommendations
from .schemas import (
    EntityRelationship,
    FederationIntelligenceOutput,
    FederationPlan,
    FederatedView,
    LineageRecord,
)
from .view_recommender import recommend_views

logger = logging.getLogger(__name__)


FEDERATION_INTELLIGENCE_SYSTEM_PROMPT = """
You are an enterprise Federation Intelligence Agent for IBM + Unisys data federation.

Your job is to reason over grounded entity relationships, candidate federated views,
lineage, governance metadata, and the user's intent. You may recommend the best view
ONLY from the provided candidate view IDs.

Critical domain rule:
- IBM CardDemo is the financial authority for all spend/amount totals.
- Unisys ePortal shopping data is behavioral enrichment only.
- NEVER recommend summing IBM amount + Unisys amount for total_spend.

Return STRICT JSON only:
{{
  "recommended_view_id": "one of the candidate view IDs",
  "overall_confidence": 0.0,
  "reasoning": "short business-readable explanation",
  "governance_notes": ["short audit/governance note"],
  "plan_notes": ["short execution or lineage note"]
}}
"""


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


def _records_from_normalized(normalized_output: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not normalized_output:
        return []
    records = normalized_output.get("records")
    if isinstance(records, list):
        return [record for record in records if isinstance(record, dict)]
    canonical = normalized_output.get("canonical_output", {})
    data = canonical.get("data") if isinstance(canonical, dict) else None
    if isinstance(data, list):
        return [record for record in data if isinstance(record, dict)]
    return []


def _entities_from_normalized(records: List[Dict[str, Any]]) -> List[str]:
    entities = []
    for record in records:
        entity = record.get("entity")
        if entity and entity not in entities:
            entities.append(str(entity))
    return entities


def _build_normalized_federated_result(
    records: List[Dict[str, Any]],
    top_view: Optional[FederatedView],
    intent: Dict[str, Any],
) -> Dict[str, Any]:
    ibm_records = [record for record in records if record.get("source_system") == "ibm"]
    unisys_records = [record for record in records if record.get("source_system") == "unisys"]

    ibm_total = round(
        sum(float(record.get("amount") or 0) for record in ibm_records),
        2,
    )

    category_totals: Dict[str, float] = {}
    merchant_events: Dict[str, int] = {}
    merchant_observed_amounts: Dict[str, float] = {}
    loyalty_points = 0
    cart_statuses: Dict[str, int] = {}
    browsing_minutes = 0
    unisys_observed_total = 0.0

    for record in unisys_records:
        observed_amount = float(record.get("amount") or 0)
        unisys_observed_total += observed_amount
        category = record.get("category") or "unknown"
        category_totals[category] = round(
            category_totals.get(category, 0) + observed_amount,
            2,
        )
        merchant = record.get("merchant")
        if merchant:
            merchant_events[merchant] = merchant_events.get(merchant, 0) + 1
            merchant_observed_amounts[merchant] = round(
                merchant_observed_amounts.get(merchant, 0) + observed_amount,
                2,
            )
        enrichment = record.get("enrichment") or {}
        loyalty_points += int(enrichment.get("loyaltyPoints") or 0)
        cart_status = enrichment.get("cartStatus")
        if cart_status:
            cart_statuses[cart_status] = cart_statuses.get(cart_status, 0) + 1
        browsing_minutes += int(enrichment.get("browsingSessionMinutes") or 0)

    customer_ids = sorted(
        {str(record.get("customer_id")) for record in records if record.get("customer_id")}
    )
    dates = sorted({str(record.get("date")) for record in records if record.get("date")})
    unisys_observed_total = round(unisys_observed_total, 2)
    amount_variance = round(unisys_observed_total - ibm_total, 2)
    reconciliation_status = "matched" if amount_variance == 0 else "variance_detected"
    reconciliation_warning = None
    if amount_variance != 0:
        reconciliation_warning = (
            "Unisys observed shopping amounts do not reconcile exactly to the IBM "
            "financial total for the same filter. IBM remains authoritative for "
            "total_spend; Unisys amounts are retained only as behavioral/enrichment "
            "signals and must not be summed into the ledger total."
        )

    return {
        "view_id": top_view.view_id if top_view else "normalized_federated_view",
        "customerIds": customer_ids,
        "dates": dates,
        "federation": {
            "total_spend": ibm_total,
            "ibm_transaction_count": len(ibm_records),
            "unisys_enrichment_count": len(unisys_records),
            "unisys_observed_amount_total": unisys_observed_total,
            "amount_variance_unisys_minus_ibm": amount_variance,
            "note": (
                "total_spend is computed from normalized IBM records only. "
                "Unisys normalized records provide behavioral enrichment and are not additive."
            ),
        },
        "behavioral_enrichment": {
            "category_observed_amounts": category_totals,
            "merchant_events": merchant_events,
            "merchant_observed_amounts": merchant_observed_amounts,
            "loyalty": {"total_loyalty_points": loyalty_points},
            "cart_status_breakdown": cart_statuses,
            "browsing": {"total_browsing_minutes": browsing_minutes},
        },
        "reconciliation": {
            "status": reconciliation_status,
            "ibm_authoritative_total": ibm_total,
            "unisys_observed_total": unisys_observed_total,
            "variance": amount_variance,
            "warning": reconciliation_warning,
            "rule": "Use IBM amount for total_spend; use Unisys amount only as observed behavior/enrichment.",
        },
        "metadata": {
            "input": "normalization_agent",
            "join_key": "customer_id",
            "source_record_count": len(records),
            "requested_metric": intent.get("metric"),
        },
        "normalized_records": records,
    }


def _llm_refine_output(
    output: FederationIntelligenceOutput,
    intent: Dict[str, Any],
    context: Dict[str, Any],
    model: Any,
) -> FederationIntelligenceOutput:
    """Use an LLM to refine view choice and explanation over grounded candidates."""
    if model is None or not output.recommended_views:
        return output

    forced_view_id = _forced_view_id(intent)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", FEDERATION_INTELLIGENCE_SYSTEM_PROMPT),
            ("user", "{federation_request}"),
        ]
    )
    request = {
        "intent": intent,
        "context_summary": {
            "resolution_confidence": context.get("resolution_confidence"),
            "is_federation": context.get("is_federation"),
            "systems_checked": context.get("systems_checked"),
        },
        "entity_relationships": [
            relationship.model_dump() for relationship in output.entity_relationships
        ],
        "candidate_views": [view.model_dump() for view in output.recommended_views],
        "current_top_view": output.top_view.model_dump() if output.top_view else None,
        "federation_plan": output.federation_plan.model_dump(),
        "governance": output.governance,
    }

    try:
        chain = prompt | model
        result = chain.invoke({"federation_request": json.dumps(request, default=str)})
        json_match = re.search(r"\{[\s\S]*\}", result.content)
        if not json_match:
            raise ValueError("No JSON found in LLM output")
        data = json.loads(json_match.group())
    except Exception as exc:
        logger.warning("[Federation Intelligence] LLM refinement failed: %s", exc)
        output.governance["llm_refinement"] = "fallback_grounded"
        return output

    candidate_by_id = {view.view_id: view for view in output.recommended_views}
    recommended_id = forced_view_id or data.get("recommended_view_id")
    if recommended_id in candidate_by_id:
        selected = candidate_by_id[recommended_id]
        output.recommended_views = [
            selected,
            *[view for view in output.recommended_views if view.view_id != recommended_id],
        ]
        output.top_view = selected
        output.federation_plan = _build_federation_plan(output.entity_relationships, selected)

    confidence = data.get("overall_confidence")
    if isinstance(confidence, (int, float)):
        grounded = output.overall_confidence
        output.overall_confidence = round(
            min(max((grounded * 0.7) + (float(confidence) * 0.3), 0.0), 0.97),
            3,
        )
        output.governance["overall_confidence"] = output.overall_confidence

    if data.get("reasoning"):
        output.reasoning = str(data["reasoning"])

    if output.top_view and output.top_view.view_id == "fraud_risk_assessment":
        current_result = output.federated_result if isinstance(output.federated_result, dict) else {}
        if current_result.get("view_id") != "fraud_risk_assessment":
            customer_id = _extract_customer_id(intent)
            if customer_id is not None:
                output.federated_result = execute_view(
                    "fraud_risk_assessment",
                    customer_id,
                    _extract_date(intent),
                )
                output.governance["federation_executed"] = True
                output.governance["fraud_executor_applied_after_refinement"] = True

    output.governance["llm_refinement"] = "applied"
    output.governance["llm_governance_notes"] = data.get("governance_notes", [])
    output.governance["llm_plan_notes"] = data.get("plan_notes", [])
    if forced_view_id:
        output.governance["forced_view_reason"] = "Fraud/risk intent requires fraud_risk_assessment."
    return output


def _forced_view_id(intent: Dict[str, Any]) -> Optional[str]:
    """Return a deterministic view override for high-specificity intents."""
    terms = {
        str(intent.get("task") or "").lower(),
        str(intent.get("metric") or "").lower(),
        *{str(entity).lower() for entity in intent.get("entities", [])},
        *{str(attr).lower() for attr in intent.get("attributes", [])},
    }
    expanded = set(terms)
    for term in terms:
        expanded.update(token for token in re.split(r"[^a-z0-9_]+", term) if token)
    fraud_terms = {
        "fraud",
        "fraudulent",
        "fraud_risk",
        "risk",
        "risky",
        "suspicious",
        "unusual",
        "anomaly",
        "anomalous",
        "genuine",
        "fake",
        "unauthorized",
        "unauthorised",
    }
    if expanded & fraud_terms:
        return "fraud_risk_assessment"
    return None


def run(
    intent: Dict[str, Any],
    context: Dict[str, Any],
    normalized_output: Optional[Dict[str, Any]] = None,
    execute: bool = True,
    model: Any = None,
    enable_llm: bool = True,
) -> FederationIntelligenceOutput:
    """Entry point for the Federation Intelligence Agent."""

    normalized_records = _records_from_normalized(normalized_output)
    normalized_entities = _entities_from_normalized(normalized_records)
    intent_entities: List[str] = normalized_entities or intent.get("entities", [])
    requires_federation: bool = intent.get("requires_federation", False)

    if not intent_entities and not requires_federation:
        intent_entities = ["transaction", "shopping"]

    relationships = build_entity_graph(intent_entities)
    capability_discovery = discover_capabilities(intent)
    llm_model = None
    if enable_llm:
        llm_model = model if model is not None else build_llm_model(logger=logger)
    suggested_explorations = build_discovery_recommendations(
        intent=intent,
        capability_discovery=capability_discovery,
        context=context,
        model=llm_model,
        enable_llm=enable_llm,
    )

    views = recommend_views(relationships, intent, top_n=5)
    forced_view_id = _forced_view_id(intent)
    if forced_view_id:
        selected = next((view for view in views if view.view_id == forced_view_id), None)
        if selected:
            views = [
                selected,
                *[view for view in views if view.view_id != forced_view_id],
            ]
    top_view = views[0] if views else None

    federation_plan = _build_federation_plan(relationships, top_view)
    lineage = _build_lineage(top_view)

    federated_result: Optional[Dict[str, Any]] = None
    executed = False

    fraud_view_selected = bool(top_view and top_view.view_id == "fraud_risk_assessment")

    if fraud_view_selected and execute:
        customer_id = _extract_customer_id(intent)
        if customer_id is not None:
            date = _extract_date(intent)
            federated_result = execute_view("fraud_risk_assessment", customer_id, date)
            executed = True

    if federated_result is None and normalized_records:
        federated_result = _build_normalized_federated_result(
            normalized_records,
            top_view,
            intent,
        )
        executed = True
    elif federated_result is None and execute:
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
        "consumed_normalization_output": bool(normalized_records),
        "normalized_record_count": len(normalized_records),
        "overall_confidence": confidence,
        "entity_relationships_count": len(relationships),
        "views_evaluated": len(views),
        "capability_discovery_mode": capability_discovery.get("mode"),
        "suggested_explorations_count": len(suggested_explorations),
    }

    if isinstance(federated_result, dict) and federated_result.get("reconciliation"):
        reconciliation = federated_result["reconciliation"]
        governance["amount_reconciliation"] = reconciliation
        if reconciliation.get("status") == "variance_detected":
            governance["reconciliation_warning"] = reconciliation.get("warning")

    grounded_output = FederationIntelligenceOutput(
        entity_relationships=relationships,
        recommended_views=views,
        top_view=top_view,
        federation_plan=federation_plan,
        federated_result=federated_result,
        lineage=lineage,
        governance=governance,
        capability_discovery=capability_discovery,
        suggested_explorations=suggested_explorations,
        overall_confidence=confidence,
        reasoning=reasoning,
    )

    if enable_llm:
        return _llm_refine_output(
            output=grounded_output,
            intent=intent,
            context=context,
            model=llm_model,
        )

    grounded_output.governance["llm_refinement"] = "disabled"
    return grounded_output
