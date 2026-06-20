from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"

def fix_schema():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Applying schema fixes...")
        
        # Products table fixes
        # Check if 'id' column exists and is not TEXT PRIMARY KEY DEFAULT gen_random_uuid()
        with engine.connect() as check_conn:
            result = check_conn.execute(text("SELECT data_type, column_default FROM information_schema.columns WHERE table_name = 'products' AND column_name = 'id'")).fetchone()
            if not result or result.data_type != 'text' or 'gen_random_uuid()' not in (result.column_default or ''):
                # If 'id' is not TEXT or doesn't have gen_random_uuid as default, we assume it needs fixing
                # Drop primary key constraint to alter column type if needed
                conn.execute(text("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_pkey CASCADE"))
                conn.execute(text("ALTER TABLE products ALTER COLUMN id TYPE TEXT"))
                conn.execute(text("ALTER TABLE products ALTER COLUMN id SET DEFAULT gen_random_uuid()"))
                conn.execute(text("ALTER TABLE products ADD PRIMARY KEY (id)"))

        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS code TEXT UNIQUE"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS price DECIMAL(12,2) DEFAULT 0.0"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 0"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(100)"))
        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_weight BOOLEAN DEFAULT FALSE"))
        print("Fixed 'products' table.")
        
        # system_audit_log fix
        # Check if 'params' column exists and is TEXT
        with engine.connect() as check_conn:
            result = check_conn.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'system_audit_log' AND column_name = 'params'")).fetchone()
            if not result or result.data_type != 'text':
                conn.execute(text("ALTER TABLE system_audit_log ADD COLUMN IF NOT EXISTS params TEXT"))
        
        # Check if 'timestamp' column exists and is not created_at
        with engine.connect() as check_conn:
            result = check_conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'system_audit_log' AND column_name = 'created_at'")).fetchone()
            if result: # created_at exists, rename it to timestamp
                conn.execute(text("ALTER TABLE system_audit_log RENAME COLUMN created_at TO timestamp"))
            else: # created_at does not exist, ensure timestamp exists
                conn.execute(text("ALTER TABLE system_audit_log ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
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
