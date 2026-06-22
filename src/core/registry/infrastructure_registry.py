import logging
import time
from typing import Any, Dict, Optional, Tuple

from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.BusinessRegistry")


class BusinessRegistry:
    """
    Simplified Registry for OmniCore-AI (UUS).
    Resolves User identities directly from the Unified Central Database.
    """

    def __init__(self):
        # L1 Cache: Local memory for extreme speed
        self._l1_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.L1_TTL = 300

    def get_business_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Resolves the business associated with a user and their role."""
        now = time.time()

        if user_id in self._l1_cache:
            timestamp, context = self._l1_cache[user_id]
            if now - timestamp < self.L1_TTL:
                return context

        query = """
            SELECT 
                u.business_id, u.role, b.plan, b.name as business_name
            FROM users u
            JOIN businesses b ON u.business_id = b.id
            WHERE u.id = :user_id
            LIMIT 1
        """

        try:
            result = (
                core_db_manager.execute_raw(query, {"user_id": user_id})
                .mappings()
                .first()
            )

            if not result:
                logger.warning(f"No business found for user: {user_id}")
                return None

            config_ctx = {
                "business_id": result["business_id"],
                "role": result["role"],
                "tier": result["plan"],
                "business_name": result["business_name"],
            }

            self._l1_cache[user_id] = (now, config_ctx)
            return config_ctx
        except Exception as e:
            logger.error(f"Error resolving business context for user {user_id}: {e}")
            return None

    def register_business(
        self, owner_id: str, business_name: str, tier: str = "FREE"
    ) -> str:
        """Registers a new business with default sandbox configuration."""
        db_config = {
            "host": "sandbox.omnicore.internal",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "dbname": f"db_{business_name.lower().replace(' ', '_')}",
        }
        return self.register_app(
            agent_id=owner_id, app_name=business_name, db_config=db_config, tier=tier
        )

    def register_app(
        self,
        agent_id: str,
        app_name: str,
        db_config: Dict[str, Any],
        tier: str = "FREE",
    ) -> str:
        """Registers a new app and links it to an agent."""
        import uuid

        app_id = str(uuid.uuid4())
        try:
            # 1. Create the app
            core_db_manager.execute_raw(
                "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner)",
                {
                    "id": app_id,
                    "name": app_name,
                    "owner": agent_id,
                },
            )

            # 2. Add infrastructure details
            core_db_manager.execute_raw(
                """
                INSERT INTO app_infrastructure 
                (app_id, db_host, db_port, db_user, db_password, db_name, tier) 
                VALUES (:aid, :host, :port, :user, :pw, :db, :tier)
                """,
                {
                    "aid": app_id,
                    "host": db_config["host"],
                    "port": db_config["port"],
                    "user": db_config["user"],
                    "pw": db_config["password"],
                    "db": db_config["dbname"],
                    "tier": tier.upper(),
                },
            )

            logger.info(
                f"Registered app {app_name} (ID: {app_id}) for agent {agent_id}"
            )
            return app_id
        except Exception as e:
            logger.error(f"Failed to register app: {e}")
            raise e

    def get_all_apps(self) -> Dict[str, Any]:
        """Returns all onboarded apps."""
        query = "SELECT id, name FROM apps"
        try:
            results = core_db_manager.execute_raw(query).mappings().all()
            return {r["id"]: {"app_id": r["id"], "name": r["name"]} for r in results}
        except Exception as e:
            logger.error(f"Error fetching all apps: {e}")
            return {}

    def get_app_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the configuration of a specific app by its ID."""
        query = """
            SELECT a.name, ai.db_host, ai.db_port, ai.db_user, ai.db_password, ai.db_name, ai.tier
            FROM apps a
            JOIN app_infrastructure ai ON a.id = ai.app_id
            WHERE a.id = :app_id
        """
        try:
            result = (
                core_db_manager.execute_raw(query, {"app_id": app_id})
                .mappings()
                .first()
            )
            if not result:
                return None

            return {
                "name": result.name,
                "tier": result.tier,
                "db_config": {
                    "host": result.db_host,
                    "port": result.db_port,
                    "user": result.db_user,
                    "password": result.db_password,
                    "dbname": result.db_name,
                },
            }
        except Exception as e:
            logger.error(f"Error fetching app {app_id}: {e}")
            return None

    def update_app_tier(self, app_id: str, new_tier: str) -> bool:
        """Updates the tier of a SaaS instance."""
        try:
            sql = "UPDATE app_infrastructure SET tier = :tier WHERE app_id = :app_id"
            core_db_manager.execute_raw(
                sql, {"tier": new_tier.upper(), "app_id": app_id}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update tier for app {app_id}: {e}")
            return False


# Singleton
business_registry = BusinessRegistry()
