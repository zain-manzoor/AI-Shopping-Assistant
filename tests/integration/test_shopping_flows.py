"""Deterministic end-to-end shopping flows through the MCP handler functions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from agents.shopping_assistant.customer_context import (
    customer_id_for_session,
    inject_customer_identity,
)
from mcp_server import tools
from tests.support import ShoppingDatabaseTestCase


class ShoppingFlowTests(ShoppingDatabaseTestCase):
    def test_cart_and_session_identity_survive_a_new_python_process(self) -> None:
        session_id = "host-session-resume-after-restart"
        customer_id = customer_id_for_session(session_id)
        tools.add_to_cart(customer_id, "EL-001", 1)
        child_environment = {
            key: os.environ[key]
            for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
            if os.environ.get(key)
        }
        child_environment["SHOPPING_DB_PATH"] = str(self.database_file)
        project_root = Path(__file__).resolve().parents[2]
        script = (
            "import json; from mcp_server.tools import view_cart; "
            f"print(json.dumps(view_cart({customer_id!r})))"
        )

        child = subprocess.run(
            [sys.executable, "-c", script],
            cwd=project_root,
            env=child_environment,
            capture_output=True,
            check=True,
            text=True,
        )
        restored = json.loads(child.stdout)
        self.assertEqual(restored["cart"]["items"][0]["product_id"], "EL-001")
        self.assertEqual(restored["cart"]["total_paisa"], 18_490_000)
        self.assertEqual(customer_id_for_session(session_id), customer_id)

    def test_search_compare_recommendation_candidate_and_cart_flow(self) -> None:
        results = tools.search_products(category="electronics", max_price_pkr=200000)
        candidates = [item for item in results["products"] if item["available_quantity"] > 0]
        self.assertTrue(candidates)
        compare = tools.compare_products([candidates[0]["product_id"], "EL-002"])
        self.assertEqual(compare["status"], "ok")
        self.assertEqual(len(compare["products"]), 2)
        customer_id = "demo-customer-1"
        added = tools.add_to_cart(customer_id, candidates[0]["product_id"], 1)
        self.assertEqual(added["status"], "ok")
        cart = tools.view_cart(customer_id)["cart"]
        self.assertEqual(cart["items"][0]["product_id"], candidates[0]["product_id"])
        self.assertEqual(cart["total_paisa"], cart["items"][0]["subtotal_paisa"])

    def test_session_identity_is_stable_and_isolated_without_using_message_text(self) -> None:
        first = customer_id_for_session("host-session-001")
        self.assertEqual(first, customer_id_for_session("host-session-001"))
        second = customer_id_for_session("host-session-002")
        self.assertNotEqual(first, second)
        tools.add_to_cart(first, "EL-001", 1)
        self.assertEqual(tools.view_cart(second)["cart"]["items"], [])
        self.assertEqual(tools.view_cart(first)["cart"]["items"][0]["product_id"], "EL-001")

    def test_application_identity_overwrites_model_supplied_customer_id(self) -> None:
        args: dict[str, object] = {"customer_id": "another-customer", "product_id": "EL-001"}
        trusted = inject_customer_identity(args, "host-session-003")
        self.assertEqual(args["customer_id"], trusted)
        self.assertNotEqual(args["customer_id"], "another-customer")
