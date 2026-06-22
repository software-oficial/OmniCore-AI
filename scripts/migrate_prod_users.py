import os

from sqlalchemy import create_engine, text


def migrate():
    # URL de producción
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway",
    )
    engine = create_engine(db_url)

    with engine.connect() as conn:
        print("🚀 Aplicando migración UUS a tabla 'users'...")
        # 1. Renombrar email -> username
        try:
            conn.execute(text("ALTER TABLE users RENAME COLUMN email TO username"))
        except Exception as e:
            print(f"Skipping rename (puede que ya se llame username): {e}")

        # 2. Añadir columnas faltantes
        try:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN business_id TEXT REFERENCES businesses(id)"
                )
            )
        except Exception as e:
            print(f"Skipping business_id: {e}")

        try:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'EMPLOYEE'")
            )
        except Exception as e:
            print(f"Skipping role: {e}")

        conn.commit()
        print("✅ Migración completada.")


if __name__ == "__main__":
    migrate()
