from sqlalchemy import create_engine, inspect, text

# URL provided by user
DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"


def inspect_full_db():
    engine = create_engine(DB_URL)
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    print(f"Tables: {tables}")

    def print_table_info(table_name):
        print(f"\n--- Table: {table_name} ---")
        if table_name in tables:
            columns = inspector.get_columns(table_name)
            print("Columns:")
            for col in columns:
                print(
                    f"- {col['name']} (Type: {col['type']}) (Default: {col['default']}) (Nullable: {col['nullable']})"
                )

            # Try to fetch some data
            with engine.connect() as conn:
                try:
                    result = conn.execute(
                        text(f"SELECT * FROM {table_name} LIMIT 1")
                    ).fetchone()
                    print(f"First row data: {result}")
                except Exception as e:
                    print(f"Could not fetch data: {e}")
        else:
            print(f"Table '{table_name}' not found.")

    print_table_info("products")
    print_table_info("system_audit_log")
    print_table_info("apps")  # To check app_id reference
    print_table_info("agent_app_mapping")  # To check app_id reference


if __name__ == "__main__":
    inspect_full_db()
