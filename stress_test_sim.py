import requests
import uuid
import random
import concurrent.futures
import time
from typing import List

API_BASE = "http://localhost:8000/api"
NUM_USERS = 30  # Simular 30 usuarios concurrentes
COMMANDS = ["stock.list", "stock.add", "sales.process"]

def simulate_user(user_id: int):
    email = f"user_{user_id}@stress_test.ai"
    password = f"Pass_{user_id}_Omni"
    agent_name = f"Agent_{user_id}"
    platform = f"Platform_{user_id}"
    
    try:
        # 1. Register
        requests.post(f"{API_BASE}/auth/register", json={"email": email, "password": password})
        
        # 2. Login
        login_res = requests.post(f"{API_BASE}/auth/login", json={"email": email, "password": password})
        if login_res.status_code != 200: return False, f"Login failed for {user_id}"
        uid = login_res.json()["data"]["user_id"]
        
        # 3. Create Agent (via /api/agent/register)
        agent_res = requests.post(f"{API_BASE}/agent/register", json={"name": agent_name, "platform_name": platform})
        if agent_res.status_code != 200: return False, f"Agent reg failed for {user_id}"
        agent_id = agent_res.json()["agent_id"]
        
        # 4. Create a Token
        token_res = requests.post(f"{API_BASE}/auth/tokens/create", 
            headers={"Authorization": f"Bearer {uid}"},
            json={"agent_id": agent_id, "token_name": f"Tkn_{user_id}", "mode": "LEARNING"})
        token = token_res.json()["data"]["api_token"]
        
        # 5. Execute random commands
        for _ in range(3):
            cmd = random.choice(COMMANDS)
            requests.post(f"{API_BASE}/gateway/execute", 
                headers={"Authorization": f"Bearer {token}"},
                json={"command": cmd, "params": {"test": "data"}})
            
        return True, f"User {user_id} completed flow"
    except Exception as e:
        return False, f"User {user_id} error: {str(e)}"

def main():
    print(f"🚀 Starting stress simulation with {NUM_USERS} concurrent users...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(simulate_user, range(NUM_USERS)))
    
    end_time = time.time()
    duration = end_time - start_time
    
    successes = [r for r, m in results if r]
    failures = [m for r, m in results if not r]
    
    print("\n" + "="*40)
    print(f"📊 STRESS TEST RESULTS")
    print("="*40)
    print(f"Total Users: {NUM_USERS}")
    print(f"Successful: {len(successes)}")
    print(f"Failed: {len(failures)}")
    print(f"Total Duration: {duration:.2f}s")
    print(f"Avg Time per User: {duration/NUM_USERS:.2f}s")
    print("="*40)
    
    if failures:
        print("\n❌ Top Failures:")
        for f in failures[:5]: print(f"- {f}")

if __name__ == "__main__":
    main()
