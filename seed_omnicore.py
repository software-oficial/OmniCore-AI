import logging
from infra.db.core_db_manager import core_db_manager
from sqlalchemy import text
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmniCoreSeeder")

def seed_database():
    logger.info("🌱 Starting OmniCore-AI Database Seeding...")
    from config.settings import config
    from infra.blueprint_manager import blueprint_manager

    # 1. Initialize Schema
    core_db_manager.init_schema()

    # 2. Create Test Agent
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

    # 4. Setup Infrastructure
    core_db_manager.execute_raw("DELETE FROM app_infrastructure")
    infra_config = {
        "app_id": app_id,
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "dbname": config.DB_NAME,
        "tier": "FREE"
    }

    logger.info(f"Seeding infrastructure for {app_id} with Tier: {infra_config['tier']}")
    core_db_manager.execute_raw(
        """
        INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier)
        VALUES (:app_id, :host, :port, :user, :password, :dbname, :tier)
        """,
        infra_config
    )

    # 5. Deploy Blueprints Directly to Business DB
    logger.info("🏗️ Deploying business blueprints to the test DB...")
    blueprints = blueprint_manager.get_all_blueprints()

    # We use a temporary engine to deploy blueprints to the business DB
    from sqlalchemy import create_engine
    business_url = f"postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    engine = create_engine(business_url)
    with engine.connect() as conn:
        for module, sql in blueprints.items():
            logger.info(f"📦 Deploying blueprint for: {module}")
            for statement in sql.strip().split(';'):
                if statement.strip():
                    conn.execute(text(statement))
        conn.commit()

    # 6. Map Agent to App
    core_db_manager.execute_raw(
        "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id) ON CONFLICT DO NOTHING",
        {"agent_id": agent_id, "app_id": app_id}
    )

    logger.info("✅ Seeding and Blueprint Deployment completed successfully.")
    return agent_id

if __name__ == "__main__":
    try:
        agent_id = seed_database()
        print(f"SEED_AGENT_ID={agent_id}")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
