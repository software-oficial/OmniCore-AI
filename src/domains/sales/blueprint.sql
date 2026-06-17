-- OmniCore-AI Sales & Payments Blueprint
-- This SQL should be executed by the developer in their external database.

-- Sales Table
CREATE TABLE IF NOT EXISTS sales (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    client_email VARCHAR(255),
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, PAID, CANCELLED, COMPLETED
    payment_method VARCHAR(50), -- CASH, CREDIT_CARD, TRANSFER, MP
    payment_reference VARCHAR(255),
    paga_con DECIMAL(12, 2) DEFAULT 0.00,
    vuelto DECIMAL(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sale Items Table
CREATE TABLE IF NOT EXISTS sale_items (
    id SERIAL PRIMARY KEY,
    sale_id INTEGER REFERENCES sales(id) ON DELETE CASCADE,
    product_code VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cash Box Table (For Physical Store Management)
CREATE TABLE IF NOT EXISTS cash_box (
    id SERIAL PRIMARY KEY,
    abierta BOOLEAN DEFAULT FALSE,
    efectivo_inicial DECIMAL(12, 2) DEFAULT 0.00,
    ventas_efectivo DECIMAL(12, 2) DEFAULT 0.00,
    ventas_digital DECIMAL(12, 2) DEFAULT 0.00,
    monto_cierre_real DECIMAL(12, 2),
    hora_apertura TIMESTAMP WITH TIME ZONE,
    hora_cierre TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);
CREATE INDEX IF NOT EXISTS idx_sales_client ON sales(client_name);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id);
