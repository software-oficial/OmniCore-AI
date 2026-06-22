import asyncio
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def stress_cycle():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        email = f"user_{uuid.uuid4().hex[:4]}@tienda.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )
        resp_login = await client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        resp_reg = await client.post(
            "/api/business/register",
            json={"name": f"Biz_{random.randint(1,1000)}"},
            headers=headers,
        )
        biz_id = resp_reg.json()["business_id"]
        headers["X-App-ID"] = biz_id

        while True:
            try:
                await client.post(
                    "/api/business/products",
                    json={
                        "code": f"P{random.randint(1,100)}",
                        "name": "Item",
                        "price": 10.0,
                        "quantity": 100,
                        "category": "A",
                        "is_weight": False,
                    },
                    headers=headers,
                )
                await client.post(
                    "/api/business/sales",
                    json={
                        "cliente": "Cli",
                        "items": [
                            {"product_code": f"P{random.randint(1,100)}", "quantity": 1}
                        ],
                        "metodo_pago": "Efectivo",
                        "paga_con": 50.0,
                    },
                    headers=headers,
                )
                await asyncio.sleep(0.5)
            except Exception:
                await asyncio.sleep(1)


async def main():
    await asyncio.gather(*(stress_cycle() for _ in range(3)))


if __name__ == "__main__":
    asyncio.run(main())
