import requests
import json
import time

BASE_URL = "http://localhost:8000"
EMAIL = f"test_{int(time.time())}@omnicore.ai"
PASSWORD = "SecurePass123!"

def test_flow():
    print(f"--- Starting E2E Test for {EMAIL} ---")
    
    # 1. Register
    print("Testing Registration...")
    try:
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
        print(f"Reg Response: {reg.status_code} - {reg.text}")
        if reg.status_code != 200: return
    except Exception as e:
        print(f"Error: {e}"); return

    # 2. Login
    print("\nTesting Login...")
    try:
        login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
        print(f"Login Response: {login.status_code} - {login.text}")
        user_id = login.json()['data']['user_id']
        print(f"Authenticated as: {user_id}")
    except Exception as e:
        print(f"Error: {e}"); return

    # 3. Create Project
    print("\nTesting Project Creation...")
    try:
        proj = requests.post(
            f"{BASE_URL}/api/agent/projects/create", 
            headers={"Authorization": f"Bearer {user_id}"}, 
            json={"name": "E2E Validation Project"}
        )
        print(f"Proj Response: {proj.status_code} - {proj.text}")
        if proj.status_code != 200: return
    except Exception as e:
        print(f"Error: {e}"); return

    # 4. List Projects
    print("\nTesting Project List...")
    try:
        plist = requests.get(
            f"{BASE_URL}/api/agent/projects", 
            headers={"Authorization": f"Bearer {user_id}"}
        )
        print(f"List Response: {plist.status_code} - {plist.text}")
        if plist.status_code != 200: return
    except Exception as e:
        print(f"Error: {e}"); return

    # 5. Discovery
    print("\nTesting Discovery...")
    try:
        disc = requests.get(
            f"{BASE_URL}/api/discovery/commands", 
            headers={"Authorization": f"Bearer {user_id}"}
        )
        print(f"Disc Response: {disc.status_code} - {disc.text[:200]}...")
        if disc.status_code != 200: return
    except Exception as e:
        print(f"Error: {e}"); return

    print("\n--- RESULT: ALL TESTS PASSED SUCCESSFULLY ---")

if __name__ == '__main__':
    test_flow()
