import os
import time

from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:FXHFZRZSNRzmrcUMbfXVLGrMvOJYOaOW@nozomi.proxy.rlwy.net:34662/railway"
engine = create_engine(DB_URL)


def run_monitor():
    while True:
        start = time.time()
        with engine.connect() as conn:
            biz_count = conn.execute(text("SELECT COUNT(*) FROM apps")).scalar()
            sales_count = conn.execute(text("SELECT COUNT(*) FROM sales")).scalar()
            total_stock = conn.execute(
                text("SELECT SUM(quantity) FROM products")
            ).scalar()

        latency = (time.time() - start) * 1000
        os.system("cls" if os.name == "nt" else "clear")
        print(f"=== DB REAL-TIME MONITOR (Latencia: {latency:.2f}ms) ===")
        print(f"Negocios Totales: {biz_count}")
        print(f"Ventas Totales  : {sales_count}")
        print(f"Stock Global    : {total_stock}")
        time.sleep(1)


if __name__ == "__main__":
    run_monitor()
