import asyncio
import os
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"

# Shared state for the dashboard
state = {}


async def setup_tenant(client, user_idx):
    # 1. Register User (Dueño)
    email = f"user_{user_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
    await client.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    resp_login = await client.post(
        f"{BASE_URL}/api/auth/login", json={"email": email, "password": "password123"}
    )
    user_id = resp_login.json()["data"]["user_id"]
    headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

    businesses = []
    for biz_idx in range(2):
        # 2. Register Business
        resp_reg = await client.post(
            f"{BASE_URL}/api/business/register",
            json={"name": f"Negocio_{user_idx}_{biz_idx}"},
            headers=headers,
        )
        biz_id = resp_reg.json()["business_id"]

        # 3. Create Employees
        biz_headers = headers.copy()
        biz_headers["X-App-ID"] = biz_id
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

        # 4. Inventory
        products = [f"P{i:03d}" for i in range(50)]
        for code in products:
            await client.post(
                f"{BASE_URL}/api/business/products",
                json={
                    "code": code,
                    "name": f"Prod_{code}",
                    "price": random.uniform(1, 100),
                    "quantity": 1000,
                    "category": "General",
                    "is_weight": False,
                },
                headers=biz_headers,
            )

        state[f"{user_idx}_{biz_idx}"] = {
            "name": f"N_{user_idx}_{biz_idx}",
            "sales": 0,
            "last_action": "Init",
            "employees": 3,
        }
        businesses.append((biz_headers, biz_id, products))

    return businesses


async def business_loop(user_idx, biz_idx, biz_headers, products):
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                code = random.choice(products)
                await client.post(
                    f"{BASE_URL}/api/business/sales",
                    json={
                        "cliente": "Cli",
                        "items": [
                            {"product_code": code, "quantity": random.randint(1, 5)}
                        ],
                        "metodo_pago": "Efectivo",
                        "paga_con": 500.0,
                    },
                    headers=biz_headers,
                )
                state[f"{user_idx}_{biz_idx}"]["sales"] += 1
                state[f"{user_idx}_{biz_idx}"]["last_action"] = f"Venta {code}"
            except Exception:
                state[f"{user_idx}_{biz_idx}"]["last_action"] = "Error"
            await asyncio.sleep(random.uniform(0.5, 2.0))


async def dashboard():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== OMNICORE-AI LIVE MONITOR (3 Usuarios, 2 Negocios C/U) ===")
        print(f"{'Negocio':<15} | {'Ventas':<10} | {'Empleados'} | {'Ultima Acción'}")
        print("-" * 65)
        for key, s in state.items():
            print(
                f"{s['name']:<15} | {s['sales']:<10} | {s['employees']:<9} | {s['last_action']}"
            )
        await asyncio.sleep(1)


async def main():
    async with httpx.AsyncClient() as client:
        tenants = [await setup_tenant(client, i) for i in range(3)]
        tasks = []
        for u_idx, biz_list in enumerate(tenants):
            for b_idx, (h, b, p) in enumerate(biz_list):
                tasks.append(business_loop(u_idx, b_idx, h, p))
        tasks.append(dashboard())
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Simulación detenida.")
