from sqlalchemy import create_engine, inspect

# URL provided by user
DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"


def inspect_db():
    engine = create_engine(DB_URL)
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    print(f"Tables: {tables}")

    if "products" in tables:
        columns = inspector.get_columns("products")
        print("Columns in 'products':")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")
    else:
        print("'products' table not found.")

    if "system_audit_log" in tables:
        columns = inspector.get_columns("system_audit_log")
        print("Columns in 'system_audit_log':")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")


if __name__ == "__main__":
    inspect_db()
