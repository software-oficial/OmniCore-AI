import json
import os
from typing import Any, Dict, Optional

import requests

# Configuración desde variables de entorno o valores por defecto
API_BASE_URL = os.getenv("OMNICORE_API_URL", "http://localhost:8000/api")
AUTH_TOKEN = os.getenv("OMNICORE_TOKEN", "")

headers = {"Authorization": f"Bearer {AUTH_TOKEN}", "Content-Type": "application/json"}


def log_request(method: str, endpoint: str, payload: Any = None):
    print(f"\n--- 🚀 {method} {endpoint} ---")
    if payload:
        print(f"Payload: {json.dumps(payload, indent=2)}")


def log_response(response: requests.Response):
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"Response: {response.text}")
    print("-" * 40)


def test_endpoint(method: str, endpoint: str, data: Optional[Dict] = None):
    url = f"{API_BASE_URL}{endpoint}"
    log_request(method, endpoint, data)

    try:
        if method == "GET":
            res = requests.get(url, headers=headers)
        elif method == "POST":
            res = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            res = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            res = requests.delete(url, headers=headers)
        else:
            print(f"Método {method} no soportado.")
            return None

        log_response(res)
        return res
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None


def run_full_workflow():
    print("=== INICIANDO FLUJO DE PRUEBAS E2E OMNICORE ===")

    # 1. Verificar Token / Perfil
    print("\n[1/4] Verificando autenticación...")
    # Usamos /business/team como probe de acceso ya que sabemos que existe
    if test_endpoint("GET", "/business/team").status_code == 401:
        print("❌ ERROR: Token inválido o ausente. Configura OMNICORE_TOKEN.")
        return

    # 2. Gestión de Equipo (Crear usuario y asignar rol)
    print("\n[2/4] Probando Gestión de Equipo...")
    new_user = {
        "username": "test_worker_01",
        "password": "password123",
        "role": "employee",
        "platforms": ["Stock", "Pagos"],
    }
    test_endpoint("POST", "/business/team", new_user)

    # 3. Carga de Stock
    print("\n[3/4] Probando Carga de Stock...")
    # Simulamos un payload de importación (basado en el endpoint /import/execute)
    stock_data = {
        "source": "manual_test",
        "items": [
            {
                "sku": "PROD-001",
                "name": "Producto Test 1",
                "quantity": 100,
                "price": 15.50,
            },
            {
                "sku": "PROD-002",
                "name": "Producto Test 2",
                "quantity": 50,
                "price": 25.00,
            },
        ],
    }
    test_endpoint("POST", "/import/execute", stock_data)

    # 4. Verificación de Productos y Ventas
    print("\n[4/4] Verificando Productos Finales...")
    test_endpoint("GET", "/products")

    print("\n=== FLUJO COMPLETADO ===")


if __name__ == "__main__":
    if not AUTH_TOKEN:
        print(
            "⚠️  ADVERTENCIA: OMNICORE_TOKEN no configurado. Las peticiones fallarán con 401."
        )

    run_full_workflow()
