import asyncio
import random

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def run_stress_test():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # Creamos 3 negocios simultáneos
        tenants = []
        for i in range(3):
            # 1. Onboarding
            resp = await client.post(
                "/api/agent/register",
                json={"name": f"Negocio_{i}", "platform_name": "TestMultiTenant"},
            )
            token = resp.json()["token"]

            # Obtener app_id
            resp_proj = await client.get(
                "/api/agent/projects", headers={"Authorization": f"Bearer {token}"}
            )
            app_id = resp_proj.json()[0]["id"]
            tenants.append({"token": token, "app_id": app_id, "name": f"Negocio_{i}"})
            print(f"✅ Registrado {tenants[-1]['name']} con AppID: {app_id}")

        # 2. Ejecutar matriz de comandos para cada tenant
        for tenant in tenants:
            headers = {
                "Authorization": f"Bearer {tenant['token']}",
                "X-App-ID": tenant["app_id"],
                "X-User-ID": "admin",
            }

            # A. Crear Empleado (Usando el comando correcto descubierto)
            emp_email = f"emp{random.randint(100, 999)}@demo.com"
            resp = await client.post(
                "/api/business/team",
                json={"email": emp_email, "password": "pass", "role": "cashier"},
                headers=headers,
            )
            print(f"[{tenant['name']}] ✅ Empleado {emp_email}: {resp.status_code}")

            # B. Cargar Stock
            prod_code = f"SKU_{random.randint(1000, 9999)}"
            resp = await client.post(
                "/api/business/products",
                json={
                    "code": prod_code,
                    "name": "Item",
                    "price": 10.0,
                    "quantity": 100,
                    "category": "General",
                    "is_weight": False,
                },
                headers=headers,
            )
            print(f"[{tenant['name']}] ✅ Producto {prod_code}: {resp.status_code}")

            # C. Venta Completa
            resp = await client.post(
                "/api/business/sales",
                json={
                    "cliente": "Cliente",
                    "items": [{"product_code": prod_code, "quantity": 1}],
                    "metodo_pago": "Efectivo",
                    "paga_con": 100.0,
                },
                headers=headers,
            )
            print(f"[{tenant['name']}] ✅ Venta: {resp.status_code}")

        print("\n🎉 STRESS TEST FINALIZADO.")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
