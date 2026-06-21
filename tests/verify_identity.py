import asyncio

import httpx

BASE_URL = "https://omnicore-ai-production.up.railway.app"


async def check_onboarding():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Register
        resp = await client.post(
            "/api/agent/register", json={"name": "Test", "platform_name": "Test"}
        )
        token = resp.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check Agent
        resp_me = await client.get("/api/agent/me", headers=headers)
        print(f"🕵️ Agente: {resp_me.json()}")

        # Check Projects
        resp_proj = await client.get("/api/agent/projects", headers=headers)
        print(f"📂 Proyectos: {resp_proj.json()}")


asyncio.run(check_onboarding())
