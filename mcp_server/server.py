"""MCP 2.x stdio server that exposes the shopping data operations."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from mcp_server import tools

server = MCPServer("ai-shopping-catalog-cart")


@server.tool()
def search_products(
    query: str | None = None,
    category: str | None = None,
    min_price_pkr: float | None = None,
    max_price_pkr: float | None = None,
    features: str | None = None,
) -> dict:
    """Search fictional products by name, category, inclusive price range, and catalog features."""
    return tools.search_products(query, category, min_price_pkr, max_price_pkr, features)


@server.tool()
def get_product_details(product_id: str) -> dict:
    """Get a catalog product's ID, price, current availability, and listed specifications."""
    return tools.get_product_details(product_id)


@server.tool()
def compare_products(product_ids: list[str]) -> dict:
    """Get catalog-backed comparison data for two to four products."""
    return tools.compare_products(product_ids)


@server.tool()
def get_product_categories() -> dict:
    """List the product categories in the fictional catalog."""
    return tools.get_product_categories()


@server.tool()
def check_stock(product_id: str) -> dict:
    """Check current on-hand, reserved, and available stock for a product."""
    return tools.check_stock(product_id)


@server.tool()
def add_to_cart(customer_id: str, product_id: str, quantity: int) -> dict:
    """Add units to the customer's cart; an existing line is incremented."""
    return tools.add_to_cart(customer_id, product_id, quantity)


@server.tool()
def remove_from_cart(customer_id: str, product_id: str) -> dict:
    """Remove a product from the customer's cart and release its reservation."""
    return tools.remove_from_cart(customer_id, product_id)


@server.tool()
def update_cart_quantity(customer_id: str, product_id: str, quantity: int) -> dict:
    """Set a cart line to a total quantity from one through ten."""
    return tools.update_cart_quantity(customer_id, product_id, quantity)


@server.tool()
def view_cart(customer_id: str) -> dict:
    """View the customer's saved cart with current subtotals and total."""
    return tools.view_cart(customer_id)


if __name__ == "__main__":
    server.run()
