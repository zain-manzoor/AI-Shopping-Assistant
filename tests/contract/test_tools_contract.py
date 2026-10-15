"""Public shopping tool results obey the documented contract."""

from __future__ import annotations

import os
import tempfile

from mcp_server import tools
from tests.support import ShoppingDatabaseTestCase


class ToolContractTests(ShoppingDatabaseTestCase):
    def test_all_catalog_tools_return_real_catalog_facts(self) -> None:
        search = tools.search_products(query="NovaBook")
        self.assertEqual(search["status"], "ok")
        self.assertEqual(search["products"][0]["product_id"], "EL-001")
        self.assertEqual(search["products"][0]["price_pkr"], "PKR 184,900.00")
        self.assertEqual(tools.get_product_details("missing")["status"], "not_found")
        categories = tools.get_product_categories()["categories"]
        self.assertEqual(len(categories), 4)
        self.assertEqual(tools.check_stock("EL-001")["available_quantity"], 8)
        comparison = tools.compare_products(["EL-001", "missing"])
        self.assertEqual(comparison["missing_product_ids"], ["missing"])

    def test_cart_tool_response_and_rejections_are_explicit(self) -> None:
        result = tools.add_to_cart("demo-customer-1", "EL-001", 2)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["cart"]["total_paisa"], 36_980_000)
        rejected = tools.add_to_cart("demo-customer-1", "EL-001", 20)
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(rejected["code"], "quantity_limit")
        self.assertEqual(tools.view_cart("demo-customer-1")["cart"]["items"][0]["quantity"], 2)

    def test_empty_search_and_cart_are_honest(self) -> None:
        self.assertEqual(tools.search_products(query="absent item")["products"], [])
        empty = tools.view_cart("demo-customer-1")
        self.assertEqual(empty["cart"]["total_paisa"], 0)
        self.assertIn("empty", empty["message"].lower())

    def test_invalid_search_comparison_and_removal_return_clear_rejections(self) -> None:
        invalid_range = tools.search_products(min_price_pkr=500, max_price_pkr=10)
        self.assertEqual(invalid_range["status"], "rejected")
        self.assertEqual(tools.compare_products(["EL-001"])["status"], "rejected")
        too_many = tools.compare_products(["EL-001", "EL-002", "EL-003", "EL-004", "EL-005"])
        self.assertEqual(too_many["status"], "rejected")
        removed = tools.remove_from_cart("demo-customer-1", "EL-001")
        self.assertEqual(removed["code"], "not_in_cart")

    def test_database_error_returns_safe_generic_result(self) -> None:
        original_path = os.environ.get("SHOPPING_DB_PATH")
        with tempfile.TemporaryDirectory() as temporary_directory:
            os.environ["SHOPPING_DB_PATH"] = f"{temporary_directory}/missing/shopping.db"
            try:
                result = tools.search_products(query="NovaBook")
            finally:
                if original_path is None:
                    os.environ.pop("SHOPPING_DB_PATH", None)
                else:
                    os.environ["SHOPPING_DB_PATH"] = original_path

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["code"], "storage_error")
        self.assertNotIn("missing", result["message"])
