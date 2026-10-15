"""Parameterized catalog queries and customer-facing product views."""

from __future__ import annotations

import sqlite3
from decimal import Decimal, InvalidOperation
from typing import Any

VALID_CATEGORIES = {"electronics", "clothing", "books", "home-accessories"}
SPEC_FIELDS = {
    "electronics": ("brand", "model", "product_type", "key_specs"),
    "clothing": ("size", "color", "material", "fit"),
    "books": ("author", "genre", "format"),
    "home-accessories": ("home_type", "home_material", "dimensions"),
}


class CatalogInputError(ValueError):
    """Raised when a catalog filter is malformed or unsupported."""


def to_paisa(value: int | float | str | Decimal | None) -> int | None:
    """Convert a PKR amount to integer paisa without binary-float arithmetic."""
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise CatalogInputError("Prices must be valid numbers in PKR.") from error
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise CatalogInputError("Prices must be nonnegative and have at most two decimal places.")
    return int(amount * 100)


def format_pkr(paisa: int) -> str:
    """Format integer paisa as a readable PKR amount."""
    return f"PKR {paisa // 100:,}.{paisa % 100:02d}"


def _available_quantity(connection: sqlite3.Connection, product_id: str) -> tuple[int, int]:
    row = connection.execute(
        """SELECT p.stock_on_hand,
                  COALESCE((SELECT SUM(ci.quantity)
                            FROM cart_items AS ci
                            WHERE ci.product_id = p.product_id), 0) AS reserved
           FROM products AS p WHERE p.product_id = ?""",
        (product_id,),
    ).fetchone()
    if row is None:
        raise KeyError(product_id)
    reserved = int(row["reserved"])
    return int(row["stock_on_hand"]), max(0, int(row["stock_on_hand"]) - reserved)


def _product_view(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any]:
    stock_on_hand, available = _available_quantity(connection, row["product_id"])
    category = row["category_id"]
    specs = {field: row[field] for field in SPEC_FIELDS[category]}
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category_name"],
        "price_paisa": int(row["price_paisa"]),
        "price_pkr": format_pkr(int(row["price_paisa"])),
        "stock_on_hand": stock_on_hand,
        "available_quantity": available,
        "availability": "in stock" if available else "out of stock",
        "specifications": specs,
    }


_PRODUCT_SELECT = """SELECT p.*, c.name AS category_name
                     FROM products AS p JOIN categories AS c USING(category_id)"""


def search_products(
    connection: sqlite3.Connection,
    *,
    query: str | None = None,
    category: str | None = None,
    min_price_pkr: int | float | str | Decimal | None = None,
    max_price_pkr: int | float | str | Decimal | None = None,
    features: str | None = None,
) -> list[dict[str, Any]]:
    """Find products using case-insensitive literal matches and inclusive price bounds."""
    if any(
        value is not None and not isinstance(value, str) for value in (query, category, features)
    ):
        raise CatalogInputError("Name, category, and feature filters must be text.")
    minimum = to_paisa(min_price_pkr)
    maximum = to_paisa(max_price_pkr)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise CatalogInputError("The minimum price cannot be greater than the maximum price.")
    if category is not None:
        category = category.strip().casefold()
        if category not in VALID_CATEGORIES:
            raise CatalogInputError("Choose electronics, clothing, books, or home accessories.")
    query = query.strip() if query and query.strip() else None
    features = features.strip() if features and features.strip() else None
    if not any((query, category, minimum is not None, maximum is not None, features)):
        raise CatalogInputError("Give a name, category, price range, or feature to search for.")

    clauses: list[str] = []
    parameters: list[Any] = []
    if query:
        clauses.append("lower(p.name) LIKE ? ESCAPE '\\'")
        parameters.append(f"%{_escape_like(query.casefold())}%")
    if category:
        clauses.append("p.category_id = ?")
        parameters.append(category)
    if minimum is not None:
        clauses.append("p.price_paisa >= ?")
        parameters.append(minimum)
    if maximum is not None:
        clauses.append("p.price_paisa <= ?")
        parameters.append(maximum)
    if features:
        searchable = " || ' ' || ".join(
            [
                "p.name",
                "c.name",
                *(f"COALESCE(p.{field}, '')" for group in SPEC_FIELDS.values() for field in group),
            ]
        )
        clauses.append(f"lower({searchable}) LIKE ? ESCAPE '\\'")
        parameters.append(f"%{_escape_like(features.casefold())}%")
    sql = f"{_PRODUCT_SELECT} WHERE {' AND '.join(clauses)} ORDER BY p.product_id"
    rows = connection.execute(sql, parameters).fetchall()
    return [_product_view(connection, row) for row in rows]


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def get_product_details(connection: sqlite3.Connection, product_id: str) -> dict[str, Any] | None:
    """Return a product with its current available quantity, or None if it is missing."""
    row = connection.execute(
        f"{_PRODUCT_SELECT} WHERE p.product_id = ?", (product_id.strip(),)
    ).fetchone()
    return _product_view(connection, row) if row else None


def get_product_categories(connection: sqlite3.Connection) -> list[dict[str, str]]:
    """Return the catalog's seeded categories."""
    rows = connection.execute(
        "SELECT category_id, name FROM categories ORDER BY category_id"
    ).fetchall()
    return [{"category_id": row["category_id"], "name": row["name"]} for row in rows]


def compare_products(connection: sqlite3.Connection, product_ids: list[str]) -> dict[str, Any]:
    """Return details for requested products and explicitly list missing IDs."""
    if not isinstance(product_ids, list) or not all(isinstance(item, str) for item in product_ids):
        raise CatalogInputError("Product IDs must be provided as a list of text IDs.")
    ids = list(dict.fromkeys(item.strip() for item in product_ids))
    if len(ids) < 2:
        raise CatalogInputError("Choose at least two different products to compare.")
    if len(ids) > 4:
        raise CatalogInputError("Compare no more than four products at a time.")
    found = [
        product for product_id in ids if (product := get_product_details(connection, product_id))
    ]
    found_ids = {product["product_id"] for product in found}
    return {
        "products": found,
        "missing_product_ids": [item for item in ids if item not in found_ids],
    }


def check_stock(connection: sqlite3.Connection, product_id: str) -> dict[str, Any] | None:
    """Return current physical, reserved, and available counts for a known product."""
    row = connection.execute(
        """SELECT p.product_id, p.stock_on_hand,
                  COALESCE((SELECT SUM(ci.quantity) FROM cart_items ci
                            WHERE ci.product_id = p.product_id), 0) AS reserved
           FROM products p WHERE p.product_id = ?""",
        (product_id.strip(),),
    ).fetchone()
    if row is None:
        return None
    on_hand, reserved = int(row["stock_on_hand"]), int(row["reserved"])
    return {
        "product_id": row["product_id"],
        "stock_on_hand": on_hand,
        "reserved_quantity": reserved,
        "available_quantity": max(0, on_hand - reserved),
    }
