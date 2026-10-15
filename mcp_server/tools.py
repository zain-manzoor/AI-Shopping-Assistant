"""Plain Python operations used by MCP tools and direct deterministic tests."""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from shopping_data.cart import (
    CartRejected,
)
from shopping_data.cart import (
    add_to_cart as cart_add,
)
from shopping_data.cart import (
    remove_from_cart as cart_remove,
)
from shopping_data.cart import (
    update_cart_quantity as cart_update,
)
from shopping_data.cart import (
    view_cart as cart_view,
)
from shopping_data.catalog import (
    CatalogInputError,
)
from shopping_data.catalog import (
    check_stock as catalog_check_stock,
)
from shopping_data.catalog import (
    compare_products as catalog_compare,
)
from shopping_data.catalog import (
    get_product_categories as catalog_categories,
)
from shopping_data.catalog import (
    get_product_details as catalog_details,
)
from shopping_data.catalog import (
    search_products as catalog_search,
)
from shopping_data.database import open_database

logger = logging.getLogger(__name__)


def _failure(operation: str) -> dict[str, Any]:
    logger.error("Shopping data operation failed: %s", operation)
    return {
        "status": "error",
        "code": "storage_error",
        "message": "I could not access shopping data just now. Please try again.",
    }


def search_products(
    query: str | None = None,
    category: str | None = None,
    min_price_pkr: int | float | str | None = None,
    max_price_pkr: int | float | str | None = None,
    features: str | None = None,
) -> dict[str, Any]:
    """Search by name/category/price/features and return only catalog records."""
    try:
        with open_database() as connection:
            rows = catalog_search(
                connection,
                query=query,
                category=category,
                min_price_pkr=min_price_pkr,
                max_price_pkr=max_price_pkr,
                features=features,
            )
        return {
            "status": "ok",
            "products": rows,
            "message": f"Found {len(rows)} matching product(s)."
            if rows
            else "No products match those filters.",
        }
    except CatalogInputError as error:
        return {
            "status": "rejected",
            "code": "invalid_search",
            "message": str(error),
            "products": [],
        }
    except sqlite3.Error:
        return _failure("search_products")


def get_product_details(product_id: str) -> dict[str, Any]:
    """Look up one product ID, including current availability."""
    try:
        with open_database() as connection:
            product = catalog_details(connection, product_id)
        return (
            {"status": "ok", "product": product, "message": "Product details loaded."}
            if product
            else {
                "status": "not_found",
                "product": None,
                "message": "That product ID is not in the catalog.",
            }
        )
    except AttributeError, TypeError:
        return {
            "status": "rejected",
            "code": "invalid_product_id",
            "product": None,
            "message": "Provide a product ID as text.",
        }
    except sqlite3.Error:
        return _failure("get_product_details")


def get_product_categories() -> dict[str, Any]:
    """List the seeded product categories."""
    try:
        with open_database() as connection:
            categories = catalog_categories(connection)
        return {"status": "ok", "categories": categories}
    except sqlite3.Error:
        return _failure("get_product_categories")


def check_stock(product_id: str) -> dict[str, Any]:
    """Return current stock, reservations, and available units for a product."""
    try:
        with open_database() as connection:
            result = catalog_check_stock(connection, product_id)
        return (
            {"status": "ok", **result}
            if result
            else {
                "status": "not_found",
                "product_id": product_id,
                "message": "That product ID is not in the catalog.",
            }
        )
    except AttributeError, TypeError:
        return {
            "status": "rejected",
            "code": "invalid_product_id",
            "message": "Provide a product ID as text.",
        }
    except sqlite3.Error:
        return _failure("check_stock")


def compare_products(product_ids: list[str]) -> dict[str, Any]:
    """Compare up to four catalog products and report missing IDs explicitly."""
    try:
        with open_database() as connection:
            result = catalog_compare(connection, product_ids)
        return {"status": "ok", **result, "message": "Comparison data loaded from the catalog."}
    except CatalogInputError as error:
        return {
            "status": "rejected",
            "code": "invalid_comparison",
            "message": str(error),
            "products": [],
            "missing_product_ids": [],
        }
    except sqlite3.Error:
        return _failure("compare_products")


def add_to_cart(customer_id: str, product_id: str, quantity: int) -> dict[str, Any]:
    """Add units to the application-selected customer's durable cart."""
    try:
        with open_database() as connection:
            cart = cart_add(connection, customer_id, product_id, quantity)
        return {"status": "ok", "cart": cart, "message": "Added to your cart."}
    except CartRejected as error:
        return {"status": "rejected", "code": error.code, "message": str(error), "cart": None}
    except sqlite3.Error:
        return _failure("add_to_cart")


def remove_from_cart(customer_id: str, product_id: str) -> dict[str, Any]:
    """Remove a product line from the application-selected customer's cart."""
    try:
        with open_database() as connection:
            cart = cart_remove(connection, customer_id, product_id)
        return {"status": "ok", "cart": cart, "message": "Removed from your cart."}
    except CartRejected as error:
        return {"status": "rejected", "code": error.code, "message": str(error), "cart": None}
    except sqlite3.Error:
        return _failure("remove_from_cart")


def update_cart_quantity(customer_id: str, product_id: str, quantity: int) -> dict[str, Any]:
    """Set a cart line to the requested total quantity."""
    try:
        with open_database() as connection:
            cart = cart_update(connection, customer_id, product_id, quantity)
        return {"status": "ok", "cart": cart, "message": "Cart quantity updated."}
    except CartRejected as error:
        return {"status": "rejected", "code": error.code, "message": str(error), "cart": None}
    except sqlite3.Error:
        return _failure("update_cart_quantity")


def view_cart(customer_id: str) -> dict[str, Any]:
    """Read only the application-selected customer's saved cart."""
    try:
        with open_database() as connection:
            cart = cart_view(connection, customer_id)
        message = "Your cart is empty." if not cart["items"] else "Your saved cart is shown below."
        return {"status": "ok", "cart": cart, "message": message}
    except CartRejected as error:
        return {"status": "rejected", "code": error.code, "message": str(error), "cart": None}
    except sqlite3.Error:
        return _failure("view_cart")
