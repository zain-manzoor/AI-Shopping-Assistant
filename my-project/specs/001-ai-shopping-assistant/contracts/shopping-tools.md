# MCP Tool Contract: Catalog and Cart

This document defines the first-party server contract, independent of the model's wording. All operations return structured, truthful results. Tool failures must not be rendered as success. JSON-like field names below are contract fields, not a database schema. IDs are opaque strings. Prices are numeric PKR values in customer-readable output; persisted arithmetic uses integer paisa.

## Common behavior

- Server: local first-party MCP server over stdio. ADK is its MCP client via `McpToolset`.
- Catalog search/details/comparison/stock return only seeded catalog facts. No tool fabricates a missing result.
- Cart tools require `customer_id`; the application callback overrides that value on every call from trusted application/session state. Never trust a model-selected ID.
- All tool arguments are validated. Cart writes are atomic. A validation/business rejection returns `status: "rejected"`, a stable `code`, and a short `message`; it does not mutate state.
- A successful read returns `status: "ok"`; a successful state change returns `status: "ok"` with the resulting cart. An internal failure is reported as a tool error or `status: "error"` with safe wording; do not expose secrets, paths, SQL, or stack traces.
- For an item-level missing product in comparison, return the missing ID/name marker alongside valid products. For a zero-result search, return an empty `products` list and explanatory message.

## `search_products`

Search using any combination of name, category, inclusive min/max price, and feature text. Feature matching is case-insensitive substring/phrase matching over names, category names, and listed spec fields; no synonym inference.

**Input**

| Field | Type | Required | Validation |
|---|---|---:|---|
| `query` | string/null | no | Name keyword/phrase; trimmed. |
| `category` | string/null | no | One of electronics, clothing, books, home accessories. |
| `min_price_pkr` | number/null | no | Nonnegative; inclusive. |
| `max_price_pkr` | number/null | no | Nonnegative; inclusive. |
| `features` | string/null | no | Case-insensitive catalog keyword/phrase. |

If min exceeds max, reject with `invalid_price_range`. If no filters are given, ask the customer to narrow the request at the conversation layer rather than dumping the catalog.

**Output**: `{status, products: ProductSummary[], message}`; empty list is valid no-match outcome.

## `get_product_details`

**Input**: `{product_id: string}`. Nonexistent ID returns `not_found`.

**Output**: `{status, product: ProductDetail|null, message}`. Detail includes product ID, name, category, price, currently available (unreserved) quantity, and category-specific catalog facts.

## `compare_products`

**Input**: `{product_ids: string[]}`. Require 2–4 requested IDs. Fewer than 2 yields `too_few_products`; more than 4 yields `too_many_products`. Deduplicate repeated IDs before comparison and explain if fewer than two distinct products remain.

**Output**: `{status, products: ProductDetail[], missing_product_ids: string[], message}`. Valid entries include real prices, available quantities, and listed specs. Missing entries carry no invented facts. Comparison explanation and recommendation against stated needs/budget are composed by the agent using these results.

## `get_product_categories`

**Input**: none.

**Output**: `{status, categories: [{category_id, name}], message}`; exactly the seeded four categories.

## `check_stock`

**Input**: `{product_id: string}`.

**Output**: `{status, product_id, stock_on_hand, reserved_quantity, available_quantity, message}`. All counts are read consistently. Nonexistent ID returns `not_found`.

## `add_to_cart`

**Input**: `{customer_id: string, product_id: string, quantity: integer}`. Quantity must be 1–10. Quantity means the requested amount to add; if the product is already present it increments the existing line. Resulting line may not exceed 10, available unreserved stock, or the 20-distinct-product cart limit.

**Output**: `{status, cart: CartView|null, message}`. On success, stock reservation delta is applied atomically and returned cart is authoritative. Rejections: `invalid_customer`, `not_found`, `invalid_quantity`, `quantity_limit`, `insufficient_stock`, `cart_item_limit`.

## `remove_from_cart`

**Input**: `{customer_id: string, product_id: string}`.

**Output**: `{status, cart: CartView|null, message}`. Success releases the full line reservation. If the item is absent, return `not_in_cart` and leave the cart unchanged.

## `update_cart_quantity`

**Input**: `{customer_id: string, product_id: string, quantity: integer}`. Quantity is the desired total line quantity, not a delta; valid range is 1–10. Rejected zero/negative and nonnumeric values should direct the customer to remove the product if they want zero. Increases reserve only the positive delta after current unreserved stock check; decreases release the difference.

**Output**: `{status, cart: CartView|null, message}`. Rejections include `not_in_cart`, `invalid_quantity`, `quantity_limit`, `insufficient_stock`.

## `view_cart`

**Input**: `{customer_id: string}`.

**Output**: `{status, cart: CartView, message}`. Empty carts return `items: []`, `total_pkr: 0`, and a clear empty message.

### Shared result shapes

`ProductSummary`: `{product_id, name, category, price_pkr, available_quantity, key_specs}`. `ProductDetail` has those fields plus category-specific spec fields. `CartView`: `{customer_id, items: [{product_id, name, unit_price_pkr, quantity, subtotal_pkr, available_quantity}], total_pkr}`. Prices/subtotals/totals are derived from SQLite catalog prices and saved cart quantity. Agent must not reconstruct cart state from chat history.
