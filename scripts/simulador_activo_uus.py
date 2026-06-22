import asyncio
import logging
import random
import uuid

import aiohttp

BASE_URL = "https://omnicore-ai-production.up.railway.app"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ActiveSimulator")


async def active_worker(index):
    async with aiohttp.ClientSession() as session:
        # Onboarding
        name = f"Negocio_Activo_{index}_{uuid.uuid4().hex[:4]}"
        username = f"owner_{name}"
        async with session.post(
            f"{BASE_URL}/api/admin/setup",
            json={
                "username": username,
                "password": "pass",
                "business_name": name,
            },
        ) as r:
            if r.status != 200:
                logger.error(
                    f"Error HTTP al crear negocio {name}: {r.status} - {await r.text()}"
                )
                return False
            data = await r.json()
            if not data.get("success"):
                logger.error(
                    f"Error lógico al crear negocio {name}: {data.get('message', 'Error desconocido')}"
                )
                return False
            bid = data["data"]["business_id"]
            token = data["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"🚀 {name} activo. Inicializando stock base...")

        # --- FASE DE INICIALIZACIÓN: Asegurar que hay stock para vender ---
        for i in range(1, 6):
            await session.post(
                f"{BASE_URL}/api/admin/stock/sync",
                json={
                    "business_id": bid,
                    "sku": f"PROD_{i}",
                    "data": {"name": f"Producto {i}", "price": 100.0, "quantity": 50},
                },
                headers=headers,
            )
        logger.info(f"📦 {name} stock base cargado. Iniciando operaciones...")

        while True:
            # Acción aleatoria: cargar stock o vender
            if random.random() > 0.4:
                # Venta
                prod_code = f"PROD_{random.randint(1, 5)}"
                async with session.post(
                    f"{BASE_URL}/api/business/sales",
                    json={
                        "cliente": "Cliente Activo",
                        "items": [
                            {
                                "product_code": prod_code,
                                "quantity": 1,
                            }
                        ],
                        "metodo_pago": "Efectivo",
                        "paga_con": 200,
                    },
                    headers=headers,
                ) as r:
                    res_text = await r.text()
                    if r.status == 200:
                        logger.info(f"💰 {name} vendió {prod_code}.")
                    else:
                        logger.warning(
                            f"❌ {name} falló venta {prod_code}: {r.status} - {res_text}"
                        )
            else:
                # Cargar stock adicional
                prod_code = f"PROD_{random.randint(1, 10)}"
                await session.post(
                    f"{BASE_URL}/api/admin/stock/sync",
                    json={
                        "business_id": bid,
                        "sku": prod_code,
                        "data": {"name": "Prod Extra", "price": 100.0, "quantity": 10},
                    },
                    headers=headers,
                )
                logger.info(f"📦 {name} recargó {prod_code}.")

            await asyncio.sleep(random.randint(2, 5))


async def main():
    await asyncio.gather(*(active_worker(i) for i in range(3)))


if __name__ == "__main__":
    asyncio.run(main())
