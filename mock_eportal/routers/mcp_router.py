"""
mcp_router.py - MCP (Model Context Protocol) tool discovery endpoints

Enables the Context Resolution Agent and Planner Agent to discover
available tools and their capabilities on the Unisys ePortal.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/mcp", tags=["mcp"])

# ================================================================
# MCP TOOL MANIFEST
# ================================================================

MCP_TOOLS = [
    {
        "name": "get_payroll",
        "description": "Retrieve employee payroll data from Unisys MCP COBOL backend",
        "endpoint": "/api/unisys/payroll",
        "method": "GET",
        "params": [
            {"name": "employeeId", "type": "integer", "required": False, "description": "Filter by employee ID"},
            {"name": "department", "type": "string", "required": False, "description": "Filter by department"}
        ],
        "output_fields": ["employeeId", "employeeName", "department", "netSalary", "grossSalary", "deductions", "payPeriod", "position", "hireDate"],
        "entity": "payroll",
        "schema_endpoint": "/schema/payroll",
        "rate_limit": "100/min",
        "auth_required": False
    },
    {
        "name": "get_customer",
        "description": "Retrieve customer records from Unisys DMSII database",
        "endpoint": "/api/unisys/customer",
        "method": "GET",
        "params": [
            {"name": "customerId", "type": "string", "required": False, "description": "Filter by customer ID"},
            {"name": "status", "type": "string", "required": False, "description": "Filter by status"},
            {"name": "customerType", "type": "string", "required": False, "description": "Filter by type: individual/corporate"}
        ],
        "output_fields": ["customerId", "customerName", "accountId", "email", "phone", "status", "customerType", "registrationDate", "creditLimit"],
        "entity": "customer",
        "schema_endpoint": "/schema/customer",
        "rate_limit": "100/min",
        "auth_required": False
    },
    {
        "name": "get_transaction",
        "description": "Retrieve financial transaction records from Unisys MCP transaction processor",
        "endpoint": "/api/unisys/transaction",
        "method": "GET",
        "params": [
            {"name": "accountId", "type": "string", "required": False, "description": "Filter by account ID"},
            {"name": "transactionType", "type": "string", "required": False, "description": "Filter by type: credit/debit"},
            {"name": "startDate", "type": "string", "required": False, "description": "Start date (YYYY-MM-DD)"},
            {"name": "endDate", "type": "string", "required": False, "description": "End date (YYYY-MM-DD)"}
        ],
        "output_fields": ["transactionId", "accountId", "transactionAmount", "transactionDate", "transactionType", "description", "status", "currency"],
        "entity": "transaction",
        "schema_endpoint": "/schema/transaction",
        "rate_limit": "50/min",
        "auth_required": False
    }
]


@router.get("/tools")
async def get_tools():
    """
    MCP Tool Discovery Endpoint
    
    Returns a manifest of all available tools that the Context Resolution
    Agent and Planner Agent can use to discover and plan Unisys operations.
    """
    return {
        "source": "unisys_eportal",
        "protocol": "mcp",
        "version": "1.0",
        "tools": MCP_TOOLS,
        "tool_count": len(MCP_TOOLS)
    }


@router.get("/tools/{tool_name}")
async def get_tool_details(tool_name: str):
    """
    Get detailed information about a specific MCP tool
    """
    for tool in MCP_TOOLS:
        if tool["name"] == tool_name:
            return tool
    raise HTTPException(
        status_code=404,
        detail=f"Tool not found: {tool_name}"
    )


@router.get("/health")
async def mcp_health():
    """MCP service health check"""
    return {
        "status": "healthy",
        "protocol": "mcp",
        "tools_available": len(MCP_TOOLS),
        "version": "1.0"
    }
