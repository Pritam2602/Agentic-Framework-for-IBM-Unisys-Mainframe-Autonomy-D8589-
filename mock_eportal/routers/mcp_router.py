"""
mcp_router.py - MCP (Model Context Protocol) tool discovery endpoints

Enables the Context Resolution Agent and Planner Agent to discover
available tools and their capabilities on the Unisys ePortal.
Aligned with AWS CardDemo entity structure.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/mcp", tags=["mcp"])

# ================================================================
# MCP TOOL MANIFEST (CardDemo Aligned)
# ================================================================

MCP_TOOLS = [
    {
        "name": "get_customer",
        "description": "Retrieve customer records from Unisys DMSII database. Maps to AWS CardDemo Customer entity.",
        "endpoint": "/api/unisys/customer",
        "method": "GET",
        "params": [
            {"name": "customerId", "type": "string", "required": False, "description": "Filter by customer ID"},
            {"name": "status", "type": "string", "required": False, "description": "Filter by status"},
            {"name": "customerType", "type": "string", "required": False, "description": "Filter by type: individual/corporate"}
        ],
        "output_fields": ["customerId", "customerName", "email", "phone", "status", "customerType", "customerOpenDate", "address", "kyc_status"],
        "entity": "customer",
        "carddemo_entity": "CUSTOMER",
        "schema_endpoint": "/schema/customer",
        "rate_limit": "100/min",
        "auth_required": False
    },
    {
        "name": "get_account",
        "description": "Retrieve account records from Unisys VSAM database. Maps to AWS CardDemo Account entity. Enforces 1:1 relationship with Customer.",
        "endpoint": "/api/unisys/account",
        "method": "GET",
        "params": [
            {"name": "accountNumber", "type": "string", "required": False, "description": "Filter by account number"},
            {"name": "customerId", "type": "string", "required": False, "description": "Filter by customer ID"},
            {"name": "accountStatus", "type": "string", "required": False, "description": "Filter by status: ACTIVE/INACTIVE/SUSPENDED/CLOSED"},
            {"name": "accountType", "type": "string", "required": False, "description": "Filter by type: CREDIT/SAVINGS/CHECKING"}
        ],
        "output_fields": ["accountNumber", "customerId", "accountType", "accountBalance", "currency", "accountOpenDate", "accountStatus", "interestRate", "creditLimit"],
        "entity": "account",
        "carddemo_entity": "ACCOUNT",
        "schema_endpoint": "/schema/account",
        "relationship": "1:1 to Customer (CardDemo constraint)",
        "rate_limit": "100/min",
        "auth_required": False
    },
    {
        "name": "get_card",
        "description": "Retrieve card records from Unisys VSAM database. Maps to AWS CardDemo Card entity. Enforces 1:1 relationship with Account.",
        "endpoint": "/api/unisys/card",
        "method": "GET",
        "params": [
            {"name": "cardNumber", "type": "string", "required": False, "description": "Filter by card number"},
            {"name": "customerId", "type": "string", "required": False, "description": "Filter by customer ID"},
            {"name": "accountNumber", "type": "string", "required": False, "description": "Filter by account number"},
            {"name": "cardStatus", "type": "string", "required": False, "description": "Filter by status: ACTIVE/EXPIRED/BLOCKED/CANCELLED"},
            {"name": "cardType", "type": "string", "required": False, "description": "Filter by type: CREDIT/DEBIT"}
        ],
        "output_fields": ["cardNumber", "customerId", "accountNumber", "cardStatus", "cardType", "expiryDate", "cardholderName", "issuedDate", "cardLimit"],
        "entity": "card",
        "carddemo_entity": "CARD",
        "schema_endpoint": "/schema/card",
        "relationship": "1:1 to Account and Customer (CardDemo constraint)",
        "rate_limit": "100/min",
        "auth_required": False
    },
    {
        "name": "get_transaction",
        "description": "Retrieve financial transaction records from Unisys MCP transaction processor. Maps to AWS CardDemo Transaction entity.",
        "endpoint": "/api/unisys/transaction",
        "method": "GET",
        "params": [
            {"name": "accountNumber", "type": "string", "required": False, "description": "Filter by account number"},
            {"name": "transactionType", "type": "string", "required": False, "description": "Filter by type: CREDIT/DEBIT/TRANSFER/PAYMENT"},
            {"name": "startDate", "type": "string", "required": False, "description": "Start date (YYYY-MM-DD)"},
            {"name": "endDate", "type": "string", "required": False, "description": "End date (YYYY-MM-DD)"},
            {"name": "transactionStatus", "type": "string", "required": False, "description": "Filter by status: POSTED/PENDING/DECLINED"}
        ],
        "output_fields": ["transactionId", "accountNumber", "transactionAmount", "transactionDate", "transactionType", "transactionDescription", "transactionStatus", "currency", "referenceNumber"],
        "entity": "transaction",
        "carddemo_entity": "TRANSACTION",
        "schema_endpoint": "/schema/transaction",
        "relationship": "Many to Account (CardDemo constraint)",
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
    
    All tools are aligned with AWS CardDemo entity structure.
    """
    return {
        "source": "unisys_eportal",
        "protocol": "mcp",
        "version": "1.0",
        "federation_standard": "AWS CardDemo",
        "relationship_model": "1:1:1 between Customer, Account, Card; 1:* to Transaction",
        "tools": MCP_TOOLS,
        "tool_count": len(MCP_TOOLS),
        "federation_metadata_endpoint": "/api/unisys/federation-metadata"
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
    """MCP service health check endpoint"""
    return {
        "status": "healthy",
        "service": "unisys_eportal_mcp",
        "version": "1.0.0",
        "federation_standard": "AWS CardDemo",
        "tools_available": len(MCP_TOOLS),
        "entities_supported": ["customer", "account", "card", "transaction"]
    }
