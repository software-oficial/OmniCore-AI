-- STOCK SECTOR: PROFESSIONAL ARCHITECTURE

-- 1. General Product Data
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    app_id TEXT REFERENCES apps(id) ON DELETE CASCADE,
    code TEXT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(12,2) NOT NULL DEFAULT 0.0,
    quantity INT NOT NULL DEFAULT 0,
    category VARCHAR(100),
    is_weight BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Stock Movements Ledger
CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    app_id TEXT REFERENCES apps(id) ON DELETE CASCADE,
    product_code TEXT NOT NULL REFERENCES products(code),
    amount INT NOT NULL,
    reason TEXT,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_app ON products(app_id);
CREATE INDEX IF NOT EXISTS idx_products_code ON products(code);
CREATE INDEX IF NOT EXISTS idx_movements_app ON stock_movements(app_id);
CREATE INDEX IF NOT EXISTS idx_movements_code ON stock_movements(product_code);
