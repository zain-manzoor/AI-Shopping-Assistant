PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    category_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES categories(category_id),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    price_paisa INTEGER NOT NULL CHECK (price_paisa >= 0),
    stock_on_hand INTEGER NOT NULL CHECK (stock_on_hand >= 0),
    brand TEXT,
    model TEXT,
    product_type TEXT,
    key_specs TEXT,
    size TEXT,
    color TEXT,
    material TEXT,
    fit TEXT,
    author TEXT,
    genre TEXT,
    format TEXT,
    home_type TEXT,
    home_material TEXT,
    dimensions TEXT,
    CHECK (
        (category_id = 'electronics' AND brand IS NOT NULL AND model IS NOT NULL
            AND product_type IS NOT NULL AND key_specs IS NOT NULL
            AND size IS NULL AND color IS NULL AND material IS NULL AND fit IS NULL
            AND author IS NULL AND genre IS NULL AND format IS NULL
            AND home_type IS NULL AND home_material IS NULL AND dimensions IS NULL)
        OR
        (category_id = 'clothing' AND size IS NOT NULL AND color IS NOT NULL
            AND material IS NOT NULL AND fit IS NOT NULL
            AND brand IS NULL AND model IS NULL AND product_type IS NULL AND key_specs IS NULL
            AND author IS NULL AND genre IS NULL AND format IS NULL
            AND home_type IS NULL AND home_material IS NULL AND dimensions IS NULL)
        OR
        (category_id = 'books' AND author IS NOT NULL AND genre IS NOT NULL AND format IS NOT NULL
            AND brand IS NULL AND model IS NULL AND product_type IS NULL AND key_specs IS NULL
            AND size IS NULL AND color IS NULL AND material IS NULL AND fit IS NULL
            AND home_type IS NULL AND home_material IS NULL AND dimensions IS NULL)
        OR
        (category_id = 'home-accessories' AND home_type IS NOT NULL
            AND home_material IS NOT NULL AND dimensions IS NOT NULL
            AND brand IS NULL AND model IS NULL AND product_type IS NULL AND key_specs IS NULL
            AND size IS NULL AND color IS NULL AND material IS NULL AND fit IS NULL
            AND author IS NULL AND genre IS NULL AND format IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL CHECK (length(trim(display_name)) > 0)
);

CREATE TABLE IF NOT EXISTS carts (
    cart_id INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS cart_items (
    cart_id INTEGER NOT NULL REFERENCES carts(cart_id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 10),
    PRIMARY KEY (cart_id, product_id)
);
