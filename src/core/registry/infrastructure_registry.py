import logging
import time
from typing import Any, Dict, Optional, Tuple

from src.infrastructure.cache.redis_manager import cache_manager
from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.BusinessRegistry")


class BusinessRegistry:
    """
    Simplified Registry for OmniCore-AI.
    Resolves User identities directly into Business infrastructure configurations.
    """

    def __init__(self):
        # L1 Cache: Local memory for extreme speed
        self._l1_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.L1_TTL = 300

    def get_business_context(self, owner_id: str) -> Optional[Dict[str, Any]]:
        """Resolves the business associated with a user (owner)."""
        now = time.time()

        if owner_id in self._l1_cache:
            timestamp, context = self._l1_cache[owner_id]
            if now - timestamp < self.L1_TTL:
                return context

        cached_context = cache_manager.get_session_context(owner_id)
        if cached_context:
            self._l1_cache[owner_id] = (now, cached_context)
            return cached_context

        query = """
            SELECT 
                a.id as business_id, 
                ai.db_host, ai.db_port, ai.db_user, ai.db_password, ai.db_name, ai.tier
            FROM apps a
            JOIN app_infrastructure ai ON a.id = ai.app_id
            WHERE a.owner_id = :owner_id
            LIMIT 1
        """

        try:
            result = core_db_manager.execute_raw(
                query, {"owner_id": owner_id}
            ).fetchone()
            if not result:
                logger.warning(f"No business infrastructure found for user: {owner_id}")
                return None

            config_ctx = {
                "business_id": result.business_id,
                "db_config": {
                    "host": result.db_host,
                    "port": result.db_port,
                    "user": result.db_user,
                    "password": result.db_password,
                    "dbname": result.db_name,
                },
                "tier": result.tier,
            }

            cache_manager.set_session_context(owner_id, config_ctx, ttl=3600)
            self._l1_cache[owner_id] = (now, config_ctx)
            return config_ctx
        except Exception as e:
            logger.error(f"Error resolving business context for user {owner_id}: {e}")
            return None

    def register_business(
        self,
        owner_id: str,
        name: str,
        db_config: Dict[str, Any],
        tier: str = "FREE",
    ) -> str:
        """Registers a new business directly for a user."""
        import uuid

        business_id = str(uuid.uuid4())
        try:
            # 1. Create the app linked to owner_id
            app_sql = (
                "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner_id)"
            )
            core_db_manager.execute_raw(
                app_sql, {"id": business_id, "name": name, "owner_id": owner_id}
            )

            # 2. Create the infrastructure config
            infra_sql = """
                INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier)
                VALUES (:app_id, :host, :port, :user, :password, :dbname, :tier)
            """
            core_db_manager.execute_raw(
                infra_sql,
                {
                    "app_id": business_id,
                    "host": db_config["host"],
                    "port": db_config["port"],
                    "user": db_config["user"],
                    "password": db_config["password"],
                    "dbname": db_config["dbname"],
                    "tier": tier,
                },
            )

            logger.info(f"Registered business {name} for user {owner_id}")
            return business_id
        except Exception as e:
            logger.error(f"Failed to register business: {e}")
            raise e


# Singleton
business_registry = BusinessRegistry()
