import asyncio
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def audit_tenant(biz_idx):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Register & Login
        email = f"audit_{biz_idx}_{uuid.uuid4().hex[:4]}@demo.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )
        resp_login = await client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        # 2. Register Business
        resp_biz = await client.post(
            "/api/business/register", json={"name": f"Audit_{biz_idx}"}, headers=headers
        )
        biz_id = resp_biz.json()["business_id"]
        headers["X-App-ID"] = biz_id

        # 3. Add Product (Initial 100)
        prod_code = f"SKU_{biz_idx}"
        await client.post(
            "/api/business/products",
            json={
                "code": prod_code,
                "name": "Item",
                "price": 10.0,
                "quantity": 100,
                "category": "A",
                "is_weight": False,
            },
            headers=headers,
        )

        # 4. Open Cash (100)
        await client.post(
            "/api/business/sales/cash/open",
            json={"monto_inicial": 100.0},
            headers=headers,
        )

        # 5. Sell 10
        await client.post(
            "/api/business/sales",
            json={
                "cliente": "Cli",
                "items": [{"product_code": prod_code, "quantity": 10}],
                "metodo_pago": "Efectivo",
                "paga_con": 200.0,
            },
            headers=headers,
        )

        # --- EMPIRICAL VERIFICATION ---
        print(f"\n🔍 [AUDITORÍA {biz_idx}]")

        # Check Stock
        stock_resp = await client.get(
            f"/api/business/products/{prod_code}", headers=headers
        )
        stock = stock_resp.json()["data"]["quantity"]
        print(f"  - Stock (Esperado 90): {stock} -> {'✅' if stock == 90 else '❌'}")

        # Check Cash
        cash_resp = await client.get("/api/business/sales/cash/status", headers=headers)
        cash_data = cash_resp.json()["data"]
        ventas = float(cash_data["ventas_efectivo"])
        print(
            f"  - Ventas (Esperado 100): {ventas} -> {'✅' if ventas == 100 else '❌'}"
        )

        # Check Employees
        # Note: If no employees, this is expected if we didn't add them.
        # Adding one to verify:
        await client.post(
            "/api/business/team",
            json={
                "email": f"emp_{biz_idx}@demo.com",
                "password": "pass",
                "role": "manager",
            },
            headers=headers,
        )
        emp_list = await client.get("/api/business/team", headers=headers)
        print(
            f"  - Empleados creados: {len(emp_list.json()['data'])} -> {'✅' if len(emp_list.json()['data']) > 0 else '❌'}"
        )


async def main():
    await asyncio.gather(*(audit_tenant(i) for i in range(3)))


if __name__ == "__main__":
    asyncio.run(main())
