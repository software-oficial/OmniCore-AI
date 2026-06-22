import asyncio
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def verify_persistence():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Onboarding
        email = f"audit_{uuid.uuid4().hex[:6]}@demo.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "pass"}
        )
        token = (
            await client.post(
                "/api/auth/login", json={"email": email, "password": "pass"}
            )
        ).json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {token}", "X-User-ID": token}

        # 2. Register Business
        resp_biz = await client.post(
            "/api/business/register", json={"name": "AuditStore"}, headers=headers
        )
        business_id = resp_biz.json()["business_id"]
        print(f"✅ Negocio creado: {business_id}")

        # 3. Add Product
        prod_code = "TEST001"
        await client.post(
            "/api/business/products",
            json={
                "code": prod_code,
                "name": "Item Audit",
                "price": 10.0,
                "quantity": 100,
                "category": "Audit",
                "is_weight": False,
            },
            headers=headers,
        )

        # VERIFICACIÓN 1: ¿Existe el producto?
        prod_get = await client.get(
            f"/api/business/products/{prod_code}", headers=headers
        )
        print(f"🔍 Producto existe en DB: {prod_get.status_code == 200}")
        if prod_get.status_code == 200:
            print(f"   Stock inicial: {prod_get.json()['data']['quantity']}")

        # 4. Venta
        await client.post(
            "/api/business/sales",
            json={
                "cliente": "AuditClient",
                "items": [{"product_code": prod_code, "quantity": 10}],
                "metodo_pago": "Efectivo",
                "paga_con": 200.0,
            },
            headers=headers,
        )

        # VERIFICACIÓN 2: ¿Descontó stock?
        prod_get_final = await client.get(
            f"/api/business/products/{prod_code}", headers=headers
        )
        final_stock = prod_get_final.json()["data"]["quantity"]
        print(f"🔍 Stock tras venta (esperado 90): {final_stock}")

        # VERIFICACIÓN 3: ¿Auditó?
        audit_get = await client.get("/api/business/audit", headers=headers)
        logs = audit_get.json().get("data", [])
        print(f"🔍 Eventos en auditoría: {len(logs)}")
        for log in logs:
            print(f"   - {log['command']} | {log['status']}")


if __name__ == "__main__":
    asyncio.run(verify_persistence())
