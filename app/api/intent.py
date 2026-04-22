"""
app/api/intent.py - Intent Agent API endpoint
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from intent_agent.config import build_llm_model

router = APIRouter(prefix="/api/intent", tags=["intent"])


class IntentRequest(BaseModel):
    """Request body for intent extraction"""
    user_query: str
    enable_llm: bool = True


class IntentResponse(BaseModel):
    """Response body with extracted intent"""
    task: str
    entities: list
    attributes: list
    filters: dict
    systems: list
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    output_mode: str
    requires_federation: bool
    priority: str
    confidence_score: float


@router.post("/extract", response_model=IntentResponse)
async def extract_intent(request: IntentRequest):
    """
    Extract structured intent from user query
    
    Usage:
        POST /api/intent/extract
        {
            "user_query": "Show me payroll for March 2026",
            "enable_llm": true
        }
    
    Returns:
        {
            "task": "fetch",
            "entities": ["payroll"],
            "attributes": ["employeeId", "netSalary"],
            "systems": ["ibm", "unisys"],
            "priority": "medium",
            "confidence_score": 0.85
        }
    """
    try:
        from intent_agent import IntentAgent
        
        # Initialize agent
        if request.enable_llm:
            model = build_llm_model()
        else:
            model = None
        
        agent = IntentAgent(model=model)
        
        # Extract intent
        intent = agent.run(request.user_query)
        
        # Return structured response
        return IntentResponse(
            task=intent.task,
            entities=intent.entities,
            attributes=intent.attributes,
            filters=intent.filters.model_dump(),
            systems=intent.systems,
            metric=intent.metric,
            aggregation=intent.aggregation,
            output_mode=intent.output_mode,
            requires_federation=intent.requires_federation,
            priority=intent.priority,
            confidence_score=intent.confidence_score
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Intent extraction failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "intent-agent",
        "version": "1.0.0"
    }


@router.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities and task types"""
    return {
        "tasks": ["fetch", "reconcile", "analyze", "compare", "transform"],
        "entities": ["payroll", "customer", "transaction", "account"],
        "systems": ["ibm", "unisys"],
        "priorities": ["low", "medium", "high"]
    }
