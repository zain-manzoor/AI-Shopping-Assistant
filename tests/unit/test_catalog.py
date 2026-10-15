"""Catalog query filtering and truthful missing/empty result behavior."""

from __future__ import annotations

from shopping_data.catalog import (
    CatalogInputError,
    compare_products,
    get_product_details,
    search_products,
)
from tests.support import ShoppingDatabaseTestCase


class CatalogTests(ShoppingDatabaseTestCase):
    def test_searches_name_category_and_inclusive_price_range(self) -> None:
        rows = search_products(
            self.connection,
            query="novabook",
            category="electronics",
            min_price_pkr=184900,
            max_price_pkr=184900,
        )
        self.assertEqual([row["product_id"] for row in rows], ["EL-001"])
        self.assertEqual(rows[0]["price_pkr"], "PKR 184,900.00")

    def test_features_match_case_insensitive_catalog_phrases(self) -> None:
        rows = search_products(self.connection, features="1440P")
        self.assertEqual([row["product_id"] for row in rows], ["EL-006"])

    def test_zero_results_are_an_empty_list(self) -> None:
        self.assertEqual(search_products(self.connection, query="not a real product"), [])

    def test_minimum_above_maximum_is_rejected(self) -> None:
        with self.assertRaises(CatalogInputError):
            search_products(self.connection, min_price_pkr=100, max_price_pkr=99)

    def test_only_literal_search_filters_are_applied(self) -> None:
        self.assertEqual(search_products(self.connection, query="notebook"), [])

    def test_missing_details_and_comparison_products_are_not_invented(self) -> None:
        self.assertIsNone(get_product_details(self.connection, "missing"))
        result = compare_products(self.connection, ["EL-001", "does-not-exist"])
        self.assertEqual([item["product_id"] for item in result["products"]], ["EL-001"])
        self.assertEqual(result["missing_product_ids"], ["does-not-exist"])

    def test_comparison_count_is_two_to_four_distinct_products(self) -> None:
        for ids in (
            ["EL-001"],
            ["EL-001", "EL-001"],
            ["EL-001", "EL-002", "EL-003", "EL-004", "EL-005"],
        ):
            with self.subTest(ids=ids), self.assertRaises(CatalogInputError):
                compare_products(self.connection, list(ids))

    def test_feature_search_escapes_sql_like_wildcards(self) -> None:
        self.assertEqual(search_products(self.connection, query="%"), [])
