import asyncio
import random

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def run_simple_simulation():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        print("\n🚀 [1/3] REGISTRO DE DUEÑO (Email/Pass)...")
        email = f"dueno_{random.randint(1000, 9999)}@tienda.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )

        # Login
        resp_login = await client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        # 1.5 Register Business (New step needed)
        await client.post(
            "/api/business/register", json={"name": "Mi Tienda"}, headers=headers
        )

        print(f"✅ Login y Registro exitoso. UserID: {user_id}")

        print("\n📦 [2/3] CREACIÓN DE NEGOCIO Y STOCK...")
        prod_code = f"PROD_{random.randint(100, 999)}"
        resp = await client.post(
            "/api/business/products",
            json={
                "code": prod_code,
                "name": "Producto de Prueba",
                "price": 10.0,
                "quantity": 100,
                "category": "General",
                "is_weight": False,
            },
            headers=headers,
        )
        print(f"✅ Producto {prod_code}: {resp.status_code} - {resp.text[:100]}")

        print("\n💰 [3/3] OPERACIÓN DE VENTA...")
        resp = await client.post(
            "/api/business/sales",
            json={
                "cliente": "Cliente Final",
                "items": [{"product_code": prod_code, "quantity": 1}],
                "metodo_pago": "Efectivo",
                "paga_con": 50.0,
            },
            headers=headers,
        )
        print(f"✅ Venta procesada: {resp.status_code} - {resp.text[:100]}")


if __name__ == "__main__":
    asyncio.run(run_simple_simulation())
