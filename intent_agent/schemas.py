"""
schemas.py - Pydantic models for Intent output
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FilterCriteria(BaseModel):
    """Filter conditions for data queries"""
    time_range: Optional[Dict[str, str]] = None
    conditions: List[str] = Field(default_factory=list)


class IntentOutput(BaseModel):
    """
    Pure Intent Understanding Output
    
    NO: commands, APIs, parameters, execution logic
    YES: semantic understanding of user requirements
    """
    task: str
    entities: List[str]
    attributes: List[str]
    filters: FilterCriteria = Field(default_factory=FilterCriteria)
    systems: List[str]
    priority: str
    confidence_score: float = Field(ge=0.0, le=1.0)
