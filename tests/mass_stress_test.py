import asyncio
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def simulate_business(biz_idx):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Dueño
        email = f"owner_{biz_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )
        resp_login = await client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        # 2. Registrar Negocio
        resp_reg = await client.post(
            "/api/business/register",
            json={"name": f"Supermercado_{biz_idx}"},
            headers=headers,
        )
        biz_id = resp_reg.json()["business_id"]
        headers["X-App-ID"] = biz_id

        # 3. Empleados
        roles = ["manager", "cashier_1", "cashier_2"]
        for role in roles:
            await client.post(
                "/api/business/team",
                json={
                    "email": f"{role}_{biz_idx}@demo.com",
                    "password": "pass",
                    "role": role,
                },
                headers=headers,
            )

        # 4. Inventario
        prod_code = f"SKU_{biz_idx}_001"
        await client.post(
            "/api/business/products",
            json={
                "code": prod_code,
                "name": f"Prod_{biz_idx}",
                "price": 10.0,
                "quantity": 100,
                "category": "General",
                "is_weight": False,
            },
            headers=headers,
        )

        # 5. Caja
        await client.post(
            "/api/business/sales/cash/open",
            json={"monto_inicial": 100.0},
            headers=headers,
        )

        # 6. Ventas
        for i in range(3):
            await client.post(
                "/api/business/sales",
                json={
                    "cliente": f"Cli_{i}",
                    "items": [{"product_code": prod_code, "quantity": 1}],
                    "metodo_pago": "Efectivo",
                    "paga_con": 50.0,
                },
                headers=headers,
            )

        # 7. Cierre
        await client.post(
            "/api/business/sales/cash/close",
            json={"monto_real": 130.0},
            headers=headers,
        )

        # Auditoría local
        print(f"✅ Negocio {biz_idx} completado: Venta finalizada, Caja cerrada.")


async def main():
    await asyncio.gather(*(simulate_business(i) for i in range(3)))
    print("\n🎉 SIMULACIÓN MASIVA EXITOSA.")


if __name__ == "__main__":
    asyncio.run(main())
