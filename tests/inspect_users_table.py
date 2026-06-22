from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"
)


def inspect_users():
    with engine.connect() as conn:
        print("--- Table: users ---")
        result = conn.execute(
            text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'"
            )
        )
        for row in result:
            print(f"- {row[0]} (Type: {row[1]})")

        print("\nSample data:")
        sample = conn.execute(text("SELECT * FROM users LIMIT 5")).mappings().all()
        for s in sample:
            print(s)


if __name__ == "__main__":
    inspect_users()
