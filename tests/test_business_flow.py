import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.api.main import app

# --- Configuration ---
# Using SQLite for fast, isolated testing of business logic.
# Note: In production, OmniCore uses Postgres, but the business logic
# uses SQLAlchemy, so SQLite is sufficient for validating flow.
TEST_DB_URL = "sqlite:///test_omnicore_biz.db"
engine = create_engine(TEST_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

# Mock Master Key for Admin/Dev access
os.environ["OMNICORE_MASTER_KEY"] = "test-master-key"
HEADERS = {"Authorization": "test-master-key"}


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """
    Initialize the database schema for the business flow test.
    Translates Postgres blueprints to SQLite compatible SQL.
    """
    with SessionLocal() as session:
        # --- STOCK BLUEPRINT (SQLite compatible) ---
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
                quantity INTEGER NOT NULL DEFAULT 0,
                category VARCHAR(100),
                is_weight BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code VARCHAR(50) NOT NULL,
                amount INTEGER NOT NULL,
                reason VARCHAR(100) DEFAULT 'MANUAL',
                user_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # --- SALES BLUEPRINT (SQLite compatible) ---
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name VARCHAR(255) NOT NULL,
                client_email VARCHAR(255),
                total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                payment_method VARCHAR(50),
                payment_reference VARCHAR(255),
                paga_con DECIMAL(12, 2) DEFAULT 0.00,
                vuelto DECIMAL(12, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_code VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(12, 2) NOT NULL,
                subtotal DECIMAL(12, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sale_id) REFERENCES sales(id)
            )
        """
            )
        )
        session.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS cash_box (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abierta BOOLEAN DEFAULT FALSE,
                efectivo_inicial DECIMAL(12, 2) DEFAULT 0.00,
                ventas_efectivo DECIMAL(12, 2) DEFAULT 0.00,
                ventas_digital DECIMAL(12, 2) DEFAULT 0.00,
                monto_cierre_real DECIMAL(12, 2),
                hora_apertura TIMESTAMP,
                hora_cierre TIMESTAMP
            )
        """
            )
        )

        # Initialize Cash Box
        session.execute(text("INSERT INTO cash_box (id, abierta) VALUES (1, 0)"))
        session.commit()


def test_full_business_flow():
    """
    End-to-End test: Stock Load -> Open Cash Box -> Sale -> Verify Stock & Cash
    """
    # 1. Load Stock
    # Command: stock.add
    stock_payload = {
        "code": "PROD-001",
        "name": "Café Gourmet 250g",
        "price": 1500.0,
        "quantity": 10,
        "category": "Bebidas",
        "is_weight": False,
    }
    res_stock = client.post(
        "/api/commands/execute",
        json={"command": "stock.add", "params": stock_payload},
        headers=HEADERS,
    )

    assert res_stock.status_code == 200
    assert res_stock.json()["success"] is True

    # 2. Open Cash Box
    # Command: caja.abrir
    cash_payload = {"monto_inicial": 5000.0}
    res_cash = client.post(
        "/api/commands/execute",
        json={"command": "caja.abrir", "params": cash_payload},
        headers=HEADERS,
    )

    assert res_cash.status_code == 200
    assert res_cash.json()["success"] is True

    # 3. Process Sale
    # Command: venta.cobrar
    sale_payload = {
        "cliente": "Cliente Prueba",
        "items": [{"product_code": "PROD-001", "quantity": 2}],
        "metodo_pago": "Efectivo",
        "paga_con": 4000.0,
        "alias": None,
    }
    res_sale = client.post(
        "/api/commands/execute",
        json={"command": "venta.cobrar", "params": sale_payload},
        headers=HEADERS,
    )

    assert res_sale.status_code == 200
    assert res_sale.json()["success"] is True

    sale_data = res_sale.json()["data"]
    total_sale = sale_data["total"]
    vuelto_sale = sale_data["vuelto"]

    assert total_sale == 3000.0  # 1500 * 2
    assert vuelto_sale == 1000.0  # 4000 - 3000

    # 4. Verify Final State
    with SessionLocal() as session:
        # Verify Stock
        prod = session.execute(
            text("SELECT quantity FROM products WHERE code = 'PROD-001'")
        ).scalar()
        assert prod == 8  # 10 - 2

        # Verify Cash Box
        cash = (
            session.execute(text("SELECT ventas_efectivo FROM cash_box WHERE id = 1"))
            .mappings()
            .first()
        )
        assert float(cash["ventas_efectivo"]) == 3000.0


if __name__ == "__main__":
    # Run via pytest manually if needed
    pytest.main([__file__])
