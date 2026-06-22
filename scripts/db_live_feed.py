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


class DbLiveFeed:
    def __init__(self):
        self.last_check = datetime.now() - timedelta(seconds=10)
        self.event_history = []
        self.max_history = 15

    def fetch_new_events(self):
        with engine.connect() as conn:
            now = datetime.now()
            new_events = []

            # 1. Nuevos Negocios
            biz = (
                conn.execute(
                    text(
                        "SELECT id, name, plan FROM businesses WHERE created_at > :last"
                    ),
                    {"last": self.last_check},
                )
                .mappings()
                .all()
            )
            for b in biz:
                new_events.append(f"🏢 [NEGOCIO] {b['name']} ({b['plan']}) creado.")

            # 2. Nuevos Usuarios/Empleados
            users = (
                conn.execute(
                    text(
                        """
                    SELECT u.username, u.role, b.name 
                    FROM users u 
                    JOIN businesses b ON u.business_id = b.id 
                    WHERE u.created_at > :last
                """
                    ),
                    {"last": self.last_check},
                )
                .mappings()
                .all()
            )
            for u in users:
                new_events.append(
                    f"👤 [USUARIO] {u['username']} ({u['role']}) unido a {u['name']}."
                )

            # 3. Cambios en Stock (Usamos updated_at)
            stock = (
                conn.execute(
                    text(
                        """
                    SELECT s.sku, s.data, b.name 
                    FROM stock s 
                    JOIN businesses b ON s.business_id = b.id 
                    WHERE s.updated_at > :last
                """
                    ),
                    {"last": self.last_check},
                )
                .mappings()
                .all()
            )
            for s in stock:
                new_events.append(f"📦 [STOCK] {s['sku']} actualizado en {s['name']}.")

            # 4. Nuevas Ventas
            sales = (
                conn.execute(
                    text(
                        """
                    SELECT s.total_amount, b.name 
                    FROM sales s 
                    JOIN businesses b ON s.app_id = b.id 
                    WHERE s.created_at > :last
                """
                    ),
                    {"last": self.last_check},
                )
                .mappings()
                .all()
            )
            for sl in sales:
                new_events.append(
                    f"💰 [VENTA] ${sl['total_amount']} registrada en {sl['name']}."
                )

            self.last_check = now
            return new_events

    def get_totals(self):
        with engine.connect() as conn:
            return {
                "biz": conn.execute(text("SELECT count(*) FROM businesses")).scalar(),
                "users": conn.execute(text("SELECT count(*) FROM users")).scalar(),
                "stock": conn.execute(text("SELECT count(*) FROM stock")).scalar(),
                "sales": conn.execute(text("SELECT count(*) FROM sales")).scalar(),
            }

    async def run(self):
        print("\033[2J\033[H")  # Limpiar pantalla completa

        while True:
            # Obtener nuevos eventos
            events = self.fetch_new_events()
            if events:
                for e in events:
                    self.event_history.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] {e}"
                    )
                # Mantener solo los últimos N eventos
                self.event_history = self.event_history[-self.max_history :]

            totals = self.get_totals()

            # Renderizado del Dashboard
            print("\033[H")  # Mover cursor al inicio
            print("=" * 70)
            print(
                f" 🛰️  OMNICORE LIVE DB FEED | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print("=" * 70)

            # Fila de Totales
            print(
                f" TOTALES: Negocios: {totals['biz']} | Usuarios: {totals['users']} | Stock: {totals['stock']} | Ventas: {totals['sales']}"
            )
            print("-" * 70)

            # Feed de Eventos
            print(" EVENTOS RECIENTES:")
            if not self.event_history:
                print("  Esperando actividad en la base de datos...")
            else:
                for event in reversed(self.event_history):
                    print(f"  {event}")

            if len(self.event_history) >= self.max_history:
                print(
                    f"\n  ... {len(self.event_history) - self.max_history} eventos más ocultos."
                )

            print("\n" + "-" * 70)
            print(" Tip: Ejecuta el simulador en otra terminal para ver la magia ✨")
            print(" Ctrl+C para salir")

            await asyncio.sleep(1)


if __name__ == "__main__":
    feed = DbLiveFeed()
    try:
        asyncio.run(feed.run())
    except KeyboardInterrupt:
        print("\n👋 Monitor detenido.")
