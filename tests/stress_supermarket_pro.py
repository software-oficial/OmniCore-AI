import asyncio
import random

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def create_tenant(client, name):
    # 1. Register Owner
    email = f"{name}_{random.randint(1000, 9999)}@tienda.com"
    await client.post(
        "/api/auth/register", json={"email": email, "password": "password123"}
    )
    resp_login = await client.post(
        "/api/auth/login", json={"email": email, "password": "password123"}
    )
    user_id = resp_login.json()["data"]["user_id"]
    headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

    # 2. Register Business
    resp = await client.post(
        "/api/business/register", json={"name": name}, headers=headers
    )
    business_id = resp.json()["business_id"]
    return headers, business_id, name


async def run_stress_test():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        tenants = []
        for i in range(3):
            tenants.append(await create_tenant(client, f"Supermercado_{i}"))

        for headers, biz_id, name in tenants:
            print(f"\n--- Probando {name} (ID: {biz_id}) ---")

            # A. Crear Empleados (user.create_employee)
            for role in ["manager", "cashier_1", "cashier_2"]:
                resp = await client.post(
                    "/api/business/team",
                    json={
                        "email": f"{role}_{biz_id[:4]}@demo.com",
                        "password": "pass",
                        "role": role,
                    },
                    headers=headers,
                )
                print(f"✅ Empleado {role}: {resp.status_code}")

            # B. Compras/Stock (stock.add)
            prod_code = f"SKU_{random.randint(1000, 9999)}"
            resp = await client.post(
                "/api/business/products",
                json={
                    "code": prod_code,
                    "name": "Producto Bulk",
                    "price": 10.0,
                    "quantity": 500,
                    "category": "General",
                    "is_weight": False,
                },
                headers=headers,
            )
            print(f"✅ Stock cargado: {resp.status_code}")

            # C. Venta (venta.cobrar)
            resp = await client.post(
                "/api/business/sales",
                json={
                    "cliente": "ClienteStress",
                    "items": [{"product_code": prod_code, "quantity": 1}],
                    "metodo_pago": "Efectivo",
                    "paga_con": 50.0,
                },
                headers=headers,
            )
            print(f"✅ Venta procesada: {resp.status_code}")

        print("\n🎉 SIMULACIÓN MASIVA COMPLETA.")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
