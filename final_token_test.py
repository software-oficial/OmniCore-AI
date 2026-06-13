import requests
import json

API_BASE = "http://localhost:8000/api"
USER_EMAIL = "tester_final@omnicore.ai"
USER_PASS = "Password_Final_2026!"
AGENT_ID = "00000000-0000-0000-0000-000000000002"

def test():
    print("🚀 --- FINAL TOKEN INTEGRATION TEST ---")
    
    # 1. Register
    print("\nStep 1: Registering user...")
    reg = requests.post(f"{API_BASE}/auth/register", json={"email": USER_EMAIL, "password": USER_PASS})
    print(f"Register Response: {reg.status_code}")

    # 2. Login
    print("\nStep 2: Logging in...")
    login = requests.post(f"{API_BASE}/auth/login", json={"email": USER_EMAIL, "password": USER_PASS})
    user_id = login.json()["data"]["user_id"]
    print(f"Authenticated User ID: {user_id}")

    # 3. Learning Token
    print("\nStep 3: Creating LEARNING token...")
    l_res = requests.post(f"{API_BASE}/auth/tokens/create", 
        headers={"Authorization": f"Bearer {user_id}"},
        json={"agent_id": AGENT_ID, "token_name": "Learning_Test", "mode": "LEARNING"})
    l_token = l_res.json()["data"]["api_token"]
    print(f"Learning Token: {l_token}")

    # 4. Production Token
    print("\nStep 4: Creating PRODUCTION token...")
    p_res = requests.post(f"{API_BASE}/auth/tokens/create", 
        headers={"Authorization": f"Bearer {user_id}"},
        json={"agent_id": AGENT_ID, "token_name": "Prod_Test", "mode": "PRODUCTION"})
    p_token = p_res.json()["data"]["api_token"]
    print(f"Production Token: {p_token}")

    # 5. Test Learning
    print("\nStep 5: Testing LEARNING token access...")
    res_l = requests.post(f"{API_BASE}/gateway/execute", 
        headers={"Authorization": f"Bearer {l_token}"},
        json={"command": "stock.list", "params": {}})
    print(f"Learning Result: {res_l.json()['success']} - {res_l.json().get('message')}")

    # 6. Test Production
    print("\nStep 6: Testing PRODUCTION token access...")
    res_p = requests.post(f"{API_BASE}/gateway/execute", 
        headers={"Authorization": f"Bearer {p_token}"},
        json={"command": "stock.list", "params": {}})
    print(f"Production Result: {res_p.json()['success']} - {res_p.json().get('message')}")

if __name__ == "__main__":
    test()
