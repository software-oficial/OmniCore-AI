import requests
import json

# --- CONFIGURATION ---
API_BASE = "http://localhost:8000/api"
# Usando el usuario creado en el test anterior para obtener un token de sesión
# En un escenario real, este script haría primero el login
USER_EMAIL = "test_user@omnicore.ai"
USER_PASS = "SecurePassword123!"

def main():
    print("🚀 Starting OmniCore-AI API Integration Test...")
    
    # 1. AUTHENTICATION: Login to get user_id (acting as session token for panel)
    print("\n🔑 Step 1: Authenticating...")
    login_res = requests.post(f"{API_BASE}/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASS
    })
    
    if login_res.status_code != 200:
        print(f"❌ Login failed: {login_res.text}")
        return
    
    user_id = login_res.json()["data"]["user_id"]
    print(f"✅ Authenticated as User ID: {user_id}")

    # 2. TOKEN GENERATION: Create an API token for an agent
    # El Gateway requiere un TOKEN (LEARNING o PRODUCTION), no un USER_ID.
    # Vamos a crear un token de API para el agente "TestBot"
    print("\n🔑 Step 2: Generating API Token for Agent...")
    token_res = requests.post(f"{API_BASE}/auth/tokens/create", 
        headers={"Authorization": f"Bearer {user_id}"},
        json={
            "agent_id": "00000000-0000-0000-0000-000000000001", # ID de prueba
            "token_name": "IntegrationTestToken"
        }
    )
    
    if token_res.status_code != 200:
        print(f"❌ Token generation failed: {token_res.text}")
        return
    
    api_token = token_res.json()["data"]["api_token"]
    print(f"✅ API Token generated: {api_token}")

    # 3. COMMAND EXECUTION: Using the Gateway to add a product to stock
    print("\n📦 Step 3: Executing 'stock.add' command via Gateway...")
    payload = {
        "command": "stock.add",
        "params": {
            "name": "OmniCore Neural Processor",
            "price": 1499.99,
            "quantity": 10
        }
    }
    
    exec_res = requests.post(f"{API_BASE}/gateway/execute", 
        headers={"Authorization": f"Bearer {api_token}"},
        json=payload
    )
    
    if exec_res.status_code == 200:
        print("✅ Command executed successfully!")
        print(f"Response: {json.dumps(exec_res.json(), indent=2)}")
    else:
        print(f"❌ Command failed: {exec_res.text}")

if __name__ == "__main__":
    main()
