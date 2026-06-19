-- PAYMENTS SECTOR: MULTI-ACCOUNT FINANCIAL ARCHITECTURE

-- 1. Transactions (The "Money Trail" linked to a specific credential)
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    credential_id TEXT REFERENCES service_credentials(id),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(20) NOT NULL, -- 'PENDING', 'COMPLETED', 'FAILED', 'REFUNDED'
    gateway_ref TEXT, -- MP Payment ID
    payment_method VARCHAR(50), -- 'MercadoPago', 'Transfer', 'Cash'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sales (The "Business Deal")
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    transaction_id TEXT REFERENCES transactions(transaction_id),
    client_name VARCHAR(255),
    total_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'COMPLETED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Sale Items (The "What was sold")
CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INT REFERENCES sales(id) ON DELETE CASCADE,
    sku TEXT, -- Link to product_variants
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL
);

-- 4. Cash Box (The "Daily Control" per credential/store)
CREATE TABLE IF NOT EXISTS cash_box (
    id SERIAL PRIMARY KEY,
    credential_id TEXT REFERENCES service_credentials(id),
    abierta BOOLEAN DEFAULT FALSE,
    efectivo_inicial DECIMAL(12,2) DEFAULT 0,
    ventas_efectivo DECIMAL(12,2) DEFAULT 0,
    ventas_digital DECIMAL(12,2) DEFAULT 0,
    hora_apertura TIMESTAMP,
    hora_cierre TIMESTAMP,
    monto_cierre_real DECIMAL(12,2),
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trans_cred ON transactions(credential_id);
CREATE INDEX IF NOT EXISTS idx_cash_cred ON cash_box(credential_id);
