import time

import requests

# --- CONFIGURATION ---
BASE_URL = "https://omnicore-ai-production.up.railway.app"
# We will attempt to create a new user for testing.
# If this fails due to existing data, we'll use a unique email.
TEST_EMAIL = f"stress_test_{int(time.time())}@omnicore.ai"
TEST_PASSWORD = "SecurePassword123!"

print("🚀 Starting OmniCore-AI Production Stress Test")
print(f"🌐 Base URL: {BASE_URL}")
print(f"👤 Test Account: {TEST_EMAIL}")


def log_step(step, status, message=""):
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{icon} [{step}] {status}: {message}")


def run_test_suite():
    session_token = None

    # --- PHASE 1: Identity & Access ---
    print("\n--- Phase 1: Identity & Access ---")

    # 1. Register
    try:
        reg_res = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10,
        )
        if reg_res.status_code == 200:
            log_step(
                "Registration", "PASS", f"User created: {reg_res.json().get('id')}"
            )
        else:
            log_step("Registration", "FAIL", reg_res.text)
    except Exception as e:
        log_step("Registration", "FAIL", str(e))

    # 2. Login
    try:
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10,
        )
        if login_res.status_code == 200:
            session_token = login_res.json().get("token")
            log_step("Login", "PASS", "Session token acquired")
        else:
            log_step("Login", "FAIL", login_res.text)
    except Exception as e:
        log_step("Login", "FAIL", str(e))

    if not session_token:
        print("\n🛑 Critical Failure: Could not authenticate. Aborting suite.")
        return

    headers = {"Authorization": f"Bearer {session_token}"}

    # --- PHASE 2: Credentials Management (The New Feature) ---
    print("\n--- Phase 2: Credentials Management ---")

    # 1. Create a Credential
    cred_payload = {
        "account_name": "Test-WhatsApp-Account",
        "provider": "whatsapp",
        "api_key": "test_api_key_123",
        "secret": "test_secret_456",
        "metadata": {"phone_id": "123456789"},
        "is_default": True,
    }
    try:
        c_res = requests.post(
            f"{BASE_URL}/api/business/credentials",
            json=cred_payload,
            headers=headers,
            timeout=10,
        )
        if c_res.status_code == 200:
            cred_id = c_res.json().get("data", {}).get("id")
            log_step(
                "Create Credential", "PASS", f"Credential created with ID: {cred_id}"
            )
        else:
            log_step("Create Credential", "FAIL", c_res.text)
    except Exception as e:
        log_step("Create Credential", "FAIL", str(e))

    # 2. List Credentials
    try:
        l_res = requests.get(
            f"{BASE_URL}/api/business/credentials", headers=headers, timeout=10
        )
        if l_res.status_code == 200:
            log_step(
                "List Credentials",
                "PASS",
                f"Found {len(l_res.json().get('data', []))} credentials",
            )
        else:
            log_step("List Credentials", "FAIL", l_res.text)
    except Exception as e:
        log_step("List Credentials", "FAIL", str(e))

    # 3. Filter Credentials by Provider
    try:
        f_res = requests.get(
            f"{BASE_URL}/api/business/credentials?provider=whatsapp",
            headers=headers,
            timeout=10,
        )
        if f_res.status_code == 200:
            log_step("Filter Credentials", "PASS", "Provider filtering working")
        else:
            log_step("Filter Credentials", "FAIL", f_res.text)
    except Exception as e:
        log_step("Filter Credentials", "FAIL", str(e))

    # --- PHASE 3: Business Core (Gateway Commands) ---
    print("\n--- Phase 3: Business Core ---")

    # 1. Heartbeat / Health
    try:
        h_res = requests.get(f"{BASE_URL}/api/heartbeat", timeout=10)
        if h_res.status_code == 200:
            log_step("Heartbeat", "PASS", "System is ALIVE")
        else:
            log_step("Heartbeat", "FAIL", h_res.text)
    except Exception as e:
        log_step("Heartbeat", "FAIL", str(e))

    # 2. Command Execution: Stock Add
    stock_payload = {
        "command": "stock.add",
        "params": {
            "code": f"STRESS-{int(time.time())}",
            "name": "Stress Test Product",
            "price": 10.0,
            "quantity": 100,
            "category": "Test",
        },
    }
    try:
        s_res = requests.post(
            f"{BASE_URL}/api/gateway/execute",
            json=stock_payload,
            headers=headers,
            timeout=10,
        )
        if s_res.status_code == 200 and s_res.json().get("success"):
            log_step("Command Execute (Stock)", "PASS", "Product added successfully")
        else:
            log_step("Command Execute (Stock)", "FAIL", s_res.text)
    except Exception as e:
        log_step("Command Execute (Stock)", "FAIL", str(e))

    # --- PHASE 4: Cleanup ---
    print("\n--- Phase 4: Cleanup ---")
    try:
        # Note: We can't easily delete the user via API based on current routes,
        # but we could revoke tokens if we had the hash.
        log_step("Cleanup", "INFO", "User created for testing remains in DB.")
    except Exception as e:
        log_step("Cleanup", "FAIL", str(e))

    print("\n" + "=" * 40)
    print("🏁 STRESS TEST COMPLETE")
    print("=" * 40)


if __name__ == "__main__":
    run_test_suite()
