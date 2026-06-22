import asyncio
import os
import time

from sqlalchemy import create_engine, text

# Configuración
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway",
)
engine = create_engine(DB_URL)


def get_db_stats():
    with engine.connect() as conn:
        stats = {}
        # Negocios
        stats["businesses"] = conn.execute(
            text("SELECT count(*) FROM businesses")
        ).scalar()
        # Stock
        stats["stock_items"] = conn.execute(text("SELECT count(*) FROM stock")).scalar()
        # Ventas
        stats["sales"] = conn.execute(text("SELECT count(*) FROM sales")).scalar()
        return stats


async def monitor():
    print("🚀 Iniciando Monitor en Tiempo Real (UUS)...")
    while True:
        stats = get_db_stats()
        print(
            f"\r[ {time.strftime('%H:%M:%S')} ] "
            f"Negocios: {stats['businesses']} | "
            f"Items Stock: {stats['stock_items']} | "
            f"Ventas: {stats['sales']}",
            end="",
            flush=True,
        )
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(monitor())
