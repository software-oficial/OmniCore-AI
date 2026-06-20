from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"


def fix_schema():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Applying schema fixes...")

        # Enable uuid-ossp extension for gen_random_uuid()
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

        # Products table fixes
        # Ensure 'id' column is TEXT PRIMARY KEY DEFAULT gen_random_uuid()
        conn.execute(
            text("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_pkey CASCADE")
        )
        conn.execute(text("ALTER TABLE products ALTER COLUMN id TYPE TEXT"))
        conn.execute(
            text("ALTER TABLE products ALTER COLUMN id SET DEFAULT gen_random_uuid()")
        )
        conn.execute(text("ALTER TABLE products ALTER COLUMN id SET NOT NULL"))
        conn.execute(text("ALTER TABLE products ADD PRIMARY KEY (id)"))

        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS code TEXT"))
        conn.execute(
            text(
                "UPDATE products SET code = gen_random_uuid()::text WHERE code IS NULL"
            )
        )
        conn.execute(text("ALTER TABLE products ALTER COLUMN code SET NOT NULL"))
        conn.execute(
            text("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_code_key")
        )  # Ensure unique constraint is applied correctly
        conn.execute(
            text("ALTER TABLE products ADD CONSTRAINT products_code_key UNIQUE (code)")
        )

        conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS app_id TEXT"))
        conn.execute(
            text(
                "UPDATE products SET app_id = (SELECT id FROM apps LIMIT 1) WHERE app_id IS NULL"
            )
        )
        conn.execute(text("ALTER TABLE products ALTER COLUMN app_id SET NOT NULL"))
        conn.execute(
            text("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_app_id_fkey")
        )  # Ensure FK is applied correctly
        conn.execute(
            text(
                "ALTER TABLE products ADD CONSTRAINT products_app_id_fkey FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE"
            )
        )

        conn.execute(
            text(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS price DECIMAL(12,2) DEFAULT 0.0"
            )
        )
        conn.execute(text("ALTER TABLE products ALTER COLUMN price SET DEFAULT 0.0"))
        conn.execute(
            text("ALTER TABLE products ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 0")
        )
        conn.execute(text("ALTER TABLE products ALTER COLUMN quantity SET DEFAULT 0"))
        conn.execute(
            text("ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(100)")
        )
        conn.execute(
            text(
                "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_weight BOOLEAN DEFAULT FALSE"
            )
        )
        print("Fixed 'products' table.")

        # system_audit_log fix
        with engine.connect() as check_conn:
            result = check_conn.execute(
                text(
                    "SELECT data_type FROM information_schema.columns WHERE table_name = 'system_audit_log' AND column_name = 'params'"
                )
            ).fetchone()
            if not result or result.data_type != "text":
                conn.execute(
                    text(
                        "ALTER TABLE system_audit_log ADD COLUMN IF NOT EXISTS params TEXT"
                    )
                )

        with engine.connect() as check_conn:
            result = check_conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'system_audit_log' AND column_name = 'created_at'"
                )
            ).fetchone()
            if result:
                conn.execute(
                    text(
                        "ALTER TABLE system_audit_log RENAME COLUMN created_at TO timestamp"
                    )
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE system_audit_log ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                )
        print("Fixed 'system_audit_log' table.")

        # Ensure stock_movements exists and has correct foreign keys
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS stock_movements (
                id SERIAL PRIMARY KEY,
                app_id TEXT REFERENCES apps(id) ON DELETE CASCADE NOT NULL,
                product_code TEXT NOT NULL REFERENCES products(code),
                amount INT NOT NULL,
                reason TEXT,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Add app_id to stock_movements if it doesn't exist
        with engine.connect() as check_conn:
            result = check_conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'stock_movements' AND column_name = 'app_id'"
                )
            ).fetchone()
            if not result:
                conn.execute(text("ALTER TABLE stock_movements ADD COLUMN app_id TEXT"))
                conn.execute(
                    text(
                        "UPDATE stock_movements SET app_id = (SELECT id FROM apps LIMIT 1) WHERE app_id IS NULL"
                    )
                )  # Backfill
                conn.execute(
                    text("ALTER TABLE stock_movements ALTER COLUMN app_id SET NOT NULL")
                )
                conn.execute(
                    text(
                        "ALTER TABLE stock_movements ADD CONSTRAINT stock_movements_app_id_fkey FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE"
                    )
                )

        print("Fixed 'stock_movements' table.")

        conn.commit()
        print("Schema fixes applied successfully.")


if __name__ == "__main__":
    fix_schema()
