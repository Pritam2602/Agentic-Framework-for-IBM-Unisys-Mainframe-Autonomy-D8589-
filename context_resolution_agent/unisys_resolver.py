"""
unisys_resolver.py - Unisys ePortal Context Resolver

Resolves WHERE data exists on the Unisys side by consulting:
1. MCP tools endpoint (/mcp/tools) → tool discovery
2. Schema endpoints (/schema/*) → field information

DOES NOT execute data retrieval. Only resolves metadata.
"""

import logging
from typing import Optional

import httpx

from .schemas import UnisysContext

logger = logging.getLogger(__name__)

EPORTAL_BASE_URL = "http://localhost:8001"


class UnisysContextResolver:
    """
    Resolves Unisys ePortal context for a given entity.

    Uses MCP tool discovery to find available APIs and their schemas.
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or EPORTAL_BASE_URL

    def resolve(self, entity: str, attributes: list = None) -> Optional[UnisysContext]:
        """
        Resolve Unisys context for an entity.

        Args:
            entity: Entity name (e.g., "payroll", "customer", "transaction")
            attributes: Optional list of specific attributes needed

        Returns:
            UnisysContext with resolved metadata, or None if not found
        """
        logger.info(f"[Unisys Resolver] Resolving context for entity: {entity}")

        # Step 1: Discover MCP tools
        tool = self._discover_tool(entity)
        if not tool:
            logger.warning(f"[Unisys Resolver] No MCP tool found for entity: {entity}")
            return None

        # Step 2: Get schema information
        schema_info = self._get_schema(entity)

        # Build context
        fields = tool.get("output_fields", [])
        if schema_info:
            # Merge schema fields if available
            schema_fields = [
                f["name"] for f in schema_info.get("fields", [])
            ]
            # Use schema fields as they're more authoritative
            if schema_fields:
                fields = schema_fields

        context = UnisysContext(
            api=tool.get("endpoint"),
            fields=fields,
            tool_name=tool.get("name"),
            params=tool.get("params", []),
            schema_endpoint=tool.get("schema_endpoint"),
            entity=entity,
        )

        logger.info(
            f"[Unisys Resolver] Resolved: api={context.api}, "
            f"fields={len(context.fields)}, tool={context.tool_name}"
        )

        return context

    def _discover_tool(self, entity: str) -> Optional[dict]:
        """
        Call /mcp/tools to discover the tool for an entity.
        Falls back to convention-based resolution if ePortal is unavailable.
        """
        try:
            response = httpx.get(
                f"{self.base_url}/mcp/tools",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])

                # Find tool matching entity
                for tool in tools:
                    if tool.get("entity", "").lower() == entity.lower():
                        return tool
                    # Also check tool name
                    if entity.lower() in tool.get("name", "").lower():
                        return tool

                logger.info(f"[Unisys Resolver] No tool matches entity '{entity}' in MCP manifest")
                return None

        except httpx.ConnectError:
            logger.warning("[Unisys Resolver] ePortal not reachable, using fallback resolution")
            return self._fallback_tool_resolution(entity)
        except Exception as e:
            logger.error(f"[Unisys Resolver] MCP discovery failed: {e}")
            return self._fallback_tool_resolution(entity)

    def _get_schema(self, entity: str) -> Optional[dict]:
        """
        Call /schema/{entity} to get field information.
        Returns None if ePortal is unavailable.
        """
        try:
            response = httpx.get(
                f"{self.base_url}/schema/{entity}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"[Unisys Resolver] Schema fetch failed for {entity}: {e}")

        return None

    @staticmethod
    def _fallback_tool_resolution(entity: str) -> Optional[dict]:
        """
        Convention-based fallback when ePortal is not running.
        Maps entities to expected API endpoints.
        """
        FALLBACK_MAP = {
            "payroll": {
                "name": "get_payroll",
                "endpoint": "/api/unisys/payroll",
                "params": [
                    {"name": "employeeId", "type": "integer", "required": False},
                    {"name": "department", "type": "string", "required": False}
                ],
                "output_fields": ["employeeId", "employeeName", "department", "netSalary", "grossSalary"],
                "entity": "payroll",
                "schema_endpoint": "/schema/payroll",
            },
            "customer": {
                "name": "get_customer",
                "endpoint": "/api/unisys/customer",
                "params": [
                    {"name": "customerId", "type": "string", "required": False}
                ],
                "output_fields": ["customerId", "customerName", "accountId", "email", "status"],
                "entity": "customer",
                "schema_endpoint": "/schema/customer",
            },
            "transaction": {
                "name": "get_transaction",
                "endpoint": "/api/unisys/transaction",
                "params": [
                    {"name": "accountId", "type": "string", "required": False},
                    {"name": "startDate", "type": "string", "required": False},
                    {"name": "endDate", "type": "string", "required": False}
                ],
                "output_fields": ["transactionId", "accountId", "transactionAmount", "transactionDate"],
                "entity": "transaction",
                "schema_endpoint": "/schema/transaction",
            },
        }

        return FALLBACK_MAP.get(entity.lower())

    def is_eportal_available(self) -> bool:
        """Check if ePortal is reachable"""
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
