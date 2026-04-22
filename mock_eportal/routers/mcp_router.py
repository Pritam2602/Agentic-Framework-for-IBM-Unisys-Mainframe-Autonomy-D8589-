"""MCP tool discovery for Unisys ePortal shopping data."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/mcp", tags=["mcp"])

MCP_TOOLS = [
    {
        "name": "get_shopping_data",
        "endpoint": "/api/unisys/shopping",
        "method": "GET",
        "params": ["customerId", "date"],
        "output": ["merchant", "amount", "category"],
        "maps_to": "IBM transactions",
        "entity": "shopping",
        "schema_endpoint": "/schema/shopping",
    }
]


@router.get("/tools")
async def get_tools():
    return {
        "source": "unisys",
        "protocol": "mcp",
        "version": "1.0",
        "tools": MCP_TOOLS,
        "tool_count": len(MCP_TOOLS),
    }


@router.get("/tools/{tool_name}")
async def get_tool_details(tool_name: str):
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")


@router.get("/health")
async def mcp_health():
    return {
        "status": "healthy",
        "service": "unisys_eportal_mcp",
        "tools_available": len(MCP_TOOLS),
        "entities_supported": ["shopping"],
    }
