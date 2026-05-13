"""
schemas.py - Pydantic models for Intent output

CRITICAL: Entities are OBJECTS, not identifiers
Identifiers (customerId, accountId) are FILTERS, not entities
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class FilterCondition(BaseModel):
    """Structured filter condition: field=value"""
    field: str
    value: Union[str, int, float, bool, None]
    
    class Config:
        json_schema_extra = {
            "example": {"field": "customerId", "value": 101}
        }


class FilterCriteria(BaseModel):
    """Filter conditions for data queries
    
    IMPORTANT: Filters contain:
    - Field-value conditions (customerId, date, etc.)
    - Time ranges
    
    NOT: Entity names or objects
    """
    time_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Date range {start: YYYY-MM-DD, end: YYYY-MM-DD}"
    )
    conditions: List[FilterCondition] = Field(
        default_factory=list,
        description="Field-value filter conditions"
    )


class IntentOutput(BaseModel):
    """
    Pure Intent Understanding Output
    
    ENTITIES: Business objects (shopping, inventory, transaction, account)
    FILTERS: Identifiers and conditions (customerId, date range, etc.)
    
    NO: commands, APIs, parameters, execution logic
    YES: semantic understanding of user requirements
    """
    task: str = Field(
        description="fetch|discover|reconcile|analyze|compare|transform"
    )
    entities: List[str] = Field(
        description="Business objects: shopping, inventory, transaction, account (NOT identifiers)"
    )
    attributes: List[str] = Field(
        description="Specific fields needed from entities"
    )
    filters: FilterCriteria = Field(
        default_factory=FilterCriteria,
        description="Conditions and constraints (customerId, date, etc.)"
    )
    systems: List[str] = Field(
        description="ibm|unisys based on entity ownership"
    )
    metric: Optional[str] = Field(
        default=None,
        description="Business metric requested, e.g. total_spend, transaction_count"
    )
    aggregation: Optional[str] = Field(
        default=None,
        description="Aggregation to apply, e.g. sum, count, avg, max, min"
    )
    output_mode: str = Field(
        default="records",
        description="records|aggregate|insight depending on requested output shape"
    )
    requires_federation: bool = Field(
        default=False,
        description="Whether the request likely needs more than one system for a correct answer"
    )
    priority: str = Field(
        description="low|medium|high (high for compare/analyze)"
    )
    confidence_score: float = Field(
        ge=0.0, 
        le=1.0,
        description="Confidence in extraction (0.0-1.0)"
    )
    
    @validator("task")
    def validate_task(cls, v):
        valid = ["fetch", "discover", "reconcile", "analyze", "compare", "transform"]
        if v not in valid:
            raise ValueError(f"task must be one of {valid}")
        return v
    
    @validator("priority")
    def validate_priority(cls, v):
        valid = ["low", "medium", "high"]
        if v not in valid:
            raise ValueError(f"priority must be one of {valid}")
        return v

    @validator("output_mode")
    def validate_output_mode(cls, v):
        valid = ["records", "aggregate", "insight", "capabilities"]
        if v not in valid:
            raise ValueError(f"output_mode must be one of {valid}")
        return v
