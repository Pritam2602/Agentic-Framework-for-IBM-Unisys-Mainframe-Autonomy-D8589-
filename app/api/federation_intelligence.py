"""
app/api/federation_intelligence.py — REST endpoints for the Federation Intelligence Layer.

Endpoints:
  POST /api/federation/analyze   — analyze intent + context, return intelligence output
  POST /api/federation/execute   — directly execute a named federated view for a customer
  GET  /api/federation/views     — catalog of all available federated views
  GET  /api/federation/health    — health check
"""

from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from federation_intelligence import run_federation_intelligence
from federation_intelligence.schemas import (
    FederationAnalyzeRequest,
    FederationExecuteRequest,
    FederationIntelligenceOutput,
    FederatedView,
)
from federation_intelligence.executor import execute_view
from federation_intelligence.view_recommender import get_all_views
from federation_intelligence.discovery import discover_capabilities

router = APIRouter(prefix="/api/federation", tags=["federation-intelligence"])


@router.post("/analyze", response_model=FederationIntelligenceOutput)
async def analyze(request: FederationAnalyzeRequest) -> FederationIntelligenceOutput:
    """
    Run the Federation Intelligence Layer.

    Input:
      - intent: output of the Intent Agent (IntentOutput as dict)
      - context: output of the Context Resolution Agent (ContextOutput as dict)
      - execute: if True and a customerId filter is present, run the federation and return data

    Output:
      - Entity relationships discovered across IBM and Unisys
      - Ranked federated business views for this intent
      - Federation execution plan
      - Actual federated data (if execute=True and customerId present)
      - LLM-generated suggested next explorations
      - Lineage records for every output field
      - Governance metadata
    """
    try:
        result = run_federation_intelligence(
            intent=request.intent,
            context=request.context,
            normalized_output=request.normalized_output,
            execute=request.execute,
            enable_llm=request.use_llm,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Federation Intelligence failed: {exc}",
        )


@router.post("/execute", response_model=Dict[str, Any])
async def execute(request: FederationExecuteRequest) -> Dict[str, Any]:
    """
    Directly execute a named federated view for a given customer.

    Available view_ids:
      - customer_spend_enriched      (default)
      - merchant_category_spend
      - loyalty_spend_correlation
      - cart_conversion_analysis
      - browsing_to_spend_funnel
      - fraud_risk_assessment
    """
    try:
        result = execute_view(
            view_id=request.view_id,
            customer_id=request.customer_id,
            date=request.date,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Federation execution failed: {exc}",
        )


@router.get("/views", response_model=List[FederatedView])
async def list_views() -> List[FederatedView]:
    """Return the full catalog of available federated business views."""
    return get_all_views()


@router.post("/discover", response_model=Dict[str, Any])
async def discover(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Discover related capabilities from current schemas and datasets."""
    return discover_capabilities(intent)


@router.get("/write-feasibility", response_model=Dict[str, Any])
async def write_feasibility() -> Dict[str, Any]:
    """Describe the feasible save/update path for federated demo use cases."""
    return {
        "status": "feasible_for_unisys_enrichment",
        "supported_use_cases": [
            {
                "id": 1,
                "name": "Customer Shopping 360",
                "read": "IBM transactions + Unisys shopping enrichment",
                "save_update": "Create/update Unisys shopping enrichment events.",
            },
            {
                "id": 3,
                "name": "Loyalty & Rewards Optimization",
                "read": "IBM spend + Unisys loyaltyPoints, merchant, and category context",
                "save_update": "Update loyaltyPoints and related enrichment fields on Unisys shopping events.",
            },
        ],
        "write_boundaries": {
            "ibm": "read_only in this demo; IBM remains financial authority",
            "unisys": {
                "create_endpoint": "POST /api/shopping on the ePortal service",
                "update_endpoint": "PATCH /api/shopping/enrichment on the ePortal service",
                "writable_fields": [
                    "loyaltyPoints",
                    "browsingSessionMinutes",
                    "cartStatus",
                    "merchantCategory",
                ],
            },
        },
        "guardrails": [
            "Do not update or add Unisys amount to IBM amount for total spend.",
            "Use Unisys writes only for behavioral enrichment/context.",
            "Require a stable event key: customerId + date + merchant.",
        ],
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "federation-intelligence",
        "capabilities": [
            "entity_relationship_discovery",
            "federated_view_recommendation",
            "federation_plan_generation",
            "federation_execution",
            "data_lineage_tracking",
            "governance_audit",
        ],
        "views_available": len(get_all_views()),
    }
