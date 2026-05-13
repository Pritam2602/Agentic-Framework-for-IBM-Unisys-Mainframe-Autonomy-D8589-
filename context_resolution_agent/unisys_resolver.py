"""
unisys_resolver.py - Unisys ePortal Context Resolver (MCP Client)

Resolves WHERE data exists on the Unisys side by consulting the
ePortal MCP server via SSE transport:
  1. list_tools()  → tool discovery
  2. read_resource() → schema / metadata

DOES NOT execute data retrieval. Only resolves metadata.
"""

import asyncio
import json
import logging
from contextlib import AsyncExitStack
from typing import Optional

from .schemas import UnisysContext

logger = logging.getLogger(__name__)

EPORTAL_MCP_URL = "http://localhost:8001/sse"


class UnisysContextResolver:
    """
    Resolves Unisys ePortal context for a given entity.

    Connects to the ePortal MCP server over SSE to discover tools and resources.
    Falls back to convention-based resolution if the MCP server is unreachable.
    """

    def __init__(self, base_url: str = None):
        self.mcp_url = base_url or EPORTAL_MCP_URL
        # Keep the base URL (without /sse) for legacy health checks
        self.base_url = self.mcp_url.replace("/sse", "")

    def resolve(self, entity: str, attributes: list = None) -> Optional[UnisysContext]:
        """
        Resolve Unisys context for an entity.

        Args:
            entity: Entity name (e.g., "shopping")
            attributes: Optional list of specific attributes needed

        Returns:
            UnisysContext with resolved metadata, or None if not found
        """
        logger.info(f"[Unisys Resolver] Resolving context for entity: {entity}")

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.resolve_async(entity, attributes))
        raise RuntimeError(
            "UnisysContextResolver.resolve() cannot be used inside a running event "
            "loop. Use 'await resolve_async(...)' instead."
        )

    async def resolve_async(
        self, entity: str, attributes: list = None
    ) -> Optional[UnisysContext]:
        """
        Resolve Unisys context for an entity from async code.

        Args:
            entity: Entity name (e.g., "shopping")
            attributes: Optional list of specific attributes needed

        Returns:
            UnisysContext with resolved metadata, or None if not found
        """
        # Try MCP-based discovery first, fall back to convention
        try:
            return await self._resolve_via_mcp(entity)
        except Exception as e:
            logger.warning(f"[Unisys Resolver] MCP discovery failed: {e}, using fallback")
            return self._resolve_fallback(entity)

    async def _resolve_via_mcp(self, entity: str) -> Optional[UnisysContext]:
        """Connect to the MCP server over SSE and discover tools."""
        try:
            from mcp import ClientSession
            from mcp.client.sse import sse_client
        except ImportError:
            logger.warning("[Unisys Resolver] mcp SDK not installed, using fallback")
            return self._resolve_fallback(entity)

        try:
            async with AsyncExitStack() as stack:
                read_stream, write_stream = await stack.enter_async_context(
                    sse_client(self.mcp_url)
                )
                session = await stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()

                # Discover matching tool
                tools_result = await session.list_tools()
                tool = self._find_matching_tool(tools_result.tools, entity)

                if not tool:
                    logger.warning(
                        f"[Unisys Resolver] No MCP tool found for entity: {entity}"
                    )
                    return self._resolve_fallback(entity)

                # Try to read schema resource
                schema_fields = []
                try:
                    schema_result = await session.read_resource(f"schema://{entity}")
                    if schema_result and schema_result.contents:
                        schema_data = json.loads(schema_result.contents[0].text)
                        schema_fields = schema_data.get("fields", [])
                except Exception as e:
                    logger.debug(f"[Unisys Resolver] Schema resource read failed: {e}")

                # Build fields list from tool or schema
                fields = schema_fields or [
                    prop for prop in (tool.inputSchema or {}).get("properties", {}).keys()
                ]

                # Build params from tool input schema
                params = self._extract_params_from_tool(tool)

                context = UnisysContext(
                    api=f"/mcp/tool/{tool.name}",
                    fields=fields,
                    tool_name=tool.name,
                    params=params,
                    schema_endpoint=f"schema://{entity}",
                    entity=entity,
                )

                logger.info(
                    f"[Unisys Resolver] Resolved via MCP: tool={context.tool_name}, "
                    f"fields={len(context.fields)}"
                )
                return context

        except Exception as e:
            logger.warning(
                f"[Unisys Resolver] MCP server not reachable ({e}), using fallback"
            )
            return self._resolve_fallback(entity)

    @staticmethod
    def _find_matching_tool(tools, entity: str):
        """Find a tool that matches the requested entity."""
        for tool in tools:
            # Match by name containing entity
            if entity.lower() in tool.name.lower():
                return tool
            # Match by description containing entity
            if tool.description and entity.lower() in tool.description.lower():
                return tool
        return None

    @staticmethod
    def _extract_params_from_tool(tool) -> list:
        """Extract parameter info from an MCP tool's input schema."""
        params = []
        schema = tool.inputSchema or {}
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        for name, prop in properties.items():
            params.append({
                "name": name,
                "type": prop.get("type", "string"),
                "required": name in required,
            })
        return params

    def _resolve_fallback(self, entity: str) -> Optional[UnisysContext]:
        """
        Convention-based fallback when ePortal MCP server is not running.
        Maps entities to expected API endpoints.
        """
        FALLBACK_MAP = {
            "shopping": {
                "name": "get_shopping_data",
                "endpoint": "/api/unisys/shopping",
                "params": [
                    {"name": "customerId", "type": "integer", "required": False},
                    {"name": "date", "type": "string", "required": False}
                ],
                "output_fields": [
                    "customerId", "merchant", "amount", "date", "category",
                    "loyaltyPoints", "browsingSessionMinutes", "cartStatus",
                    "merchantCategory"
                ],
                "entity": "shopping",
                "maps_to": "IBM transactions",
                "schema_endpoint": "schema://shopping",
            },
            "inventory": {
                "name": "get_inventory_data",
                "endpoint": "/api/inventory",
                "params": [
                    {"name": "merchant", "type": "string", "required": False},
                    {"name": "category", "type": "string", "required": False},
                    {"name": "sku", "type": "string", "required": False},
                    {"name": "availabilityStatus", "type": "string", "required": False},
                ],
                "output_fields": [
                    "entity", "sku", "productId", "productName", "merchant",
                    "category", "merchantCategory", "stockQuantity", "reorderLevel",
                    "availabilityStatus", "warehouseLocation", "lastUpdated",
                ],
                "entity": "inventory",
                "maps_to": "Unisys shopping",
                "schema_endpoint": "schema://inventory",
            },
        }

        fallback = FALLBACK_MAP.get(entity.lower())
        if not fallback:
            return None

        context = UnisysContext(
            api=fallback["endpoint"],
            fields=fallback["output_fields"],
            tool_name=fallback["name"],
            params=fallback["params"],
            schema_endpoint=fallback.get("schema_endpoint"),
            entity=entity,
        )

        logger.info(
            f"[Unisys Resolver] Resolved via fallback: api={context.api}, "
            f"fields={len(context.fields)}, tool={context.tool_name}"
        )
        return context

    def is_eportal_available(self) -> bool:
        """Check if the ePortal MCP server is reachable."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.is_eportal_available_async())
        raise RuntimeError(
            "UnisysContextResolver.is_eportal_available() cannot be used inside a "
            "running event loop. Use 'await is_eportal_available_async()' instead."
        )

    async def is_eportal_available_async(self) -> bool:
        """Check if the ePortal MCP server is reachable from async code."""
        try:
            import httpx

            # Quick HTTP check on the SSE endpoint
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(self.base_url)
            return response.status_code in (200, 405)
        except Exception:
            pass

        # Try MCP handshake
        try:
            async def _check():
                from mcp import ClientSession
                from mcp.client.sse import sse_client

                async with AsyncExitStack() as stack:
                    read_stream, write_stream = await stack.enter_async_context(
                        sse_client(self.mcp_url)
                    )
                    session = await stack.enter_async_context(
                        ClientSession(read_stream, write_stream)
                    )
                    await session.initialize()
                    return True

            return await _check()
        except Exception:
            return False
