"""Pydantic schemas for the LLM-backed Normalization Agent."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


SourceSystem = Literal["ibm", "unisys", "unknown"]


class CanonicalRecord(BaseModel):
    """Common intermediate record produced after execution."""

    source_system: SourceSystem = Field(description="Originating system")
    entity: str = Field(default="unknown", description="Canonical entity name")
    customer_id: Optional[str] = None
    record_id: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    transaction_type: Optional[str] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    enrichment: Dict[str, Any] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)


class NormalizationSummary(BaseModel):
    """High-level normalization metadata."""

    total_records: int = 0
    ibm_records: int = 0
    unisys_records: int = 0
    canonical_entities: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class NormalizationAgentRequest(BaseModel):
    """API request for normalizing execution outputs."""

    execution_output: Dict[str, Any] = Field(
        description="ExecutionAgent response or raw execution result payload"
    )
    intent: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    use_llm: bool = Field(default=True)


class NormalizationAgentResponse(BaseModel):
    """Normalized common intermediate structure for federation/consumer layers."""

    status: Literal["completed", "partial", "failed"]
    natural_response: str
    canonical_output: Dict[str, Any]
    records: List[CanonicalRecord] = Field(default_factory=list)
    summary: NormalizationSummary = Field(default_factory=NormalizationSummary)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
