import requests
import json
import uuid
import time
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("OmniCoreAudit")

BASE_URL = "http://localhost:8000"

def test_request(endpoint, method="POST", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "POST":
            res = requests.post(url, json=data, headers=headers)
        else:
            res = requests.get(url, headers=headers)
        
        return res.json()
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return {"success": False, "message": str(e)}

def run_audit():
    logger.info("🚀 Starting OmniCore-AI Full-Cycle Audit...")

    # 1. Simulate Developer Onboarding (Infrastructure Setup)
    # In a real scenario, we'd call an API. Here we simulate the registry setup.
    # Since we can't call a 'register' API yet, we assume the internal DB is ready.
    # For the purpose of this test, we will use the LEARNING tokens provided by TokenManager
    # because our Registry expects valid agent_ids.
    
    # MOCKING A TOKEN (Since TokenManager uses mode_hash)
    # We'll use a PRODUCTION token to test the real flow.
    # We assume the internal registry has been seeded with this agent for the test.
    dev_token = "PRODUCTION_test_agent_001" 
    ai_token = "LEARNING_test_agent_001"

    logger.info("\n--- Step 1: Manifest Discovery ---")
    manifest = test_request("/api/agent/manifest", method="GET")
    logger.info(f"Manifest retrieved: {manifest.get('ontology')}")

    logger.info("\n--- Step 2: Stock Operations (PRODUCTION) ---")
    # Add Product
    res = test_request("/api/command", data={
        "command": "stock.add",
        "params": {"code": "PROD_TEST", "name": "Audit Laptop", "price": 1000.0, "quantity": 50, "category": "Tech"}
    }, token=dev_token)
    logger.info(f"Add Product: {res.get('message')}")

    # List Products
    res = test_request("/api/command", data={
        "command": "stock.list",
        "params": {"filter_text": "Audit"}
    }, token=dev_token)
    logger.info(f"List Products Success: {res.get('success')}")

    logger.info("\n--- Step 3: Sales Process (Atomic Transaction) ---")
    res = test_request("/api/command", data={
        "command": "sales.process",
        "params": {
            "client_name": "Test Customer",
            "items": [{"code": "PROD_TEST", "quantity": 2}],
            "payment_method": "CASH",
            "cash_box_id": 1,
            "paga_con": 2100.0
        }
    }, token=dev_token)
    
    if res:
        msg = res.get('message', 'No message')
        vuelto = res.get('data', {}).get('vuelto', 'N/A') if res.get('data') else 'N/A'
        logger.info(f"Sale Processed: {msg} | Change: {vuelto}")
    else:
        logger.error("Sale Process failed: Response is None")

    logger.info("\n--- Step 4: Governance Validation (The Shield) ---")
    # Test 1: AI Agent attempting to close cash box (Should be DENIED_ENTITY)
    res = test_request("/api/command", data={
        "command": "cash.close",
        "params": {"cash_box_id": 1, "actual_amount": 2100.0}
    }, token=ai_token)
    logger.info(f"AI closing cash box: {res.get('message')} | Code: {res.get('error_code')}")
    if res.get('error_code') == "ENTITY_RESTRICTION":
        logger.info("✅ SUCCESS: AI Agent blocked from critical financial action.")

    # Test 2: Low Tier attempting a PRO feature (Should be TIER_ACCESS_DENIED)
    # (Assuming test_agent_001 is set to FREE in DB)
    res = test_request("/api/command", data={
        "command": "cash.open",
        "params": {"cash_box_id": 1, "initial_amount": 100.0}
    }, token=dev_token)
    logger.info(f"Free Tier opening cash: {res.get('message')} | Code: {res.get('error_code')}")

    logger.info("\n--- Step 5: Learning Mode Simulation ---")
    res = test_request("/api/command", data={
        "command": "stock.add",
        "params": {"code": "SNDBOX", "name": "Sandbox Item", "price": 10.0, "quantity": 1}
    }, token=ai_token)
    logger.info(f"Learning Mode Result: {res.get('message')}")

    logger.info("\n🚀 Audit Complete.")

if __name__ == "__main__":
    run_audit()
