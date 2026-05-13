"""Pydantic schemas for the Federation Intelligence Layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EntityRelationship(BaseModel):
    source_entity: str = Field(description="Entity on the source system (e.g. 'transaction')")
    target_entity: str = Field(description="Entity on the target system (e.g. 'shopping')")
    source_system: str = Field(description="System owning the source entity (ibm/unisys)")
    target_system: str = Field(description="System owning the target entity (ibm/unisys)")
    join_key: str = Field(description="Field used to join the two entities")
    relationship_type: str = Field(
        description="enrichment | reconciliation | reference | mirror"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Relationship confidence score")
    reasoning: str = Field(description="Why these entities are related")


class FederatedViewField(BaseModel):
    field_name: str
    source_system: str
    role: str = Field(description="financial_authority | behavioral_enrichment | join_key")
    description: str


class FederatedView(BaseModel):
    view_id: str = Field(description="Unique identifier for this federated view")
    name: str = Field(description="Human-readable view name")
    description: str = Field(description="What business question this view answers")
    entities_involved: List[str]
    systems_involved: List[str]
    join_key: str
    ibm_fields: List[str] = Field(description="Fields contributed by IBM (financial authority)")
    unisys_fields: List[str] = Field(description="Fields contributed by Unisys (behavioral enrichment)")
    business_value: str = Field(description="The business insight this view enables")
    applicability_score: float = Field(ge=0.0, le=1.0, description="Relevance score for the current intent")
    recommended: bool = Field(description="Whether this view is recommended for the current intent")
    recommendation_reason: str


class FederationPlan(BaseModel):
    primary_source: str = Field(description="System that owns financial truth (always 'ibm')")
    enrichment_source: str = Field(description="System providing behavioral enrichment (always 'unisys')")
    join_strategy: str = Field(description="left | inner | outer — how to join the two sources")
    join_key: str
    financial_authority: str = Field(
        description="Explicit note: IBM CardDemo owns all financial amounts"
    )
    enrichment_fields: List[str] = Field(description="Fields that Unisys adds on top of IBM")
    execution_steps: List[str] = Field(description="Ordered steps to execute this federation")
    double_counting_guard: str = Field(
        description="Rule preventing Unisys amounts from being summed with IBM amounts"
    )


class LineageRecord(BaseModel):
    field: str
    source_system: str
    source_entity: str
    transformation: Optional[str] = None


class FederationIntelligenceOutput(BaseModel):
    """Complete output of the Federation Intelligence Layer."""

    entity_relationships: List[EntityRelationship] = Field(
        description="All cross-system entity relationships discovered"
    )
    recommended_views: List[FederatedView] = Field(
        description="Ranked federated business views for the current intent"
    )
    top_view: Optional[FederatedView] = Field(
        None, description="The single best federated view for the request"
    )
    federation_plan: FederationPlan = Field(
        description="How to execute the recommended federation"
    )
    federated_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Actual federated data result (populated when a customerId filter is present)",
    )
    lineage: List[LineageRecord] = Field(
        description="Data lineage — which system contributed each field"
    )
    governance: Dict[str, Any] = Field(
        description="Audit metadata: sources, join keys, timestamp, confidence"
    )
    capability_discovery: Dict[str, Any] = Field(
        default_factory=dict,
        description="Grounded discovery of available and missing related capabilities",
    )
    overall_confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Natural-language explanation of the federation decision")


class FederationAnalyzeRequest(BaseModel):
    """Request body for /api/federation/analyze"""

    intent: Dict[str, Any] = Field(description="IntentOutput serialized as dict")
    context: Dict[str, Any] = Field(description="ContextOutput serialized as dict")
    normalized_output: Optional[Dict[str, Any]] = Field(
        default=None,
        description="NormalizationAgent response serialized as dict; preferred input for federation",
    )
    execute: bool = Field(
        default=True,
        description="If True and a customerId filter exists, run the federation and return real data",
    )
    use_llm: bool = Field(
        default=True,
        description="If True, use the LLM to refine view selection and reasoning over grounded candidates",
    )


class FederationExecuteRequest(BaseModel):
    """Request body for /api/federation/execute — direct execution without pipeline."""

    customer_id: int
    date: Optional[str] = None
    view_id: str = Field(
        default="customer_spend_enriched",
        description="Which federated view to execute",
    )
