import asyncio
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def simulate_biz_realtime(biz_idx):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Registro e Login
        email = f"realtime_{biz_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )
        resp_login = await client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        # 2. Register Business
        resp_reg = await client.post(
            "/api/business/register", json={"name": f"Biz_{biz_idx}"}, headers=headers
        )
        biz_id = resp_reg.json()["business_id"]
        headers["X-App-ID"] = biz_id

        print(f"✅ Biz {biz_idx} activo.")

        # Ciclo de simulación
        for cycle in range(5):
            # A. Alternar Stock
            await client.post(
                "/api/business/products",
                json={
                    "code": "SKU_A",
                    "name": "Prod A",
                    "price": 10.0,
                    "quantity": random.randint(50, 200),
                    "category": "A",
                    "is_weight": False,
                },
                headers=headers,
            )

            # B. Ventas aleatorias
            await client.post(
                "/api/business/sales",
                json={
                    "cliente": "Cli",
                    "items": [
                        {"product_code": "SKU_A", "quantity": random.randint(1, 5)}
                    ],
                    "metodo_pago": "Efectivo",
                    "paga_con": 100.0,
                },
                headers=headers,
            )

            # C. Check stock
            res = await client.get("/api/business/products/SKU_A", headers=headers)
            stock = res.json().get("data", {}).get("quantity", 0)
            print(f"📊 Biz {biz_idx} [Ciclo {cycle}]: Stock actual {stock}")

            await asyncio.sleep(random.uniform(0.5, 2.0))

        print(f"🏁 Biz {biz_idx} finalizado.")


async def main():
    await asyncio.gather(*(simulate_biz_realtime(i) for i in range(3)))


if __name__ == "__main__":
    asyncio.run(main())
