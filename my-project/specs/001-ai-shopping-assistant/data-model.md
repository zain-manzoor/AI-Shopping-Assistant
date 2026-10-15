# Data Model: AI Shopping Assistant

The application database is the durable authority for catalog and shopping state. ADK session state is conversation context only; it never substitutes for cart rows. Schema SQL is planned for `shopping_data/schema.sql` and all statements use bound parameters.

## Entities and relationships

```text
categories 1 ─── * products
customers  1 ─── 1 carts
carts      1 ─── * cart_items * ─── 1 products
```

### categories

| Field | Type | Rules |
|---|---|---|
| `category_id` | TEXT | Primary key; stable slug such as `electronics`. |
| `name` | TEXT | Required, unique, one of the four seeded category names. |

### products

| Field | Type | Rules |
|---|---|---|
| `product_id` | TEXT | Primary key; stable fictional ID. |
| `category_id` | TEXT | Required FK to `categories`. |
| `name` | TEXT | Required, nonblank. |
| `price_paisa` | INTEGER | Required, nonnegative PKR minor-unit amount; no floating arithmetic. |
| `stock_on_hand` | INTEGER | Required, nonnegative physical demo stock. |
| `brand`, `model`, `product_type`, `key_specs` | TEXT | Electronics fields; non-null for electronics, empty/null otherwise. `key_specs` is a concise catalog fact string. |
| `size`, `color`, `material`, `fit` | TEXT | Clothing fields; non-null for clothing. |
| `author`, `genre`, `format` | TEXT | Book fields; non-null for books. |
| `home_type`, `home_material`, `dimensions` | TEXT | Home accessory fields; non-null for home accessories. |

Category-specific fields are ordinary columns rather than a flexible attribute store. Add SQL CHECK constraints so each category requires its own fields; fields for other categories can be NULL. Catalog rows are seed-controlled and read-only in the initial user experience.

### customers

| Field | Type | Rules |
|---|---|---|
| `customer_id` | TEXT | Primary key; stable local demo identity created/chosen by the application. Not authentication. |
| `display_name` | TEXT | Required fictional demo label; no real personal data. |

### carts

| Field | Type | Rules |
|---|---|---|
| `cart_id` | INTEGER | Primary key. |
| `customer_id` | TEXT | Required FK to `customers`, UNIQUE so each demo customer has one durable cart. |

### cart_items

| Field | Type | Rules |
|---|---|---|
| `cart_id` | INTEGER | Required FK to `carts` with `ON DELETE CASCADE`. |
| `product_id` | TEXT | Required FK to `products`; composite primary key with cart ID and thus UNIQUE per product in each cart. |
| `quantity` | INTEGER | Required CHECK `quantity BETWEEN 1 AND 10`. One unit in this row reserves one unit of stock. |

## Integrity and operations

- Create the five tables with primary and foreign keys enabled (`PRAGMA foreign_keys=ON` for every connection).
- Use `CHECK` constraints for nonnegative price/stock, quantity 1–10, category-specific required attributes, and known category IDs. Application validation additionally enforces at most 20 distinct products in a cart and comparison count 2–4.
- Store product ID, price, and stock values from catalog queries; cart display computes each subtotal as `price_paisa * quantity` and total as the integer sum of subtotals. Format only at the customer-facing boundary as PKR.
- Available stock is `stock_on_hand - SUM(cart_items.quantity)` across all carts for the product. Never trust an earlier search result as the current stock check.
- For add, quantity increase, decrease, and removal, start a SQLite write transaction (`BEGIN IMMEDIATE`), load current cart and stock, validate customer, product, quantity, distinct-item limit and reservation delta, then mutate atomically and commit. On any failure, roll back without partial changes. Adding a carted item increments quantity; update sets the total target quantity.
- A request whose total quantity exceeds 10, available stock, or cart distinct-item limit is rejected with no state change. Removing a missing product reports not-in-cart. No purchase/checkout transition exists.
- Use parameterized SQL for all user/tool values. The trusted `customer_id` is injected by the application callback, then used in every cart query; never derive it from a message or model output.
- The local identity selector/mapping is a demo convenience, not authentication. No email, address, card, or other real personal/payment data is stored.

## Seed and runtime state

Seed exactly 40 fictional products, 10 in each of electronics, clothing, books, and home accessories. Include realistic names/prices/stock and the fields above. Seed operation should be repeatable (stable IDs and upserts or insert-if-absent) and must not reset customer carts on every start.

Durable state is `shopping.db`: categories, products, demo customers, carts, cart lines, and reservations. Conversation-only state is ADK session state: criteria/preferences, rejected product IDs, and IDs the customer says they already own. A new chat starts with empty recommendation memory. A resumed ADK Web session can retain that conversation context through the ADK local session store, but that history is not authoritative for cart contents.
