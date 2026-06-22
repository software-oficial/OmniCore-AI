import asyncio
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def simulate_business(biz_idx):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=90.0) as client:
        # 1. Registro de Dueño
        email = f"owner_{biz_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
        await client.post(
            "/api/auth/register", json={"email": email, "password": "password123"}
        )
        resp_login = await client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        user_id = resp_login.json()["data"]["user_id"]
        headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}

        # 2. Crear Negocio
        resp_reg = await client.post(
            "/api/business/register",
            json={"name": f"Supermercado_{biz_idx}"},
            headers=headers,
        )
        biz_id = resp_reg.json()["business_id"]
        headers["X-App-ID"] = biz_id

        print(f"✅ Negocio {biz_idx} creado: {biz_id}")

        # 3. Crear 3 Empleados
        for i in range(3):
            await client.post(
                "/api/business/team",
                json={
                    "email": f"emp_{biz_idx}_{i}@demo.com",
                    "password": "pass",
                    "role": "cashier",
                },
                headers=headers,
            )

        # 4. Cargar Inventario (3 Productos con precios distintos)
        products = [
            {
                "code": f"P1_{biz_idx}",
                "name": "Leche",
                "price": 1.5,
                "quantity": 100,
                "category": "Lácteos",
                "is_weight": False,
            },
            {
                "code": f"P2_{biz_idx}",
                "name": "Pan",
                "price": 2.5,
                "quantity": 50,
                "category": "Pan",
                "is_weight": False,
            },
            {
                "code": f"P3_{biz_idx}",
                "name": "Carne",
                "price": 15.0,
                "quantity": 20,
                "category": "Carnes",
                "is_weight": True,
            },
        ]
        for p in products:
            await client.post("/api/business/products", json=p, headers=headers)

        # 5. Ventas Mezcladas (Loop)
        for _ in range(5):
            # Venta aleatoria
            items = random.sample(products, k=random.randint(1, 3))
            sale_items = [
                {"product_code": p["code"], "quantity": random.randint(1, 2)}
                for p in items
            ]

            await client.post(
                "/api/business/sales",
                json={
                    "cliente": f"Cliente_{random.randint(1, 100)}",
                    "items": sale_items,
                    "metodo_pago": "Efectivo",
                    "paga_con": 500.0,
                },
                headers=headers,
            )

        print(f"🏁 Negocio {biz_idx} completado: 5 ventas procesadas con éxito.")


async def main():
    # Ejecutar 3 negocios en simultáneo
    await asyncio.gather(*(simulate_business(i) for i in range(3)))
    print("\n🎉 SIMULACIÓN FINALIZADA.")


if __name__ == "__main__":
    asyncio.run(main())
