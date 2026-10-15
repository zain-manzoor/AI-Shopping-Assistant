"""Single ADK shopping assistant backed by the first-party MCP tools."""

from __future__ import annotations

import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

from .conversation_state import recommendation_memory, remember_product
from .conversation_state import remember_preferences as save_preferences
from .customer_context import inject_customer_identity

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

CART_TOOLS = {"add_to_cart", "remove_from_cart", "update_cart_quantity", "view_cart"}
ALL_TOOLS = [
    "search_products",
    "get_product_details",
    "compare_products",
    "get_product_categories",
    "check_stock",
    "add_to_cart",
    "remove_from_cart",
    "update_cart_quantity",
    "view_cart",
]
INSTRUCTIONS = """You are a friendly, concise shopping assistant for a fictional local catalog.
Use catalog and cart tools for product facts, prices, stock, specifications, and cart totals.
Never invent a product or claim an action succeeded unless a tool confirms it. Search can show
matching out-of-stock products only when clearly labelled unavailable. Never recommend unavailable
items. Treat a customer's stated budget as a strict maximum unless they explicitly ask for higher-
priced alternatives. Keep preferences, rejected products, and customer-declared ownership only in
this conversation: call remember_preferences when criteria are shared, remember_rejected_product
or remember_owned_product when the customer says so, and get_recommendation_memory before
recommending. Also view the current cart and exclude its products. Do not re-suggest products that
are rejected, owned, or in the current cart unless specifically asked. Ask one concise clarification
question at a time. Decline checkout,
payment, purchase, and unrelated-topic requests; redirect to supported shopping actions. Never
ask for or store real personal or payment data. The application supplies the customer identity.
"""


def before_tool_callback(tool: Any, args: dict[str, Any], tool_context: Any) -> dict | None:
    """Overwrite cart identity from the ADK-created session before MCP dispatch."""
    if getattr(tool, "name", "") not in CART_TOOLS:
        return None
    session = getattr(tool_context, "session", None)
    session_id = getattr(session, "id", None)
    if not session_id:
        logger.warning("Cart tool blocked because application session identity is unavailable")
        return {
            "status": "error",
            "code": "customer_context_missing",
            "message": "I cannot verify this shopping session right now.",
        }
    try:
        inject_customer_identity(args, session_id)
    except (OSError, sqlite3.Error, ValueError) as error:
        logger.error("Could not prepare local customer context: %s", type(error).__name__)
        return {
            "status": "error",
            "code": "customer_context_unavailable",
            "message": "I could not verify this shopping session right now.",
        }
    return None


def on_model_error_callback(
    *, callback_context: Any, llm_request: LlmRequest, error: Exception
) -> LlmResponse:
    """Return a truthful fallback when Gemini is unavailable."""
    del callback_context, llm_request
    logger.error("Gemini request failed: %s", type(error).__name__)
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text="I couldn't complete that request just now. Please try again.")],
        )
    )


def on_tool_error_callback(
    *, tool: Any, args: dict[str, Any], tool_context: Any, error: Exception
) -> dict[str, Any]:
    """Convert tool failures to a safe result without exposing exception details."""
    del args, tool_context
    logger.error("MCP tool %s failed: %s", getattr(tool, "name", "unknown"), type(error).__name__)
    return {
        "status": "error",
        "code": "tool_unavailable",
        "message": "I couldn't complete that shopping action. Please try again.",
    }


def remember_preferences(preferences: dict[str, str], tool_context: ToolContext) -> dict[str, str]:
    """Remember customer-provided recommendation criteria in this conversation only."""
    return save_preferences(tool_context.state, preferences)


def remember_rejected_product(product_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Record a product the customer rejected for the current conversation."""
    rejected = remember_product(tool_context.state, "rejected_product_ids", product_id)
    return {"status": "ok", "rejected_product_ids": rejected}


def remember_owned_product(product_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Record a product the customer says they already own in this conversation."""
    owned = remember_product(tool_context.state, "owned_product_ids", product_id)
    return {"status": "ok", "owned_product_ids": owned}


def get_recommendation_memory(tool_context: ToolContext) -> dict[str, Any]:
    """Return only the current conversation's recommendation context."""
    return recommendation_memory(tool_context.state)


def _mcp_environment() -> dict[str, str]:
    """Pass only operating-system essentials and the local database path to MCP."""
    allowed = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
    environment = {key: os.environ[key] for key in allowed if os.environ.get(key)}
    configured_db = os.getenv("SHOPPING_DB_PATH", "shopping.db")
    environment["SHOPPING_DB_PATH"] = str(
        Path(configured_db).expanduser()
        if Path(configured_db).expanduser().is_absolute()
        else PROJECT_ROOT / configured_db
    )
    return environment


def build_mcp_toolset() -> McpToolset:
    """Create ADK's documented MCP client over a local Python stdio process."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "mcp_server"],
                env=_mcp_environment(),
                cwd=str(PROJECT_ROOT),
            ),
            timeout=20,
        ),
        tool_filter=ALL_TOOLS,
    )


if not os.getenv("GOOGLE_API_KEY"):
    logger.warning(
        "GOOGLE_API_KEY is not set; add it to the project .env before sending Gemini requests"
    )

root_agent = LlmAgent(
    name="shopping_assistant",
    model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    description=(
        "Search, compare, and recommend fictional catalog products and manage a simulated cart."
    ),
    instruction=INSTRUCTIONS,
    tools=[
        build_mcp_toolset(),
        remember_preferences,
        remember_rejected_product,
        remember_owned_product,
        get_recommendation_memory,
    ],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)
