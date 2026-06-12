import logging
from infra.db.core_db_manager import core_db_manager
from sqlalchemy import text
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmniCoreSeeder")

def seed_database():
    logger.info("🌱 Starting OmniCore-AI Database Seeding...")
    
    # 1. Initialize Schema
    core_db_manager.init_schema()
    
    # 2. Create Test Agent
    # We use a fixed UUID for the test agent to make the audit script predictable
    agent_id = "00000000-0000-0000-0000-000000000001"
    agent_name = "Test Developer"
    api_key = "test_api_key_123"
    
    logger.info(f"Seeding agent: {agent_name} ({agent_id})")
    core_db_manager.execute_raw(
        "INSERT INTO agents (id, name, api_key) VALUES (:id, :name, :key) ON CONFLICT (id) DO NOTHING",
        {"id": agent_id, "name": agent_name, "key": api_key}
    )
    
    # 3. Create Test App
    app_id = str(uuid.uuid4())
    app_name = "Test SaaS App"
    
    logger.info(f"Seeding app: {app_name} ({app_id})")
    core_db_manager.execute_raw(
        "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner_id) ON CONFLICT (id) DO NOTHING",
        {"id": app_id, "name": app_name, "owner_id": agent_id}
    )
    
    # 4. Setup Infrastructure (Using a local DB for testing)
    # This config should point to a DB that actually exists for the test to pass
    # For the sake of the audit, we use standard local postgres
    infra_config = {
        "app_id": app_id,
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "password", # Standard local dev password
        "dbname": "ecosistema_core", # Use the existing core DB for the business data
        "tier": "FREE" # We set to FREE to test the Governance Tier restriction
    }
    
    logger.info(f"Seeding infrastructure for {app_id} with Tier: {infra_config['tier']}")
    core_db_manager.execute_raw(
        """
        INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier)
        VALUES (:app_id, :host, :port, :user, :password, :dbname, :tier)
        ON CONFLICT (app_id) DO UPDATE SET tier = excluded.tier
        """,
        infra_config
    )
    
    # 5. Map Agent to App
    core_db_manager.execute_raw(
        "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id) ON CONFLICT DO NOTHING",
        {"agent_id": agent_id, "app_id": app_id}
    )
    
    logger.info("✅ Seeding completed successfully.")
    return agent_id

if __name__ == "__main__":
    try:
        agent_id = seed_database()
        print(f"SEED_AGENT_ID={agent_id}")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
