import json
import uuid

import requests

# Ajustado para usar la URL de Railway
BASE_URL = "https://omnicore-ai-production.up.railway.app"
TEST_NAME = f"Negocio_{uuid.uuid4().hex[:6]}"


def log(message: str):
    print(f"[SIMULATION] {message}")


def run_simulation():
    session = requests.Session()

    # 1. Registro (Auto-aprovisiona infraestructura y despliega blueprints)
    log(f"Registrando negocio: {TEST_NAME}...")
    resp = session.post(
        f"{BASE_URL}/api/agent/register",
        json={"name": TEST_NAME, "platform_name": "TestPlatform"},
    )
    if resp.status_code != 200:
        log(f"Error registro: {resp.text}")
        return

    data = resp.json()
    token = data.get("token")
    biz_headers = {"Authorization": f"Bearer {token}"}
    log("Registro exitoso. Token obtenido.")

    # 2. Llenar Stock (Payload corregido según blueprint)
    log("Importando stock...")
    prod_payload = {
        "code": "PROD-001",
        "name": "Café Premium",
        "price": 5.0,
        "quantity": 50,
        "category": "Bebidas",
        "is_weight": False,
    }
    resp = session.post(
        f"{BASE_URL}/api/business/products", json=prod_payload, headers=biz_headers
    )
    log(f"Resultado stock: {resp.status_code} - {resp.text}")

    # 3. Realizar Venta
    log("Procesando venta...")
    sale_payload = {
        "items": [{"product_code": "PROD-001", "quantity": 2}],
        "cliente": "Cliente Final",
        "metodo_pago": "Efectivo",
        "paga_con": 20.0,
    }
    resp = session.post(
        f"{BASE_URL}/api/business/sales", json=sale_payload, headers=biz_headers
    )
    log(f"Resultado venta: {resp.status_code} - {resp.text}")

    # 4. Auditar
    log("Consultando auditoría...")
    resp = session.get(f"{BASE_URL}/api/business/audit", headers=biz_headers)
    log(f"Logs: {json.dumps(resp.json(), indent=2)}")

    log("--- Simulación finalizada correctamente ---")


if __name__ == "__main__":
    run_simulation()
