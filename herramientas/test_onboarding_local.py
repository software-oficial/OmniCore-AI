import requests
import time
import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("E2ETest")

BASE_URL = "http://localhost:8000"

def run_tests():
    logger.info("🚀 Starting End-to-End Local Validation...")
    
    try:
        # 1. Test Registration
        logger.info("Testing Registration Flow...")
        reg_payload = {"name": "LocalTestAgent", "platform_name": "LocalTestApp"}
        response = requests.post(f"{BASE_URL}/api/agent/register", json=reg_payload)
        
        if response.status_code != 200:
            logger.error(f"❌ Registration failed: {response.text}")
            return False
        
        data = response.json()
        agent_id = data.get("agent_id")
        app_id = data.get("app_id")
        token = data.get("token")
        
        logger.info(f"✅ Registered: Agent={agent_id}, App={app_id}, Token={token}")

        # 2. Test API Manifest
        logger.info("Testing Manifest Access...")
        manifest_res = requests.get(f"{BASE_URL}/api/agent/manifest")
        if manifest_res.status_code != 200:
            logger.error("❌ Manifest access failed")
            return False
        logger.info("✅ Manifest retrieved successfully.")

        # 3. Test Command Execution (Learning Mode)
        logger.info("Testing Command Execution (stock.list)...")
        cmd_payload = {"command": "stock.list", "params": {}}
        headers = {"Authorization": f"Bearer {token}"}
        exec_res = requests.post(f"{BASE_URL}/api/gateway/execute", json=cmd_payload, headers=headers)
        
        if exec_res.status_code != 200:
            logger.error(f"❌ Command execution failed: {exec_res.text}")
            return False
        
        res_data = exec_res.json()
        if not res_data.get("success"):
            logger.error(f"❌ Command returned failure: {res_data}")
            return False
        
        logger.info(f"✅ Command executed: {res_data.get('message')}")

        # 4. Test Static Files
        logger.info("Checking Static Files...")
        page_res = requests.get(f"{BASE_URL}/static/index.html")
        if page_res.status_code != 200:
            logger.error("❌ Index page not found")
            return False
        logger.info("✅ Frontend Panel is accessible.")

        logger.info("🎉 ALL E2E TESTS PASSED SUCCESSFULLY!")
        return True

    except Exception as e:
        logger.error(f"❌ Unexpected error during testing: {e}")
        return False

if __name__ == "__main__":
    # Start server in background
    logger.info("Starting local server...")
    server_proc = subprocess.Popen(
        ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to boot
    time.sleep(5)
    
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    finally:
        server_proc.terminate()
        logger.info("Local server terminated.")
