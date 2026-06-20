from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"

def fix_schema():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Applying schema fixes...")
        
        # Products table fixes
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS code TEXT UNIQUE"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS price DECIMAL(12,2) DEFAULT 0.0"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 0"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(100)"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_weight BOOLEAN DEFAULT FALSE"))
        print("Fixed 'products' table.")
        
        # system_audit_log fix
        conn.execute(text("ALTER TABLE system_audit_log ADD COLUMN IF NOT EXISTS params TEXT"))
        print("Fixed 'system_audit_log' table.")
        
        # Ensure stock_movements exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id SERIAL PRIMARY KEY,
                app_id TEXT REFERENCES apps(id) ON DELETE CASCADE,
                product_code TEXT NOT NULL REFERENCES products(code),
                amount INT NOT NULL,
                reason TEXT,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("Fixed 'stock_movements' table.")
        
        conn.commit()
        print("Schema fixes applied successfully.")

if __name__ == "__main__":
    fix_schema()
