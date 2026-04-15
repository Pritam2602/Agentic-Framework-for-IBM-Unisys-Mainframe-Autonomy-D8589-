"""
app/api/context.py - Context Resolution Agent API endpoint
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api/context", tags=["context"])


class ContextRequest(BaseModel):
    """Request body for context resolution"""
    task: str
    entities: List[str]
    attributes: List[str] = []
    systems: List[str] = ["ibm", "unisys"]
    filters: Optional[Dict[str, Any]] = None


class ContextResponse(BaseModel):
    """Response with resolved context"""
    ibm: Optional[Dict[str, Any]] = None
    unisys: Optional[Dict[str, Any]] = None
    entities_resolved: List[str]
    systems_checked: List[str]
    resolution_confidence: float
    warnings: List[str]


@router.post("/resolve", response_model=ContextResponse)
async def resolve_context(request: ContextRequest):
    """
    Resolve data context from intent JSON.
    
    Determines WHERE the requested data exists across IBM and Unisys.
    Does NOT execute anything — only resolves metadata.
    
    Usage:
        POST /api/context/resolve
        {
            "task": "fetch",
            "entities": ["payroll"],
            "systems": ["ibm", "unisys"]
        }
    """
    try:
        from context_resolution_agent import ContextResolutionAgent

        agent = ContextResolutionAgent()
        context = agent.resolve(request.model_dump())

        return ContextResponse(
            ibm=context.ibm.model_dump() if context.ibm else None,
            unisys=context.unisys.model_dump() if context.unisys else None,
            entities_resolved=context.entities_resolved,
            systems_checked=context.systems_checked,
            resolution_confidence=context.resolution_confidence,
            warnings=context.warnings,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Context resolution failed: {str(e)}"
        )


@router.get("/health")
async def context_health():
    """Health check for context resolution service"""
    from context_resolution_agent import ContextResolutionAgent
    from ibm_parsers import CobolParser, JclParser, ZoweCatalogResolver

    cobol = CobolParser()
    jcl = JclParser()
    zowe = ZoweCatalogResolver()

    return {
        "status": "healthy",
        "service": "context-resolution-agent",
        "ibm": {
            "cobol_programs": len(cobol.parse_catalog()),
            "jcl_jobs": len(jcl.parse_catalog()),
            "zowe_catalog": zowe.is_available(),
        },
        "unisys": {
            "eportal_available": ContextResolutionAgent().unisys_resolver.is_eportal_available()
        }
    }
