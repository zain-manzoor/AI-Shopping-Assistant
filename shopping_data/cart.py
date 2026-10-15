"""Customer-scoped cart operations with serialized stock reservations."""

from __future__ import annotations

import sqlite3
from typing import Any

from shopping_data.catalog import format_pkr
from shopping_data.database import write_transaction

MAX_QUANTITY = 10
MAX_DISTINCT_PRODUCTS = 20


class CartRejected(ValueError):
    """A validated shopping operation that must not mutate the cart."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def ensure_customer(connection: sqlite3.Connection, customer_id: str) -> None:
    """Ensure an application-assigned local demo identity is present."""
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CartRejected(
            "invalid_customer", "The application did not provide a customer identity."
        )
    normalized_id = customer_id.strip()
    connection.execute(
        "INSERT INTO customers(customer_id, display_name) VALUES (?, ?) "
        "ON CONFLICT(customer_id) DO NOTHING",
        (normalized_id, f"Local demo customer {normalized_id[-8:]}"),
    )


def _validate_quantity(quantity: Any) -> int:
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise CartRejected("invalid_quantity", "Quantity must be a whole number from 1 to 10.")
    if quantity < 1:
        raise CartRejected(
            "invalid_quantity", "Quantity must be at least 1; remove the item to set it to zero."
        )
    if quantity > MAX_QUANTITY:
        raise CartRejected("quantity_limit", "A cart can hold at most 10 units of one product.")
    return quantity


def _cart_id(connection: sqlite3.Connection, customer_id: str) -> int | None:
    row = connection.execute(
        "SELECT cart_id FROM carts WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    return int(row["cart_id"]) if row else None


def _ensure_cart(connection: sqlite3.Connection, customer_id: str) -> int:
    connection.execute(
        "INSERT INTO carts(customer_id) VALUES (?) ON CONFLICT(customer_id) DO NOTHING",
        (customer_id,),
    )
    result = _cart_id(connection, customer_id)
    assert result is not None
    return result


def _stock(connection: sqlite3.Connection, product_id: str) -> tuple[int, int] | None:
    row = connection.execute(
        """SELECT p.stock_on_hand,
                  COALESCE((SELECT SUM(ci.quantity) FROM cart_items ci
                            WHERE ci.product_id = p.product_id), 0) AS reserved
           FROM products p WHERE p.product_id = ?""",
        (product_id,),
    ).fetchone()
    if row is None:
        return None
    return int(row["stock_on_hand"]), int(row["reserved"])


def _require_product(connection: sqlite3.Connection, product_id: str) -> str:
    if not isinstance(product_id, str) or not product_id.strip():
        raise CartRejected("not_found", "Provide a valid product ID from the catalog.")
    normalized_id = product_id.strip()
    if _stock(connection, normalized_id) is None:
        raise CartRejected("not_found", f"Product {normalized_id} is not in the catalog.")
    return normalized_id


def _check_increase(stock: tuple[int, int], delta: int) -> None:
    on_hand, reserved = stock
    available = max(0, on_hand - reserved)
    if delta > available:
        raise CartRejected(
            "insufficient_stock",
            f"Only {available} additional unit(s) are currently available.",
        )


def _view(connection: sqlite3.Connection, customer_id: str, cart_id: int | None) -> dict[str, Any]:
    if cart_id is None:
        return {
            "customer_id": customer_id,
            "items": [],
            "total_paisa": 0,
            "total_pkr": format_pkr(0),
        }
    rows = connection.execute(
        """SELECT ci.product_id, p.name, p.price_paisa, ci.quantity, p.stock_on_hand,
                  (SELECT COALESCE(SUM(other.quantity), 0)
                   FROM cart_items other WHERE other.product_id = p.product_id) AS reserved
           FROM cart_items ci JOIN products p USING(product_id)
           WHERE ci.cart_id = ? ORDER BY p.product_id""",
        (cart_id,),
    ).fetchall()
    items: list[dict[str, Any]] = []
    total = 0
    for row in rows:
        price = int(row["price_paisa"])
        quantity = int(row["quantity"])
        subtotal = price * quantity
        total += subtotal
        items.append(
            {
                "product_id": row["product_id"],
                "name": row["name"],
                "unit_price_paisa": price,
                "unit_price_pkr": format_pkr(price),
                "quantity": quantity,
                "subtotal_paisa": subtotal,
                "subtotal_pkr": format_pkr(subtotal),
                "available_quantity": max(0, int(row["stock_on_hand"]) - int(row["reserved"])),
            }
        )
    return {
        "customer_id": customer_id,
        "items": items,
        "total_paisa": total,
        "total_pkr": format_pkr(total),
    }


def view_cart(connection: sqlite3.Connection, customer_id: str) -> dict[str, Any]:
    """Return the customer's saved cart and a total computed from catalog prices."""
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CartRejected(
            "invalid_customer", "The application did not provide a customer identity."
        )
    customer_id = customer_id.strip()
    exists = connection.execute(
        "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if exists is None:
        raise CartRejected("invalid_customer", "This local demo customer is not registered.")
    return _view(connection, customer_id, _cart_id(connection, customer_id))


def add_to_cart(
    connection: sqlite3.Connection, customer_id: str, product_id: str, quantity: Any
) -> dict[str, Any]:
    """Add units, incrementing an existing line, and reserve only the added units."""
    quantity = _validate_quantity(quantity)
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CartRejected(
            "invalid_customer", "The application did not provide a customer identity."
        )
    customer_id = customer_id.strip()
    with write_transaction(connection):
        if (
            connection.execute(
                "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
            ).fetchone()
            is None
        ):
            raise CartRejected("invalid_customer", "This local demo customer is not registered.")
        product_id = _require_product(connection, product_id)
        cart_id = _cart_id(connection, customer_id)
        current_row = (
            connection.execute(
                "SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
                (cart_id, product_id),
            ).fetchone()
            if cart_id is not None
            else None
        )
        current = int(current_row["quantity"]) if current_row else 0
        new_total = current + quantity
        if new_total > MAX_QUANTITY:
            raise CartRejected("quantity_limit", "A cart can hold at most 10 units of one product.")
        if not current_row and cart_id is not None:
            distinct = connection.execute(
                "SELECT COUNT(*) AS count FROM cart_items WHERE cart_id = ?", (cart_id,)
            ).fetchone()["count"]
            if int(distinct) >= MAX_DISTINCT_PRODUCTS:
                raise CartRejected(
                    "cart_item_limit", "A cart can contain at most 20 distinct products."
                )
        stock = _stock(connection, product_id)
        assert stock is not None
        _check_increase(stock, quantity)
        cart_id = _ensure_cart(connection, customer_id)
        connection.execute(
            """INSERT INTO cart_items(cart_id, product_id, quantity) VALUES (?, ?, ?)
                ON CONFLICT(cart_id, product_id) DO UPDATE SET
                    quantity = cart_items.quantity + excluded.quantity""",
            (cart_id, product_id, quantity),
        )
    return _view(connection, customer_id, cart_id)


def update_cart_quantity(
    connection: sqlite3.Connection, customer_id: str, product_id: str, quantity: Any
) -> dict[str, Any]:
    """Set a cart line to the requested total quantity, reserving or releasing the delta."""
    quantity = _validate_quantity(quantity)
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CartRejected(
            "invalid_customer", "The application did not provide a customer identity."
        )
    customer_id = customer_id.strip()
    with write_transaction(connection):
        if (
            connection.execute(
                "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
            ).fetchone()
            is None
        ):
            raise CartRejected("invalid_customer", "This local demo customer is not registered.")
        product_id = _require_product(connection, product_id)
        cart_id = _cart_id(connection, customer_id)
        row = (
            connection.execute(
                "SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
                (cart_id, product_id),
            ).fetchone()
            if cart_id is not None
            else None
        )
        if row is None:
            raise CartRejected("not_in_cart", "That product is not in your cart.")
        current = int(row["quantity"])
        if quantity > current:
            stock = _stock(connection, product_id)
            assert stock is not None
            _check_increase(stock, quantity - current)
        connection.execute(
            "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
            (quantity, cart_id, product_id),
        )
    return _view(connection, customer_id, cart_id)


def remove_from_cart(
    connection: sqlite3.Connection, customer_id: str, product_id: str
) -> dict[str, Any]:
    """Remove a line and release its stock reservation."""
    if not isinstance(customer_id, str) or not customer_id.strip():
        raise CartRejected(
            "invalid_customer", "The application did not provide a customer identity."
        )
    customer_id = customer_id.strip()
    with write_transaction(connection):
        if (
            connection.execute(
                "SELECT 1 FROM customers WHERE customer_id = ?", (customer_id,)
            ).fetchone()
            is None
        ):
            raise CartRejected("invalid_customer", "This local demo customer is not registered.")
        product_id = _require_product(connection, product_id)
        cart_id = _cart_id(connection, customer_id)
        cursor = (
            connection.execute(
                "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?",
                (cart_id, product_id),
            )
            if cart_id is not None
            else None
        )
        if cursor is None or cursor.rowcount == 0:
            raise CartRejected("not_in_cart", "That product is not in your cart.")
    return _view(connection, customer_id, cart_id)
