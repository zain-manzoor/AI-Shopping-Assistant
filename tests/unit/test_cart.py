"""Cart arithmetic, validation, stock reservation, and customer isolation tests."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

from shopping_data.cart import (
    CartRejected,
    add_to_cart,
    remove_from_cart,
    update_cart_quantity,
    view_cart,
)
from shopping_data.database import connect
from tests.support import ShoppingDatabaseTestCase


class CartTests(ShoppingDatabaseTestCase):
    def test_add_increments_existing_line_and_totals_are_exact(self) -> None:
        first = add_to_cart(self.connection, "demo-customer-1", "EL-001", 2)
        second = add_to_cart(self.connection, "demo-customer-1", "EL-001", 1)
        self.assertEqual(second["items"][0]["quantity"], 3)
        self.assertEqual(second["items"][0]["subtotal_paisa"], 55_470_000)
        self.assertEqual(second["total_paisa"], 55_470_000)
        self.assertEqual(first["items"][0]["quantity"], 2)

    def test_update_sets_target_quantity_and_decrease_releases_stock(self) -> None:
        add_to_cart(self.connection, "demo-customer-1", "EL-001", 3)
        cart = update_cart_quantity(self.connection, "demo-customer-1", "EL-001", 1)
        self.assertEqual(cart["items"][0]["quantity"], 1)
        row = self.connection.execute(
            """SELECT stock_on_hand - (
                SELECT SUM(quantity) FROM cart_items WHERE product_id = ?
            ) FROM products WHERE product_id = ?""",
            ("EL-001", "EL-001"),
        ).fetchone()
        self.assertEqual(row[0], 7)

    def test_remove_releases_reservation_and_missing_remove_is_rejected(self) -> None:
        add_to_cart(self.connection, "demo-customer-1", "EL-001", 2)
        cart = remove_from_cart(self.connection, "demo-customer-1", "EL-001")
        self.assertEqual(cart["items"], [])
        with self.assertRaises(CartRejected) as raised:
            remove_from_cart(self.connection, "demo-customer-1", "EL-001")
        self.assertEqual(raised.exception.code, "not_in_cart")

    def test_invalid_quantities_and_unknown_products_are_rejected_without_change(self) -> None:
        for quantity in (0, -1, 11, 1.5, "2", True):
            with self.subTest(quantity=quantity), self.assertRaises(CartRejected):
                add_to_cart(self.connection, "demo-customer-1", "EL-001", quantity)
        with self.assertRaises(CartRejected):
            add_to_cart(self.connection, "demo-customer-1", "missing", 1)
        self.assertEqual(view_cart(self.connection, "demo-customer-1")["items"], [])

    def test_insufficient_stock_is_rejected_atomically(self) -> None:
        add_to_cart(self.connection, "demo-customer-1", "EL-001", 7)
        with self.assertRaises(CartRejected) as raised:
            add_to_cart(self.connection, "demo-customer-2", "EL-001", 2)
        self.assertEqual(raised.exception.code, "insufficient_stock")
        self.assertEqual(view_cart(self.connection, "demo-customer-2")["items"], [])

    def test_customer_carts_are_separate(self) -> None:
        add_to_cart(self.connection, "demo-customer-1", "EL-001", 1)
        self.assertEqual(view_cart(self.connection, "demo-customer-2")["items"], [])
        self.assertEqual(view_cart(self.connection, "demo-customer-1")["items"][0]["quantity"], 1)

    def test_empty_cart_has_zero_total(self) -> None:
        cart = view_cart(self.connection, "demo-customer-1")
        self.assertEqual(cart["items"], [])
        self.assertEqual(cart["total_paisa"], 0)

    def test_cart_survives_connection_close_and_reopen(self) -> None:
        add_to_cart(self.connection, "demo-customer-1", "EL-001", 2)
        self.connection.close()
        reopened = connect(self.database_file)
        try:
            restored = view_cart(reopened, "demo-customer-1")
            self.assertEqual(restored["items"][0]["quantity"], 2)
            self.assertEqual(restored["total_paisa"], 36_980_000)
        finally:
            reopened.close()

    def test_cart_rejects_a_twenty_first_distinct_item(self) -> None:
        available_ids = [
            row[0]
            for row in self.connection.execute(
                """SELECT product_id FROM products WHERE stock_on_hand > 0
                ORDER BY product_id LIMIT 21"""
            )
        ]
        for product_id in available_ids[:20]:
            add_to_cart(self.connection, "demo-customer-1", product_id, 1)
        with self.assertRaises(CartRejected) as raised:
            add_to_cart(self.connection, "demo-customer-1", available_ids[20], 1)
        self.assertEqual(raised.exception.code, "cart_item_limit")

    def test_two_customers_cannot_reserve_the_same_last_unit_concurrently(self) -> None:
        self.connection.execute(
            "UPDATE products SET stock_on_hand = 1 WHERE product_id = ?", ("EL-001",)
        )
        start = threading.Barrier(2)

        def reserve(customer_id: str) -> str:
            start.wait(timeout=5)
            connection = connect(self.database_file)
            try:
                add_to_cart(connection, customer_id, "EL-001", 1)
                return "reserved"
            except CartRejected as error:
                return error.code
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(reserve, ("demo-customer-1", "demo-customer-2")))
        self.assertCountEqual(outcomes, ["reserved", "insufficient_stock"])
        reserved = self.connection.execute(
            "SELECT SUM(quantity) FROM cart_items WHERE product_id = ?", ("EL-001",)
        ).fetchone()[0]
        self.assertEqual(reserved, 1)
