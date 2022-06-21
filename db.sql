DROP TABLE IF EXISTS cart;

CREATE TABLE cart (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_price INTEGER NOT NULL
);