import uuid

import requests

# URL de producción proporcionada por el usuario
BASE_URL = "https://omnicore-ai-production.up.railway.app"
TEST_NAME = f"AUDIT_TEST_{uuid.uuid4().hex[:6]}"


def log(message: str):
    print(f"[AUDIT_FLOW] {message}")


def run_audit_simulation():
    session = requests.Session()

    log("--- INICIANDO AUDITORÍA INTEGRAL DE FLUJO ---")
    log(f"Negocio de prueba: {TEST_NAME}")

    # 1. REGISTRO DE AGENTE/NEGOCIO
    # Esto nos da el token que contiene el app_id necesario para las operaciones
    log("Paso 1: Registrando nuevo agente/negocio...")
    register_payload = {"name": TEST_NAME, "platform_name": "Audit_Script"}
    try:
        resp = session.post(f"{BASE_URL}/api/agent/register", json=register_payload)
        if resp.status_code != 200:
            log(f"❌ ERROR en Registro: {resp.status_code} - {resp.text}")
            return

        auth_data = resp.json()
        token = auth_data.get("token")
        if not token:
            log("❌ ERROR: No se recibió token en el registro.")
            return

        headers = {"Authorization": f"Bearer {token}"}
        log("✅ Registro exitoso. Token obtenido.")
    except Exception as e:
        log(f"❌ ERROR de conexión en Registro: {e}")
        return

    # 2. CREACIÓN DE PRODUCTO (Testing el Fix de app_id)
    log("Paso 2: Creando producto (Validando Fix de app_id)...")
    product_code = f"AUDIT-{uuid.uuid4().hex[:4].upper()}"
    product_payload = {
        "code": product_code,
        "name": "Producto de Auditoría Pro",
        "price": 150.0,
        "quantity": 100,
        "category": "Auditoría",
        "is_weight": False,
    }

    try:
        resp = session.post(
            f"{BASE_URL}/api/business/products", json=product_payload, headers=headers
        )
        if resp.status_code != 200:
            log(f"❌ ERROR al crear producto: {resp.status_code} - {resp.text}")
            log(
                "Nota: Si ves NotNullViolation, el fix no se ha desplegado correctamente."
            )
            return

        log(f"✅ Producto creado con éxito: {product_code}")
    except Exception as e:
        log(f"❌ ERROR de conexión en creación de producto: {e}")
        return

    # 3. VERIFICACIÓN DE STOCK INICIAL
    log("Paso 3: Verificando stock inicial...")
    try:
        resp = session.get(
            f"{BASE_URL}/api/business/products/{product_code}", headers=headers
        )
        if resp.status_code != 200:
            log(f"❌ ERROR al consultar producto: {resp.status_code} - {resp.text}")
            return

        prod_data = resp.json().get("data", {})
        current_qty = prod_data.get("quantity")
        log(
            f"✅ Verificación: Stock actual de {product_code} es {current_qty} (Esperado: 100)"
        )

        if current_qty != 100:
            log(
                f"⚠️ ALERTA: Cantidad inesperada. Se esperaba 100, se obtuvo {current_qty}"
            )
    except Exception as e:
        log(f"❌ ERROR al verificar stock: {e}")
        return

    # 4. REALIZAR VENTA (Consumo de Stock)
    log("Paso 4: Realizando venta de 10 unidades...")
    # Nota: El payload de venta depende de la implementación de 'venta.cobrar'
    # Basado en los logs anteriores, parece que espera un objeto con items o similar.
    # Intentamos con una estructura común de venta.
    sale_payload = {"items": [{"code": product_code, "quantity": 10}], "total": 1500.0}

    try:
        resp = session.post(
            f"{BASE_URL}/api/business/sales", json=sale_payload, headers=headers
        )
        if resp.status_code != 200:
            log(f"❌ ERROR en la venta: {resp.status_code} - {resp.text}")
            log("Revisando si el error es por el formato del payload de venta...")
            return

        log(f"✅ Venta procesada con éxito: {resp.json().get('message')}")
    except Exception as e:
        log(f"❌ ERROR de conexión en venta: {e}")
        return

    # 5. VERIFICACIÓN FINAL (Stock y Auditoría)
    log("Paso 5: Verificación final de integridad...")

    # 5a. Verificar Stock restante
    try:
        resp = session.get(
            f"{BASE_URL}/api/business/products/{product_code}", headers=headers
        )
        if resp.status_code == 200:
            final_qty = resp.json().get("data", {}).get("quantity")
            log(f"✅ Stock final tras venta: {final_qty} (Esperado: 90)")
            if final_qty == 90:
                log("🌟 ¡FLUJO DE STOCK CORRECTO!")
            else:
                log(
                    f"❌ ERROR: Stock inconsistente. Se esperaba 90, se obtuvo {final_qty}"
                )
        else:
            log(f"❌ ERROR al verificar stock final: {resp.status_code}")
    except Exception as e:
        log(f"❌ ERROR en verificación de stock final: {e}")

    # 5b. Verificar Logs de Auditoría
    try:
        resp = session.get(f"{BASE_URL}/api/business/audit", headers=headers)
        if resp.status_code == 200:
            logs = resp.json().get("data", [])
            log(f"✅ Se encontraron {len(logs)} registros en la auditoría.")
            # Buscamos si hay menciones a nuestro producto o comando
            found_audit = any(product_code in str(log_entry) for log_entry in logs)
            if found_audit:
                log("✅ El movimiento de auditoría está registrado.")

            else:
                log(
                    "⚠️ Advertencia: No se detectaron logs específicos de este producto en la auditoría."
                )
        else:
            log(f"❌ ERROR al consultar auditoría: {resp.status_code}")
    except Exception as e:
        log(f"❌ ERROR al consultar auditoría: {e}")

    log("--- AUDITORÍA FINALIZADA ---")


if __name__ == "__main__":
    run_audit_simulation()
