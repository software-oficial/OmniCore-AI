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
        stats = []

        # Volver a usar 'businesses' ya que el simulador y el setup registran aquí los negocios
        businesses_raw = (
            conn.execute(text("SELECT id, name, plan FROM businesses")).mappings().all()
        )

        for business in businesses_raw:
            business_id = business["id"]
            business_name = business["name"]

            # Empleados
            employees_count = conn.execute(
                text("SELECT count(*) FROM users WHERE business_id = :bid"),
                {"bid": business_id},
            ).scalar()

            # Items de Stock únicos
            stock_items_count = conn.execute(
                text("SELECT count(DISTINCT sku) FROM stock WHERE business_id = :bid"),
                {"bid": business_id},
            ).scalar()

            # Total de ventas (Usamos app_id porque en la tabla sales se llama así, pero el valor es el business_id)
            sales_count = conn.execute(
                text("SELECT count(*) FROM sales WHERE app_id = :bid"),
                {"bid": business_id},
            ).scalar()

            # Monto total de ventas
            total_sales_amount = conn.execute(
                text("SELECT SUM(total_amount) FROM sales WHERE app_id = :bid"),
                {"bid": business_id},
            ).scalar()

            stats.append(
                {
                    "id": business_id,
                    "name": business_name,
                    "plan": business["plan"],
                    "employees": employees_count,
                    "stock_items": stock_items_count,
                    "sales_count": sales_count,
                    "total_sales_amount": float(total_sales_amount or 0),
                }
            )
        return stats


async def monitor():
    print("🚀 Iniciando Monitor en Tiempo Real (UUS)...\n")
    header = f"{'Hora':<10} | {'Negocio (ID)':<40} | {'Plan':<8} | {'Empleados':<10} | {'Stock':<8} | {'Ventas':<8} | {'Monto Total':<12}"
    print(header)
    print("-" * len(header))

    while True:
        stats = get_db_stats()

        # Resetear cursor al inicio y limpiar pantalla para efecto de dashboard fijo
        print("\033[H\033[J", end="")

        print(header)
        print("-" * len(header))

        if not stats:
            print(f"[{time.strftime('%H:%M:%S')}] No hay negocios activos.")
        else:
            for business in stats:
                print(
                    f"{time.strftime('%H:%M:%S'):<10} | "
                    f"{(business['name'] + ' (' + business['id'][:8] + '...)'):<40} | "
                    f"{business['plan']:<8} | "
                    f"{business['employees']:<10} | "
                    f"{business['stock_items']:<8} | "
                    f"{business['sales_count']:<8} | "
                    f"{business['total_sales_amount']:<12.2f}"
                )
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(monitor())
