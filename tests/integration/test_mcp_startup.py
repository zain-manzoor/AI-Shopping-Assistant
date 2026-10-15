"""Exercise the real MCP server process over its stdio transport."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

from agents.shopping_assistant import root_agent
from tests.support import ShoppingDatabaseTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TOOLS = {
    "search_products",
    "get_product_details",
    "compare_products",
    "get_product_categories",
    "check_stock",
    "add_to_cart",
    "remove_from_cart",
    "update_cart_quantity",
    "view_cart",
}


class McpStartupTests(ShoppingDatabaseTestCase):
    def test_adk_toolset_discovers_the_server_tools(self) -> None:
        async def discover_tools() -> None:
            toolset = next(tool for tool in root_agent.tools if isinstance(tool, McpToolset))
            try:
                discovered = await toolset.get_tools()
                self.assertEqual({tool.name for tool in discovered}, EXPECTED_TOOLS)
            finally:
                await toolset.close()

        asyncio.run(discover_tools())

    def test_stdio_handshake_lists_tools_and_searches_seeded_catalog(self) -> None:
        async def exercise_server() -> None:
            child_env = {
                key: os.environ[key]
                for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
                if os.environ.get(key)
            }
            child_env["SHOPPING_DB_PATH"] = str(self.database_file)
            child_env.pop("GOOGLE_API_KEY", None)
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "mcp_server"],
                cwd=str(PROJECT_ROOT),
                env=child_env,
            )
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    self.assertEqual({tool.name for tool in tools_result.tools}, EXPECTED_TOOLS)

                    search_result = await session.call_tool(
                        "search_products", {"query": "NovaBook"}
                    )
                    self.assertFalse(search_result.is_error)
                    payload = json.loads(search_result.content[0].text)
                    self.assertEqual(payload["products"][0]["product_id"], "EL-001")

        asyncio.run(exercise_server())
