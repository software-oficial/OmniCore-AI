import asyncio
import logging
import random
import uuid

import aiohttp

BASE_URL = "https://omnicore-ai-production.up.railway.app"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CompleteSimulator")


async def business_lifecycle(index):
    async with aiohttp.ClientSession() as session:
        # 1. ONBOARDING
        name = f"Empresa_Full_{index}_{uuid.uuid4().hex[:4]}"
        username = f"boss_{name}"

        logger.info(f"🚀 [{name}] Iniciando onboarding...")
        async with session.post(
            f"{BASE_URL}/api/admin/setup",
            json={"username": username, "password": "pass", "business_name": name},
        ) as r:
            if r.status != 200:
                logger.error(f"❌ [{name}] Error setup: {r.status}")
                return
            data = await r.json()
            bid = data["data"]["business_id"]
            token = data["data"]["token"]

        headers = {"Authorization": f"Bearer {token}"}
        logger.info(f"✅ [{name}] Onboarded. ID: {bid[:8]}")

        # 2. APERTURA DE CAJA
        # Es necesario abrir caja para que las ventas se registren correctamente en el flujo financiero
        monto_inicial = random.randint(500, 2000)
        logger.info(f"🔑 [{name}] Abriendo caja con ${monto_inicial}...")
        async with session.post(
            f"{BASE_URL}/api/business/cash_box/open",
            json={"monto_inicial": monto_inicial},
            headers=headers,
        ) as r:
            if r.status != 200:
                logger.warning(f"⚠️ [{name}] Falló apertura de caja: {await r.text()}")

        # 3. CARGA DE STOCK (Con precios variables)
        logger.info(f"📦 [{name}] Cargando catálogo de productos...")
        products = [
            {"sku": "PROD_1", "name": "Producto Premium", "price": 150.0},
            {"sku": "PROD_2", "name": "Producto Estándar", "price": 80.0},
            {"sku": "PROD_3", "name": "Producto Económico", "price": 30.0},
            {"sku": "PROD_4", "name": "Accesorio A", "price": 15.0},
            {"sku": "PROD_5", "name": "Accesorio B", "price": 12.0},
        ]

        for p in products:
            await session.post(
                f"{BASE_URL}/api/admin/stock/sync",
                json={
                    "business_id": bid,
                    "sku": p["sku"],
                    "data": {"name": p["name"], "price": p["price"], "quantity": 100},
                },
                headers=headers,
            )
        logger.info(f"✅ [{name}] Stock cargado ({len(products)} ítems).")

        # 4. SIMULACIÓN DE OPERACIONES (Ventas y Recargas)
        # Simulamos una jornada de trabajo
        for cycle in range(1, 11):  # 10 ciclos de actividad
            await asyncio.sleep(random.randint(2, 5))

            if random.random() > 0.3:
                # VENTA
                prod = random.choice(products)
                async with session.post(
                    f"{BASE_URL}/api/business/sales",
                    json={
                        "cliente": f"Cliente_{random.randint(1,100)}",
                        "items": [{"product_code": prod["sku"], "quantity": 1}],
                        "metodo_pago": "Efectivo",
                        "paga_con": prod["price"] + 20,
                    },
                    headers=headers,
                ) as r:
                    if r.status == 200:
                        logger.info(
                            f"💰 [{name}] VENDIÓ {prod['name']} (${prod['price']})"
                        )
                    else:
                        logger.warning(f"❌ [{name}] Error venta: {await r.text()}")
            else:
                # RECARGA DE STOCK
                prod = random.choice(products)
                await session.post(
                    f"{BASE_URL}/api/admin/stock/sync",
                    json={
                        "business_id": bid,
                        "sku": prod["sku"],
                        "data": {
                            "name": prod["name"],
                            "price": prod["price"],
                            "quantity": 50,
                        },
                    },
                    headers=headers,
                )
                logger.info(f"📦 [{name}] Recargó stock de {prod['name']}")

        # 5. CIERRE DE CAJA
        logger.info(f"🔒 [{name}] Cerrando caja y realizando arqueo...")
        async with session.post(
            f"{BASE_URL}/api/business/cash_box/close",
            json={"monto_real": 5000},  # Simulación de arqueo
            headers=headers,
        ) as r:
            if r.status == 200:
                logger.info(f"✅ [{name}] Caja cerrada exitosamente.")
            else:
                logger.warning(f"⚠️ [{name}] Error al cerrar caja: {await r.text()}")


async def main():
    # Simulamos 3 negocios operando en paralelo
    await asyncio.gather(*(business_lifecycle(i) for i in range(3)))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
