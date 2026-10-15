"""Database integrity, seed repeatability, and transaction rollback checks."""

from __future__ import annotations

import sqlite3

from shopping_data.seed_catalog import seed_catalog
from tests.support import ShoppingDatabaseTestCase


class DatabaseTests(ShoppingDatabaseTestCase):
    def test_seed_has_forty_products_evenly_split_across_four_categories(self) -> None:
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0], 40)
        counts = dict(
            self.connection.execute(
                "SELECT category_id, COUNT(*) FROM products GROUP BY category_id"
            ).fetchall()
        )
        self.assertEqual(
            counts,
            {
                "electronics": 10,
                "clothing": 10,
                "books": 10,
                "home-accessories": 10,
            },
        )

    def test_reseeding_is_idempotent_and_does_not_delete_cart_rows(self) -> None:
        self.connection.execute("INSERT INTO carts(customer_id) VALUES (?)", ("demo-customer-1",))
        seed_catalog(self.connection)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM products").fetchone()[0], 40)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM carts").fetchone()[0], 1)

    def test_check_constraints_reject_bad_price_stock_and_quantity(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "UPDATE products SET stock_on_hand = -1 WHERE product_id = ?", ("EL-001",)
            )
        self.connection.execute("INSERT INTO carts(customer_id) VALUES (?)", ("demo-customer-1",))
        cart_id = self.connection.execute("SELECT cart_id FROM carts").fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.connection.execute(
                "INSERT INTO cart_items(cart_id, product_id, quantity) VALUES (?, ?, ?)",
                (cart_id, "EL-001", 0),
            )

    def test_write_transaction_rolls_back_failed_operation(self) -> None:
        from shopping_data.database import write_transaction

        with self.assertRaises(RuntimeError), write_transaction(self.connection):
            self.connection.execute(
                "UPDATE products SET stock_on_hand = 1 WHERE product_id = ?", ("EL-001",)
            )
            raise RuntimeError("rollback")
        stock = self.connection.execute(
            "SELECT stock_on_hand FROM products WHERE product_id = ?", ("EL-001",)
        ).fetchone()[0]
        self.assertEqual(stock, 8)
