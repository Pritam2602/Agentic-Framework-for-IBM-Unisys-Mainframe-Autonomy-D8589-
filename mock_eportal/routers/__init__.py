"""
routers/__init__.py
"""

from .api_router import router as api_router
from .schema_router import router as schema_router
from .mcp_router import router as mcp_router

__all__ = ["api_router", "schema_router", "mcp_router"]
