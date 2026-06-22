import json
import logging
import uuid

from sqlalchemy import text

from src.core.system.universal_admin_service import universal_admin_service
from src.infrastructure.db.core_db_manager import core_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestUUS")


def test_uus_onboarding():
    logger.info("🚀 Iniciando prueba de onboarding UUS...")

    # 1. Setup Business + Owner
    username = f"user_{uuid.uuid4().hex[:6]}"
    res = universal_admin_service.setup_business_and_owner(
        username=username, password_hash="hashed_pass", business_name="Test Empresa"
    )

    assert res.success, f"Fallo al crear empresa: {res.message}"
    data = res.data
    bid = data["business_id"]
    logger.info(f"✅ Empresa creada: {bid} para usuario {data['user_id']}")

    # 2. Agregar Empleado
    res_emp = universal_admin_service.add_employee(
        business_id=bid, username=f"emp_{uuid.uuid4().hex[:6]}", password_hash="pass"
    )
    assert res_emp.success, "Fallo al agregar empleado"
    logger.info("✅ Empleado agregado.")

    # 3. Sync Stock Flexible
    stock_data = {"name": "Laptop", "price": 1000, "talla": "XL", "color": "Negro"}
    res_stock = universal_admin_service.sync_stock(
        business_id=bid, sku="LAP001", data=stock_data
    )
    assert res_stock.success, "Fallo al sincronizar stock"
    logger.info("✅ Stock sincronizado con JSON flexible.")

    # 4. Verificar DB
    with core_db_manager.get_session() as session:
        # Verificar stock
        row = session.execute(
            text("SELECT data FROM stock WHERE business_id = :bid AND sku = 'LAP001'"),
            {"bid": bid},
        ).fetchone()

        assert row is not None
        stored_data = json.loads(row[0])
        assert stored_data["talla"] == "XL"
        logger.info(
            "✅ Verificación de DB exitosa: JSON flexible guardado correctamente."
        )

    logger.info("🎉 ¡Prueba de integración UUS completada con éxito!")


if __name__ == "__main__":
    test_uus_onboarding()
