"""
app/api/context.py - Context Resolution Agent API endpoint
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from pathlib import Path

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
    from context_resolution_agent.ibm_resolver import COBOL_OUTPUT_DIR, JCL_OUTPUT_DIR
    from context_resolution_agent.unisys_resolver import UnisysContextResolver
    from app.repository.catalog_repository import DB_PATH

    unisys_resolver = UnisysContextResolver()
    cobol_programs = len(list(COBOL_OUTPUT_DIR.glob("*.json"))) if COBOL_OUTPUT_DIR.exists() else 0
    jcl_jobs = len(list(JCL_OUTPUT_DIR.glob("*.json"))) if JCL_OUTPUT_DIR.exists() else 0
    zowe_catalog_available = Path(DB_PATH).exists()

    return {
        "status": "healthy",
        "service": "context-resolution-agent",
        "ibm": {
            "cobol_programs": cobol_programs,
            "jcl_jobs": jcl_jobs,
            "zowe_catalog": zowe_catalog_available,
        },
        "unisys": {
            "eportal_available": unisys_resolver.is_eportal_available()
        }
    }
