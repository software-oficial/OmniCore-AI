import asyncio
import logging
import random

import aiohttp

BASE_URL = "https://omnicore-ai-production.up.railway.app"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ActiveSimulator")


async def active_worker(index):
    async with aiohttp.ClientSession() as session:
        # Onboarding
        name = f"Negocio_Activo_{index}"
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

        logger.info(f"🚀 {name} activo.")

        while True:
            # Acción aleatoria: cargar stock o vender
            if random.random() > 0.3:
                # Venta
                await session.post(
                    f"{BASE_URL}/api/business/sales",
                    json={
                        "cliente": "Cliente Activo",
                        "items": [
                            {
                                "product_code": f"PROD_{random.randint(1,10)}",
                                "quantity": 1,
                            }
                        ],
                        "payment_method": "Efectivo",
                        "paga_con": 200,
                    },
                    headers=headers,
                )
                logger.info(f"💰 {name} vendió.")
            else:
                # Cargar stock
                await session.post(
                    f"{BASE_URL}/api/admin/stock/sync",
                    json={
                        "business_id": bid,
                        "sku": f"PROD_{random.randint(1,10)}",
                        "data": {"name": "Prod", "price": 100, "quantity": 10},
                    },
                    headers=headers,
                )
                logger.info(f"📦 {name} cargó stock.")

            await asyncio.sleep(random.randint(1, 3))


async def main():
    await asyncio.gather(*(active_worker(i) for i in range(3)))


if __name__ == "__main__":
    asyncio.run(main())
