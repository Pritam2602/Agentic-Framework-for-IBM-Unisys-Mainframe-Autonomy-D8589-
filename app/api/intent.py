"""
app/api/intent.py - Intent Agent API endpoint
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

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
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                model = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0
                )
            except Exception as e:
                print(f"LLM failed, using fallback: {e}")
                model = None
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
