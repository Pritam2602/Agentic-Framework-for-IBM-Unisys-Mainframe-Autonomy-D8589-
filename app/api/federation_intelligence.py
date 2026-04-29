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
      - Lineage records for every output field
      - Governance metadata
    """
    try:
        result = run_federation_intelligence(
            intent=request.intent,
            context=request.context,
            execute=request.execute,
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
