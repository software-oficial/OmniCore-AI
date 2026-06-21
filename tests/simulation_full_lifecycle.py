import asyncio
import uuid

import httpx

# CONFIGURATION
BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def run_simulation():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        print("\n🚀 [1/6] REGISTRO DE DUEÑO (Onboarding)...")
        resp = await client.post(
            "/api/agent/register",
            json={
                "name": f"Super_{uuid.uuid4().hex[:6]}",
                "platform_name": "Negocio_Full_Sim",
            },
        )
        token = resp.json()["token"]
        # Need to get app_id for headers
        resp_proj = await client.get(
            "/api/agent/projects", headers={"Authorization": f"Bearer {token}"}
        )
        app_id = resp_proj.json()[0]["id"]

        headers = {
            "Authorization": f"Bearer {token}",
            "X-App-ID": app_id,
            "X-User-ID": "admin",
        }
        print(f"✅ Dueño registrado. AppID: {app_id}")

        print("\n👥 [2/6] CREANDO EMPLEADOS...")
        employees = [
            {"email": "ana.manager@demo.com", "password": "pass", "role": "manager"},
            {"email": "pedro.cajero@demo.com", "password": "pass", "role": "cashier"},
            {"email": "lucia.cajero@demo.com", "password": "pass", "role": "cashier"},
        ]
        for emp in employees:
            resp = await client.post("/api/business/team", json=emp, headers=headers)
            print(f"✅ Empleado {emp['email']}: {resp.status_code}")

        print("\n📦 [3/6] ABASTECIMIENTO (5 Productos)...")
        products = [
            {
                "code": f"P{i}",
                "name": f"Prod {i}",
                "price": 10.0 * i,
                "quantity": 100,
                "category": "General",
                "is_weight": False,
            }
            for i in range(1, 6)
        ]
        for prod in products:
            resp = await client.post(
                "/api/business/products", json=prod, headers=headers
            )
            print(f"✅ {prod['name']}: {resp.status_code}")

        print("\n💰 [4/6] PROCESANDO VENTAS MEZCLADAS...")
        for i in range(1, 6):
            sale_payload = {
                "cliente": f"Cliente {i}",
                "items": [{"product_code": f"P{i}", "quantity": i}],
                "metodo_pago": "Efectivo",
                "paga_con": 100.0,
            }
            resp = await client.post(
                "/api/business/sales", json=sale_payload, headers=headers
            )
            print(
                f"✅ Venta {i}: {resp.status_code} - {resp.json().get('message', '')}"
            )

        print("\n📑 [5/6] AUDITORÍA...")
        resp = await client.get("/api/business/audit", headers=headers)
        logs = resp.json().get("data", [])
        print(f"✅ Total eventos registrados: {len(logs)}")
        for log in logs[-5:]:
            print(f"   - [{log.get('command')}] {log.get('status')}")

        print("\n🎉 SIMULACIÓN COMPLETA.")


if __name__ == "__main__":
    asyncio.run(run_simulation())
