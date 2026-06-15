import requests
import json
import time

API_BASE = "http://localhost:8000/api"
USER_EMAIL = "final_test@omnicore.ai"
USER_PASS = "Secure_Final_Pass_2026!"
AGENT_NAME = "FinalTestAgent"
PLATFORM_NAME = "FinalTestPlatform"

def test():
    print("🚀 --- OMNICORE TOKEN FINAL VALIDATION ---")
    
    # 1. Register User
    print("\nStep 1: Registering user...")
    reg = requests.post(f"{API_BASE}/auth/register", json={"email": USER_EMAIL, "password": USER_PASS})
    if reg.status_code != 200:
        print(f"❌ Register failed: {reg.text}")
        return
    print("✅ User registered.")

    # 2. Login
    print("\nStep 2: Logging in...")
    login = requests.post(f"{API_BASE}/auth/login", json={"email": USER_EMAIL, "password": USER_PASS})
    user_id = login.json()["data"]["user_id"]
    print(f"✅ Authenticated. User ID: {user_id}")

    # 3. Register Agent (REQUIRED for Production Tokens)
    print("\nStep 3: Registering Agent to DB...")
    agent_reg = requests.post(f"{API_BASE}/agent/register", json={
        "name": AGENT_NAME, 
        "platform_name": PLATFORM_NAME
    })
    if agent_reg.status_code != 200:
        print(f"❌ Agent registration failed: {agent_reg.text}")
        return
    agent_data = agent_reg.json()
    agent_id = agent_data["agent_id"]
    print(f"✅ Agent registered. Agent ID: {agent_id}")

    # 4. Create LEARNING Token
    print("\nStep 4: Creating LEARNING token...")
    l_res = requests.post(f"{API_BASE}/auth/tokens/create", 
        headers={"Authorization": f"Bearer {user_id}"},
        json={"agent_id": agent_id, "token_name": "Learn_Token", "mode": "LEARNING"})
    l_token = l_res.json()["data"]["api_token"]
    print(f"✅ Learning Token: {l_token}")

    # 5. Create PRODUCTION Token
    print("\nStep 5: Creating PRODUCTION token...")
    p_res = requests.post(f"{API_BASE}/auth/tokens/create", 
        headers={"Authorization": f"Bearer {user_id}"},
        json={"agent_id": agent_id, "token_name": "Prod_Token", "mode": "PRODUCTION"})
    p_token = p_res.json()["data"]["api_token"]
    print(f"✅ Production Token: {p_token}")

    # 6. Test LEARNING Token
    print("\nStep 6: Testing LEARNING token in Gateway...")
    res_l = requests.post(f"{API_BASE}/gateway/execute", 
        headers={"Authorization": f"Bearer {l_token}"},
        json={"command": "stock.list", "params": {}})
    print(f"Result: {'✅ SUCCESS' if res_l.json()['success'] else '❌ FAILED'} - {res_l.json().get('message')}")

    # 7. Test PRODUCTION Token
    print("\nStep 7: Testing PRODUCTION token in Gateway...")
    res_p = requests.post(f"{API_BASE}/gateway/execute", 
        headers={"Authorization": f"Bearer {p_token}"},
        json={"command": "stock.list", "params": {}})
    print(f"Result: {'✅ SUCCESS' if res_p.json()['success'] else '❌ FAILED'} - {res_p.json().get('message')}")

if __name__ == "__main__":
    test()
