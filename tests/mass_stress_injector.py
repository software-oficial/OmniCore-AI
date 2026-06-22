import asyncio
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def setup_hierarchical_tenant(client, user_idx):
    try:
        # Registro Dueño
        email = f"owner_{user_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
        await client.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": email, "password": "password123"},
        )
        resp_login = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": "password123"},
        )

        if resp_login.status_code != 200:
            print(f"❌ Login failed for {email}: {resp_login.text}")
            return

        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        for biz_idx in range(2):
            # Crear Negocio
            resp_reg = await client.post(
                f"{BASE_URL}/api/business/register",
                json={"name": f"Negocio_{user_idx}_{biz_idx}"},
                headers=headers,
            )
            if resp_reg.status_code != 200:
                print(f"❌ Business registration failed: {resp_reg.text}")
                continue

            biz_id = resp_reg.json()["business_id"]
            biz_headers = headers.copy()
            biz_headers["X-App-ID"] = biz_id

            # Crear Empleados
            for i in range(3):
                await client.post(
                    f"{BASE_URL}/api/business/team",
                    json={
                        "email": f"emp_{user_idx}_{biz_idx}_{i}@demo.com",
                        "password": "pass",
                        "role": "cashier",
                    },
                    headers=biz_headers,
                )

            # Cargar Stock
            resp_prod = await client.post(
                f"{BASE_URL}/api/business/products",
                json={
                    "code": "PROD_A",
                    "name": "Producto A",
                    "price": 10.0,
                    "quantity": 1000,
                    "category": "General",
                    "is_weight": False,
                },
                headers=biz_headers,
            )
            if resp_prod.status_code != 200:
                print(f"❌ Product creation failed: {resp_prod.text}")
                continue

            # Pequeña pausa para asegurar la persistencia en la DB y evitar race conditions
            await asyncio.sleep(0.5)

            # Iniciar bucle de ventas
            asyncio.create_task(sales_loop(biz_headers, biz_id))
            print(
                f"✅ Tenant {user_idx} Biz {biz_idx} setup complete. Starting sales..."
            )
    except Exception as e:
        print(f"💥 Fatal error setting up tenant {user_idx}: {e}")


async def sales_loop(biz_headers, biz_id):
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        while True:
            try:
                resp = await client.post(
                    f"{BASE_URL}/api/business/sales",
                    json={
                        "cliente": "Cli",
                        "items": [{"product_code": "PROD_A", "quantity": 1}],
                        "metodo_pago": "Efectivo",
                        "paga_con": 50.0,
                    },
                    headers=biz_headers,
                )
                if resp.status_code >= 400:
                    print(
                        f"❌ Sale failed for {biz_id}: {resp.status_code} - {resp.text}"
                    )
            except Exception as e:
                print(f"⚠️ Connection error in sales_loop: {e}")
            await asyncio.sleep(random.uniform(0.5, 2.0))


async def main():
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(setup_hierarchical_tenant(client, i) for i in range(3)))
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
