import asyncio
import logging
import random
import uuid

import aiohttp

# Configuración
BASE_URL = "https://omnicore-ai-production.up.railway.app"
NUM_BUSINESSES = 10
SIM_NAME_PREFIX = "SIM_TEST_"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MassSimulation")


async def run_simulation():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(NUM_BUSINESSES):
            tasks.append(simulate_business_lifecycle(session, i))

        logger.info(
            f"🚀 Iniciando simulación masiva: {NUM_BUSINESSES} negocios simultáneos..."
        )
        results = await asyncio.gather(*tasks)
        logger.info(f"🎉 Simulación completada. Negocios procesados: {len(results)}")


async def simulate_business_lifecycle(session, index):
    suffix = uuid.uuid4().hex[:6]
    name = f"{SIM_NAME_PREFIX}{index}_{suffix}"

    # 1. Crear Negocio
    try:
        async with session.post(
            f"{BASE_URL}/api/admin/setup",
            json={
                "username": f"user_{name}",
                "password": "password123",
                "business_name": name,
                "plan": "PRO",
            },
        ) as resp:
            if resp.status != 200:
                logger.error(f"Fallo crear negocio {name}: {await resp.text()}")
                return False
            data = await resp.json()
            bid = data["data"]["business_id"]

            # 2. Agregar Empleado
            await session.post(
                f"{BASE_URL}/api/admin/employees/add",
                json={
                    "business_id": bid,
                    "username": f"emp_{name}",
                    "password": "password456",
                    "role": "EMPLOYEE",
                },
            )

            # 3. Simular Venta y Stock
            for _ in range(5):
                sku = f"SKU_{random.randint(1, 100)}"
                await session.post(
                    f"{BASE_URL}/api/admin/stock/sync",
                    json={
                        "business_id": bid,
                        "sku": sku,
                        "data": {"name": "Producto", "precio": random.random() * 100},
                    },
                )

            logger.info(f"✅ Negocio {name} (ID: {bid}) ciclo completado.")
            return True
    except Exception as e:
        logger.error(f"Error en ciclo {name}: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(run_simulation())
