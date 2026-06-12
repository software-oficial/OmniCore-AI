import uuid
import os
from core.registry.infrastructure_registry import infrastructure_registry
from infra.db.core_db_manager import core_db_manager

def setup():
    agent_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())
    app_name = f"StressTestApp_{agent_id[:8]}"
    print(f"🚀 Setup: Generating new Agent ID: {agent_id}")
    try:
        agent_sql = "INSERT INTO agents (id, name, api_key, created_at) VALUES (:id, :name, :api_key, CURRENT_TIMESTAMP)"
        core_db_manager.execute_raw(agent_sql, {"id": agent_id, "name": f"StressAgent_{agent_id[:8]}", "api_key": api_key})
        print(f"✅ Agent created in DB: {agent_id}")
        db_config = {"host": "localhost", "port": 5435, "user": "omnicore_user", "password": "omnicore_password", "dbname": "omnicore_registry"}
        app_id = infrastructure_registry.register_app(agent_id, app_name, db_config, tier="ENTERPRISE")
        print(f"✅ App registered successfully. App ID: {app_id}")
        print(f"🎯 TEST READY: Use token 'LEARNING_{agent_id}' for requests.")
    except Exception as e:
        print(f"❌ Setup failed: {e}")

if __name__ == "__main__":
    setup()
