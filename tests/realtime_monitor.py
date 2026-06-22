import asyncio
import random
import uuid

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def setup_business(client, biz_idx):
    email = f"owner_{biz_idx}_{uuid.uuid4().hex[:4]}@tienda.com"
    await client.post(
        "/api/auth/register", json={"email": email, "password": "password123"}
    )
    resp_login = await client.post(
        "/api/auth/login", json={"email": email, "password": "password123"}
    )
    user_id = resp_login.json()["data"]["user_id"]
    headers = {"Authorization": f"Bearer {user_id}", "X-User-ID": user_id}
    resp_reg = await client.post(
        "/api/business/register", json={"name": f"Negocio_{biz_idx}"}, headers=headers
    )
    biz_id = resp_reg.json()["business_id"]
    headers["X-App-ID"] = biz_id
    # Create products
    for p in ["Leche", "Pan", "Carne"]:
        await client.post(
            "/api/business/products",
            json={
                "code": f"{p}_{biz_idx}",
                "name": p,
                "price": random.uniform(1, 20),
                "quantity": 100,
                "category": "General",
                "is_weight": False,
            },
            headers=headers,
        )
    print(f"✅ Negocio {biz_idx} (ID: {biz_id}) listo.")
    return headers, biz_id


async def business_loop(biz_idx, headers, biz_id):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print(f"🚀 Iniciando bucle en caliente para Negocio {biz_idx}")
        while True:
            action = random.choice(["sale", "stock", "audit"])
            try:
                if action == "sale":
                    await client.post(
                        "/api/business/sales",
                        json={
                            "cliente": "Cli",
                            "items": [
                                {"product_code": f"Leche_{biz_idx}", "quantity": 1}
                            ],
                            "metodo_pago": "Efectivo",
                            "paga_con": 50.0,
                        },
                        headers=headers,
                    )
                    print(f"💰 Biz {biz_idx} | Venta registrada")
                elif action == "stock":
                    await client.post(
                        "/api/business/products",
                        json={
                            "code": f"Pan_{biz_idx}",
                            "name": "Pan",
                            "price": 2.5,
                            "quantity": 1,
                            "category": "Pan",
                            "is_weight": False,
                        },
                        headers=headers,
                    )
                    print(f"📦 Biz {biz_idx} | Stock actualizado")
                else:
                    await client.get(
                        f"/api/business/products/Leche_{biz_idx}", headers=headers
                    )
                    print(f"📊 Biz {biz_idx} | Auditoría de stock OK")
            except Exception as e:
                print(f"❌ Biz {biz_idx} | Error: {e}")
            await asyncio.sleep(random.uniform(1, 3))


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        tenants = [await setup_business(client, i) for i in range(3)]
        await asyncio.gather(
            *(business_loop(i, h, b) for i, (h, b) in enumerate(tenants))
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Simulación detenida.")
