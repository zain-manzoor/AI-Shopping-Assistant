"""Verify trusted identity injection and MCP environment filtering."""

from __future__ import annotations

import os
from types import SimpleNamespace

from agents.shopping_assistant.agent import _mcp_environment, before_tool_callback
from tests.support import ShoppingDatabaseTestCase


class CustomerIdentityTests(ShoppingDatabaseTestCase):
    def test_cart_callback_overwrites_model_supplied_customer_id(self) -> None:
        args: dict[str, object] = {"customer_id": "forged-customer", "product_id": "EL-001"}
        context = SimpleNamespace(session=SimpleNamespace(id="trusted-session-001"))

        result = before_tool_callback(SimpleNamespace(name="add_to_cart"), args, context)

        self.assertIsNone(result)
        self.assertNotEqual(args["customer_id"], "forged-customer")
        self.assertTrue(str(args["customer_id"]).startswith("demo-"))

    def test_mcp_child_environment_omits_gemini_key(self) -> None:
        original_key = os.environ.get("GOOGLE_API_KEY")
        original_db = os.environ.get("SHOPPING_DB_PATH")
        os.environ["GOOGLE_API_KEY"] = "sentinel-secret"
        os.environ["SHOPPING_DB_PATH"] = str(self.database_file)
        try:
            child_environment = _mcp_environment()
        finally:
            if original_key is None:
                os.environ.pop("GOOGLE_API_KEY", None)
            else:
                os.environ["GOOGLE_API_KEY"] = original_key
            if original_db is None:
                os.environ.pop("SHOPPING_DB_PATH", None)
            else:
                os.environ["SHOPPING_DB_PATH"] = original_db

        self.assertNotIn("GOOGLE_API_KEY", child_environment)
        self.assertEqual(child_environment["SHOPPING_DB_PATH"], str(self.database_file))
