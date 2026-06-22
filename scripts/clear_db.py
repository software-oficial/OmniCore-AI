from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"
engine = create_engine(DB_URL)

tables_to_clear = [
    "system_audit_log",
    "sale_items",
    "sales",
    "cash_box",
    "products",
    "aliases",
    "app_infrastructure",
    "agent_app_mapping",
    "apps",
    "agents",
    "api_tokens",
    "user_credentials",
    "users",
]

for table in tables_to_clear:
    with engine.connect() as conn:
        try:
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            conn.commit()
            print(f"✅ Tabla {table} vaciada.")
        except Exception as e:
            print(f"⚠️ No se pudo vaciar {table}: {e}")
print("🎉 Base de datos limpia.")
