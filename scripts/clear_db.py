from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"
engine = create_engine(DB_URL)

tables_to_clear = [
    "system_audit_log",
    "sale_items",
    "sales",
    "transactions",
    "cash_box",
    "stock",
    "products",
    "aliases",
    "api_tokens",
    "user_credentials",
    "users",
    "user_profiles",
    "user_permissions",
    "service_credentials",
    "businesses",
    "business_settings",
    "governance_tiers",
    "governance_commands",
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
