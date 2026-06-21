import asyncio
import uuid

import httpx

# CONFIGURATION
BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def run_simulation():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("\n🚀 [1/5] REGISTRO DE CUENTA DE DUEÑO...")

        # 1. Registro
        onboard_payload = {
            "name": f"Dueño_{uuid.uuid4().hex[:6]}",
            "platform_name": "Negocio_SaaS_Demo",
        }
        resp = await client.post("/api/agent/register", json=onboard_payload)
        if resp.status_code != 200:
            print(f"❌ Registro fallido: {resp.text}")
            return

        token = resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Obtener app_id (Cuenta de Negocio)
        resp_proj = await client.get("/api/agent/projects", headers=headers)
        projects = resp_proj.json()
        if not projects:
            print("❌ No se encontró la cuenta de negocio (app_id).")
            return

        app_id = projects[0]["id"]
        print(f"✅ Cuenta de negocio vinculada: {app_id}")

        print("\n📦 [2/5] CARGA DE PRODUCTOS...")
        prod_code = "LECHE01"
        prod = {
            "code": prod_code,
            "name": "Leche",
            "price": 1.5,
            "quantity": 100,
            "category": "Lácteos",
            "is_weight": False,
        }
        # El endpoint de productos debe tener acceso a la sesión vinculada a app_id
        resp = await client.post("/api/business/products", json=prod, headers=headers)
        print(f"✅ Producto {prod_code}: {resp.status_code}")

        print("\n💰 [3/5] PROCESAR VENTA...")
        sale_payload = {
            "cliente": "Cliente Prueba",
            "items": [{"product_code": prod_code, "quantity": 1}],
            "metodo_pago": "Efectivo",
            "paga_con": 5.0,
        }
        resp = await client.post(
            "/api/business/sales", json=sale_payload, headers=headers
        )
        print(f"✅ Venta: {resp.status_code} - {resp.text[:100]}")

        print("\n🎉 SIMULACIÓN FINALIZADA.")


if __name__ == "__main__":
    asyncio.run(run_simulation())
