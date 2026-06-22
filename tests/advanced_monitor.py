import asyncio
import os
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"

# Shared state for the dashboard
state = {}


async def setup_tenant(client, biz_idx):
    email = f"realtime_{biz_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
    await client.post(
        "/api/auth/register", json={"email": email, "password": "password123"}
    )
    resp_login = await client.post(
        "/api/auth/login", json={"email": email, "password": "password123"}
    )
    user_id = resp_login.json()["data"]["user_id"]
    headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

    resp_reg = await client.post(
        "/api/business/register", json={"name": f"Negocio_{biz_idx}"}, headers=headers
    )
    biz_id = resp_reg.json()["business_id"]
    headers["X-App-ID"] = biz_id

    # 100 Products
    products = []
    for i in range(100):
        code = f"P{i:03d}"
        await client.post(
            "/api/business/products",
            json={
                "code": code,
                "name": f"Prod_{i}",
                "price": random.uniform(10, 100),
                "quantity": 1000,
                "category": "General",
                "is_weight": False,
            },
            headers=headers,
        )
        products.append(code)

    state[biz_idx] = {
        "name": f"Negocio_{biz_idx}",
        "sales": 0,
        "last_action": "Init",
        "stock": 100000,
    }
    return headers, biz_id, products


async def business_loop(biz_idx, headers, products):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        while True:
            # Random Action
            action = random.choice(["sale", "stock"])
            try:
                if action == "sale":
                    code = random.choice(products)
                    await client.post(
                        "/api/business/sales",
                        json={
                            "cliente": "Cli",
                            "items": [
                                {"product_code": code, "quantity": random.randint(1, 5)}
                            ],
                            "metodo_pago": "Efectivo",
                            "paga_con": 500.0,
                        },
                        headers=headers,
                    )
                    state[biz_idx]["sales"] += 1
                    state[biz_idx]["last_action"] = f"Venta {code}"
                else:
                    code = random.choice(products)
                    await client.post(
                        "/api/business/products",
                        json={
                            "code": code,
                            "name": "Prod",
                            "price": 10.0,
                            "quantity": 50,
                            "category": "General",
                            "is_weight": False,
                        },
                        headers=headers,
                    )
                    state[biz_idx]["last_action"] = f"Stock {code}"
            except Exception:
                pass
            await asyncio.sleep(random.uniform(0.1, 0.5))


async def dashboard():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== OMNICORE-AI BUSINESS DASHBOARD (REAL-TIME) ===")
        print(f"{'Negocio':<15} | {'Ventas':<10} | {'Ultima Acción':<20}")
        print("-" * 50)
        for idx, s in state.items():
            print(f"{s['name']:<15} | {s['sales']:<10} | {s['last_action']:<20}")
        await asyncio.sleep(1)


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        tenants = [await setup_tenant(client, i) for i in range(3)]
        tasks = [business_loop(i, h, p) for i, (h, b, p) in enumerate(tenants)]
        tasks.append(dashboard())
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
