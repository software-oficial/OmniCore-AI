import uuid

import requests

# URL de producción
BASE_URL = "https://omnicore-ai-production.up.railway.app"
TEST_NAME = f"STRESS_TEST_{uuid.uuid4().hex[:6]}"


def log(message: str):
    print(f"[STRESS_TEST] {message}")


def run_complex_simulation():
    session = requests.Session()

    log("=== INICIANDO SIMULACIÓN DE NEGOCIO COMPLETA ===")
    log(f"Nombre del Negocio: {TEST_NAME}")

    # 1. REGISTRO DEL ADMINISTRADOR
    log("\n[1/7] Registrando Administrador...")
    register_payload = {"name": TEST_NAME, "platform_name": "StressTest"}
    try:
        resp = session.post(f"{BASE_URL}/api/agent/register", json=register_payload)
        if resp.status_code != 200:
            log(f"❌ Error en registro: {resp.text}")
            return

        admin_auth = resp.json()
        admin_token = admin_auth["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        log("✅ Admin registrado. Token listo.")
    except Exception as e:
        log(f"❌ Error en registro: {e}")
        return

    # 2. CREACIÓN DE EMPLEADOS
    log("\n[2/7] Creando equipo de trabajo...")
    vendedor_payload = {
        "username": "juan_vendedor",
        "password": "password123",
        "role": "employee",
    }
    v_resp = session.post(
        f"{BASE_URL}/api/business/team", json=vendedor_payload, headers=admin_headers
    )
    if v_resp.status_code == 200:
        log("✅ Empleado 'juan_vendedor' creado.")
    else:
        log(f"❌ Error creando empleado: {v_resp.text}")
        return

    # 3. CONFIGURACIÓN DE INVENTARIO
    log("\n[3/7] Cargando stock inicial...")
    product_code = f"PROD-{uuid.uuid4().hex[:4].upper()}"
    prod_payload = {
        "code": product_code,
        "name": "Producto Premium Test",
        "price": 500.0,
        "quantity": 20,
        "category": "Pruebas",
        "is_weight": False,
    }
    p_resp = session.post(
        f"{BASE_URL}/api/business/products", json=prod_payload, headers=admin_headers
    )
    if p_resp.status_code != 200:
        log(f"❌ Error cargando stock: {p_resp.text}")
        return
    log(f"✅ Producto {product_code} cargado (Qty: 20).")

    # 4. APERTURA DE CAJA
    log("\n[4/7] Abriendo caja con monto inicial $1000...")
    cash_resp = session.post(
        f"{BASE_URL}/api/business/cash_box/open",
        json={"monto_inicial": 1000.0},
        headers=admin_headers,
    )
    if cash_resp.status_code != 200:
        log(f"❌ Error abriendo caja: {cash_resp.text}")
        return
    log("✅ Caja abierta.")

    # 5. SIMULACIÓN DE VENTA
    log("\n[5/7] Ejecutando venta de 2 unidades (Efectivo)...")
    sale_payload = {
        "cliente": "Cliente Test",
        "items": [{"product_code": product_code, "quantity": 2}],
        "payment_method": "Efectivo",
        "paga_con": 2000.0,
    }
    s_resp = session.post(
        f"{BASE_URL}/api/business/sales", json=sale_payload, headers=admin_headers
    )
    if s_resp.status_code != 200:
        log(f"❌ Error en venta: {s_resp.text}")
        return
    log("✅ Venta exitosa. Total: $1000.0")

    # 6. VERIFICACIÓN DE INTEGRIDAD
    log("\n[6/7] Verificando integridad (Stock y Caja)...")
    prod_check = session.get(
        f"{BASE_URL}/api/business/products/{product_code}", headers=admin_headers
    )
    if prod_check.status_code == 200:
        qty = prod_check.json().get("data", {}).get("quantity")
        log(f"✅ Verificación Stock: {qty} (Esperado: 18)")
        if qty != 18:
            log(f"⚠️ ERROR: Stock incorrecto: {qty}")
    else:
        log(f"❌ Error consultando producto: {prod_check.text}")

    cash_check = session.get(
        f"{BASE_URL}/api/business/cash_box/status", headers=admin_headers
    )
    if cash_check.status_code == 200:
        cash_data = cash_check.json().get("data", {})
        log(
            f"✅ Verificación Caja: Ventas Efectivo: ${cash_data.get('ventas_efectivo')}"
        )
    else:
        log(f"❌ Error consultando caja: {cash_check.text}")

    # 7. CIERRE DE CAJA
    log("\n[7/7] Cerrando caja con arqueo de $2000...")
    close_resp = session.post(
        f"{BASE_URL}/api/business/cash_box/close",
        json={"monto_real": 2000.0},
        headers=admin_headers,
    )
    if close_resp.status_code == 200:
        log("✅ Caja cerrada y balanceada correctamente.")
        log(f"Resumen cierre: {close_resp.json().get('data')}")
    else:
        log(f"❌ Error cerrando caja: {close_resp.text}")

    log("\n=== SIMULACIÓN COMPLETADA CON ÉXITO ===")


if __name__ == "__main__":
    run_complex_simulation()
