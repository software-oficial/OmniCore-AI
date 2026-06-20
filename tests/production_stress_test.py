import uuid

import requests

BASE_URL = "https://omnicore-ai-production.up.railway.app"
TEST_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "SecurePassword123!"
# Using a valid agent_id (the owner_id of an existing app)
TEST_AGENT_ID = "419ba7cf-ed4a-4f5e-adcb-70dff559fde8"


def log(message: str, status: str = "INFO"):
    print(f"[{status}] {message}")


def test_production_lifecycle():
    session = requests.Session()

    # 1. Register
    log("Step 1: Registering test user...")
    reg_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    resp = session.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    if resp.status_code != 200:
        log(f"Registration failed: {resp.text}", "ERROR")
        return
    log("User registered successfully.")

    # 2. Login
    log("Step 2: Logging in...")
    login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    resp = session.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if resp.status_code != 200:
        log(f"Login failed: {resp.text}", "ERROR")
        return

    login_data = resp.json()
    # Extract user_id from the 'data' wrapper
    data = login_data.get("data", {})
    user_token = (
        data.get("user_id") or login_data.get("user_id") or login_data.get("token")
    )
    if not user_token:
        log(f"Login successful but no token found: {login_data}", "ERROR")
        return
    log(f"Logged in. User Token: {user_token[:10]}...")

    # 2.5 Get or Create Agent (Auto-provisioning happens on first project/token request usually,
    # but let's try to get the agent_id for THIS user)
    headers = {"Authorization": f"Bearer {user_token}"}
    log("Step 2.5: Checking for user's agent...")
    resp = session.get(f"{BASE_URL}/api/agent/me", headers=headers)

    current_agent_id = TEST_AGENT_ID  # Default fallback
    if resp.status_code == 200:
        current_agent_id = resp.json().get("agent_id")
        log(f"Found existing agent for user: {current_agent_id}")
    else:
        log(
            f"No agent found for user (Status: {resp.status_code}). Using fallback/global agent for testing."
        )

    # 3. Create API Token
    log(f"Step 3: Creating API Token for agent {current_agent_id}...")
    token_payload = {
        "agent_id": current_agent_id,
        "token_name": "StressTestToken",
        "mode": "PRODUCTION",
    }
    resp = session.post(
        f"{BASE_URL}/api/auth/tokens/create", json=token_payload, headers=headers
    )
    if resp.status_code != 200:
        log(f"Token creation failed: {resp.text}", "ERROR")
        # If it fails due to FK, it means the user doesn't have an agent and the fallback didn't work.
        return

    token_data = resp.json()
    # Extract token hash from the 'data' wrapper
    t_data = token_data.get("data", {})
    api_token = (
        t_data.get("api_token")
        or t_data.get("token")
        or t_data.get("token_hash")
        or token_data.get("token")
        or token_data.get("token_hash")
    )
    if not api_token:
        log(f"Token created but hash not found in response: {token_data}", "ERROR")
        return
    log(f"API Token created: {api_token[:10]}...")

    # 4. Business API Tests
    biz_headers = {"Authorization": f"Bearer {api_token}"}

    # 4.1 Credentials
    log("Step 4.1: Testing Credentials...")
    # List
    resp = session.get(f"{BASE_URL}/api/business/credentials", headers=biz_headers)
    log(f"List credentials status: {resp.status_code}")

    # Create
    cred_payload = {
        "account_name": "TestAcc",
        "provider": "test_provider",
        "api_key": "test_key_123",
        "secret": "test_secret_456",
        "is_default": False,
    }
    resp = session.post(
        f"{BASE_URL}/api/business/credentials", json=cred_payload, headers=biz_headers
    )
    if resp.status_code == 200:
        cred_id = resp.json().get("data", {}).get("id") or resp.json().get("id")
        log(f"Created credential: {cred_id}")

        # Delete
        resp = session.delete(
            f"{BASE_URL}/api/business/credentials/{cred_id}", headers=biz_headers
        )
        log(f"Deleted credential status: {resp.status_code}")
    else:
        log(f"Create credential failed: {resp.text}", "ERROR")

    # 4.2 Settings
    log("Step 4.2: Testing Settings...")
    resp = session.get(f"{BASE_URL}/api/business/settings", headers=biz_headers)
    log(f"Get settings status: {resp.status_code}")

    set_payload = {
        "key": "test_setting_key",
        "value": "test_value",
        "description": "test desc",
    }
    resp = session.patch(
        f"{BASE_URL}/api/business/settings", json=set_payload, headers=biz_headers
    )
    log(f"Update setting status: {resp.status_code}")

    # 4.3 Products
    log("Step 4.3: Testing Products...")
    resp = session.get(f"{BASE_URL}/api/business/products", headers=biz_headers)
    log(f"List products status: {resp.status_code}")

    prod_payload = {
        "code": f"PROD-{uuid.uuid4().hex[:4].upper()}",
        "name": "Stress Test Product",
        "price": 10.99,
        "stock": 100,
    }
    resp = session.post(
        f"{BASE_URL}/api/business/products", json=prod_payload, headers=biz_headers
    )
    if resp.status_code == 200:
        log(f"Created product: {prod_payload['code']}")
    else:
        log(f"Create product failed: {resp.text}", "ERROR")

    # 4.4 Sales
    log("Step 4.4: Testing Sales...")
    sale_payload = {
        "items": [{"code": prod_payload["code"], "quantity": 1}],
        "customer_name": "Test Customer",
        "total": 10.99,
    }
    resp = session.post(
        f"{BASE_URL}/api/business/sales", json=sale_payload, headers=biz_headers
    )
    log(f"Process sale status: {resp.status_code}")

    # 4.5 Audit
    log("Step 4.5: Testing Audit...")
    resp = session.get(f"{BASE_URL}/api/business/audit", headers=biz_headers)
    log(f"Get audit logs status: {resp.status_code}")

    # 5. Security / Edge Cases
    log("Step 5: Testing Security/Edge Cases...")

    # Unauthenticated request
    resp = session.get(f"{BASE_URL}/api/business/products")
    log(f"Unauthenticated request status (expected 401): {resp.status_code}")

    # Invalid token
    bad_headers = {"Authorization": "Bearer invalid_token_123"}
    resp = session.get(f"{BASE_URL}/api/business/products", headers=bad_headers)
    log(f"Invalid token request status (expected 401/400): {resp.status_code}")

    # Malformed payload
    resp = session.post(
        f"{BASE_URL}/api/business/products",
        json={"invalid": "data"},
        headers=biz_headers,
    )
    log(f"Malformed payload status (expected 400): {resp.status_code}")

    log("--- TEST SUITE COMPLETED ---")


if __name__ == "__main__":
    test_production_lifecycle()
