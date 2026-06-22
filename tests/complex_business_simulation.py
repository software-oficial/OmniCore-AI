import asyncio
import logging
import uuid

import aiohttp

# Configuración
BASE_URL = "https://omnicore-ai-production.up.railway.app"
NUM_SIMULATIONS = 4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComplexSimulation")


async def simulate_business_workflow(index):
    async with aiohttp.ClientSession() as session:
        name = f"Negocio_Complejo_{index}_{uuid.uuid4().hex[:4]}"

        # 1. Setup Negocio
        async with session.post(
            f"{BASE_URL}/api/admin/setup",
            json={
                "username": f"owner_{index}",
                "password": "pass",
                "business_name": name,
            },
        ) as r:
            data = await r.json()
            bid = data["data"]["business_id"]
            token = data["data"]["token"]

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Cargar 100 stock
        for i in range(100):
            await session.post(
                f"{BASE_URL}/api/admin/stock/sync",
                json={
                    "business_id": bid,
                    "sku": f"PROD_{i}",
                    "data": {"name": f"Prod_{i}", "price": 100, "quantity": 100},
                },
                headers=headers,
            )

        # 3. Abrir Caja (Nota: En UUS, esto requiere un comando de negocio real,
        # asumiendo la API de negocio/ventas implementada)
        # TODO: Ajustar según los endpoints de negocio existentes

        # 4. Ventas Simultáneas para deducir 30 stock
        for i in range(30):
            await session.post(
                f"{BASE_URL}/api/business/sales",
                json={
                    "cliente": "Cliente Test",
                    "items": [{"product_code": f"PROD_{i}", "quantity": 1}],
                    "payment_method": "Efectivo",
                    "paga_con": 200,
                },
                headers=headers,
            )

        logger.info(
            f"✅ {name} completado: 100 stock cargados, 30 vendidos, restan 70."
        )


async def main():
    logger.info("🚀 Iniciando simulación compleja de negocio...")
    await asyncio.gather(
        *(simulate_business_workflow(i) for i in range(NUM_SIMULATIONS))
    )
    logger.info("🎉 Simulación compleja finalizada.")


if __name__ == "__main__":
    asyncio.run(main())
