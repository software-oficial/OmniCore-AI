import asyncio
import os
from datetime import datetime, timedelta

from sqlalchemy import create_engine, text

# Configuración
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway",
)
engine = create_engine(DB_URL)


class MasterDbMonitor:
    def __init__(self):
        self.last_check = datetime.now() - timedelta(seconds=5)
        self.event_history = []
        self.max_history = 10

    def fetch_global_stats(self, conn):
        """Obtiene los totales generales del sistema."""
        return {
            "biz": conn.execute(text("SELECT count(*) FROM businesses")).scalar(),
            "users": conn.execute(text("SELECT count(*) FROM users")).scalar(),
            "stock": conn.execute(text("SELECT count(*) FROM stock")).scalar(),
            "sales": conn.execute(text("SELECT count(*) FROM sales")).scalar(),
        }

    def fetch_business_table(self, conn):
        """Obtiene la tabla detallada de negocios."""
        businesses_raw = (
            conn.execute(text("SELECT id, name, plan FROM businesses")).mappings().all()
        )
        table_data = []
        for biz in businesses_raw:
            bid = biz["id"]
            # Empleados
            emp = conn.execute(
                text("SELECT count(*) FROM users WHERE business_id = :bid"),
                {"bid": bid},
            ).scalar()
            # Stock
            stk = conn.execute(
                text("SELECT count(DISTINCT sku) FROM stock WHERE business_id = :bid"),
                {"bid": bid},
            ).scalar()
            # Ventas
            sl_c = conn.execute(
                text("SELECT count(*) FROM sales WHERE app_id = :bid"), {"bid": bid}
            ).scalar()
            sl_a = conn.execute(
                text("SELECT SUM(total_amount) FROM sales WHERE app_id = :bid"),
                {"bid": bid},
            ).scalar()

            table_data.append(
                {
                    "name": biz["name"],
                    "id": bid[:8],
                    "plan": biz["plan"],
                    "emp": emp,
                    "stk": stk,
                    "sl_c": sl_c,
                    "sl_a": float(sl_a or 0),
                }
            )
        return table_data

    def fetch_new_events(self, conn):
        """Detecta nuevos cambios en la base de datos."""
        now = datetime.now()
        new_events = []

        # Negocios
        biz = conn.execute(
            text("SELECT name FROM businesses WHERE created_at > :last"),
            {"last": self.last_check},
        ).all()
        for b in biz:
            new_events.append(f"🏢 [NEGOCIO] {b[0]} creado")

        # Usuarios
        users = conn.execute(
            text(
                "SELECT u.username, b.name FROM users u JOIN businesses b ON u.business_id = b.id WHERE u.created_at > :last"
            ),
            {"last": self.last_check},
        ).all()
        for u in users:
            new_events.append(f"👤 [USER] {u[0]} unido a {u[1]}")

        # Stock
        stock = conn.execute(
            text(
                "SELECT s.sku, b.name FROM stock s JOIN businesses b ON s.business_id = b.id WHERE s.updated_at > :last"
            ),
            {"last": self.last_check},
        ).all()
        for s in stock:
            new_events.append(f"📦 [STOCK] {s[0]} actualizado en {s[1]}")

        # Ventas
        sales = conn.execute(
            text(
                "SELECT s.total_amount, b.name FROM sales s JOIN businesses b ON s.app_id = b.id WHERE s.created_at > :last"
            ),
            {"last": self.last_check},
        ).all()
        for sl in sales:
            new_events.append(f"💰 [VENTA] ${sl[0]} en {sl[1]}")

        self.last_check = now
        return new_events

    async def run(self):
        print("\033[2J\033[H")  # Limpiar pantalla

        while True:
            with engine.connect() as conn:
                globals_ = self.fetch_global_stats(conn)
                table = self.fetch_business_table(conn)
                events = self.fetch_new_events(conn)

            if events:
                for e in events:
                    self.event_history.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] {e}"
                    )
                self.event_history = self.event_history[-self.max_history :]

            # RENDERIZADO COMPACTO (Ancho ~60 chars)
            # RENDERIZADO
            print(
                "\033[2J\033[H", end=""
            )  # Limpiar pantalla completa y mover cursor al inicio
            print("=" * 60)
            print(f" 🚀 OMNICORE LIVE | {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 60)
            # SECCIÓN 1: METRICAS GLOBALES
            print(
                f" BIZ: {globals_['biz']:<3} | USR: {globals_['users']:<3} | STK: {globals_['stock']:<3} | VNT: {globals_['sales']:<3}"
            )
            print("-" * 60)

            # SECCIÓN 2: TABLA DE NEGOCIOS
            # Columnas: Name(15), ID(6), Plan(4), Emp(4), Stk(4), Vnt(4), Amt(8)
            header = f" {'Negocio':<15} | {'ID':<6} | {'Pl':<4} | {'E':<4} | {'S':<4} | {'V':<4} | {'Monto':<8}"
            print(header)
            print("-" * 60)
            for b in table:
                # Truncar nombre a 15, ID a 6
                name = b["name"][:14] + ".." if len(b["name"]) > 15 else b["name"]
                plan = b["plan"][0] if b["plan"] else "?"  # Solo primera letra (F/P)
                print(
                    f" {name:<15} | {b['id']:<6} | {plan:<4} | {b['emp']:<4} | {b['stk']:<4} | {b['sl_c']:<4} | ${b['sl_a']:<8.2f}"
                )

            if not table:
                print("  No hay negocios registrados.")

            print("-" * 60)

            # SECCIÓN 3: FEED DE EVENTOS
            print(" 🕒 EVENTOS:")
            if not self.event_history:
                print("  Esperando actividad...")
            else:
                for event in reversed(self.event_history):
                    # Acortar el mensaje del evento para que quepa en 60 chars
                    print(f"  {event[:55]}")

            print("\n" + "=" * 60)
            print("  Ctrl+C para salir | Refresco: 1s")

            await asyncio.sleep(1)


if __name__ == "__main__":
    monitor = MasterDbMonitor()
    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        print("\n👋 Monitor cerrado.")
