-- STOCK SECTOR: PROFESSIONAL ARCHITECTURE

-- 1. General Product Data (The "Concept")
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    brand VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Product Variants (The "Physical Item")
CREATE TABLE IF NOT EXISTS product_variants (
    sku TEXT PRIMARY KEY,
    product_id TEXT REFERENCES products(id) ON DELETE CASCADE,
    color VARCHAR(50),
    size VARCHAR(50),
    material VARCHAR(50),
    price DECIMAL(12,2) NOT NULL,
    weight DECIMAL(10,3),
    is_weight_based BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Inventory Levels (Current Balance)
CREATE TABLE IF NOT EXISTS stock_levels (
    sku TEXT PRIMARY KEY REFERENCES product_variants(sku) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 0,
    min_threshold INT DEFAULT 5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Inventory Ledger (The "Truth" - Every single movement)
CREATE TABLE IF NOT EXISTS inventory_ledger (
    id SERIAL PRIMARY KEY,
    sku TEXT REFERENCES product_variants(sku),
    quantity_change INT NOT NULL,
    type VARCHAR(50), -- 'SALE', 'RESTOCK', 'RETURN', 'ADJUSTMENT'
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_stock_variants_prod ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_ledger_sku ON inventory_ledger(sku);
