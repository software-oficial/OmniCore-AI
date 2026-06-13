import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("GauntletTest")

BASE_URL = "http://localhost:8000"
# Token de prueba (Asumiendo que el sistema acepta tokens simples en modo test o que el registry está seedead)
# Usaremos el token de producción del agente seedead
TOKEN = "PRODUCTION_test_agent_001" 

def call_cmd(command, params=None):
    payload = {"command": command, "params": params or {}}
    res = requests.post(f"{BASE_URL}/api/gateway/execute", json=payload, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        data = res.json()
        if not data.get('success'):
            debug = data.get('debug_info')
            if debug:
                logger.error(f"🔍 DEBUG INFO for {command}:\n{debug}")
        return data
    except requests.exceptions.JSONDecodeError:
        logger.error(f"❌ NON-JSON RESPONSE received! Status: {res.status_code}")
        logger.error(f"Response Body: {res.text}")
        return {"success": False, "message": f"Server returned non-JSON response. Status: {res.status_code}", "error_code": "NON_JSON_RESPONSE"}

def run_gauntlet():
    logger.info("⚔️ STARTING THE GAUNTLET TEST (Full E2E Flow)")

    # 1. Stock: Crear Producto
    logger.info("\n--- Step 1: Inventory Setup ---")
    res = call_cmd("stock.add", {"code": "E2E_LAPTOP", "name": "Enterprise Laptop", "price": 1200.0, "quantity": 10, "category": "Hardware"})
    if res.get('success'):
        logger.info(f"✅ Product created: {res.get('message')}")
    else:
        logger.error(f"❌ Product failed: {res.get('message')}")
        return

    # 2. Stock: Verificar existencia
    logger.info("\n--- Step 2: Inventory Verification ---")
    res = call_cmd("stock.list", {"filter_text": "Enterprise"})
    if res.get('success') and res.get('data'):
        logger.info(f"✅ Product found in registry. Count: {len(res.get('data'))}")
    else:
        logger.error(f"❌ Product not found: {res.get('message')}")
        return

    # 3. Ventas: Procesar Venta
    logger.info("\n--- Step 3: Atomic Sale Process ---")
    res = call_cmd("sales.process", {
        "client_name": "Global Corp",
        "items": [{"code": "E2E_LAPTOP", "quantity": 1}],
        "payment_method": "CASH",
        "cash_box_id": 1,
        "paga_con": 1300.0
    })
    if res.get('success'):
        logger.info(f"✅ Sale processed! Vuelto: {res.get('data', {}).get('vuelto')}")
    else:
        logger.error(f"❌ Sale failed: {res.get('message')}")
        return

    # 4. Stock: Verificar descuento de stock
    logger.info("\n--- Step 4: Post-Sale Stock Check ---")
    res = call_cmd("stock.list", {"filter_text": "Enterprise"})
    # El laptop debería tener ahora 9 unidades
    product = res.get('data', [{}])[0]
    qty = product.get('quantity')
    if qty == 9:
        logger.info(f"✅ Stock correctly decremented to {qty}")
    else:
        logger.error(f"❌ Stock mismatch! Expected 9, got {qty}")
        return

    # 5. Seguridad: Intento de acción prohibida
    logger.info("\n--- Step 5: Security Boundary Check ---")
    # Intentar cerrar caja con token de AI (Simulado cambiando el token)
    ai_token = "LEARNING_test_agent_001"
    res = requests.post(f"{BASE_URL}/api/command", 
                        json={"command": "cash.close", "params": {"cash_box_id": 1, "actual_amount": 1300.0}}, 
                        headers={"Authorization": f"Bearer {ai_token}"})
    
    if not res.json().get('success') and res.json().get('error_code') == "ENTITY_RESTRICTION":
        logger.info("✅ Security check passed: AI Agent blocked from closing cash box.")
    else:
        logger.error(f"❌ Security breach! AI Agent was not blocked. Response: {res.json()}")
        return

    logger.info("\n🏆 GAUNTLET TEST COMPLETED SUCCESSFULLY! SYSTEM IS FULLY FUNCTIONAL.")

if __name__ == "__main__":
    run_gauntlet()
