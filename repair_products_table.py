from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"


def repair():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Starting repair...")

        # 1. Fix 'id' default
        print("Fixing 'id' default...")
        conn.execute(
            text("ALTER TABLE products ALTER COLUMN id SET DEFAULT gen_random_uuid()")
        )

        # 2. Fix 'app_id' default
        print("Fixing 'app_id' default...")
        # Get first app_id
        app_id_res = conn.execute(text("SELECT id FROM apps LIMIT 1")).fetchone()
        if app_id_res:
            app_id = app_id_res[0]
            conn.execute(
                text("ALTER TABLE products ALTER COLUMN app_id SET DEFAULT :app_id"),
                {"app_id": app_id},
            )
            print(f"Set app_id default to: {app_id}")
        else:
            print("Warning: No apps found, cannot set app_id default.")

        # 3. Ensure NOT NULL
        print("Ensuring NOT NULL constraints...")
        conn.execute(text("ALTER TABLE products ALTER COLUMN id SET NOT NULL"))
        conn.execute(text("ALTER TABLE products ALTER COLUMN app_id SET NOT NULL"))

        conn.commit()
        print("Repair completed successfully.")


if __name__ == "__main__":
    repair()
