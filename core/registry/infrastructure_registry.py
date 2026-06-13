import logging
import time
from typing import Dict, Any, Optional, Tuple
from infra.db.core_db_manager import core_db_manager
from infra.cache.redis_manager import cache_manager
from sqlalchemy import text

logger = logging.getLogger("OmniCore.InfrastructureRegistry")

class InfrastructureRegistry:
    """
    The Master Registry for OmniCore-AI.
    Resolves Agent identities into Application infrastructure configurations.
    Uses a tiered caching strategy: L1 (Local Memory) -> L2 (Redis) -> L3 (Core DB).
    """
    def __init__(self):
        # L1 Cache: Local memory for extreme speed (TTL based on simple timestamp)
        self._l1_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self.L1_TTL = 300  # 5 minutes

    def get_app_context(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolves the primary application associated with an agent.
        Returns the app_id, db_config, and tier.
        """
        now = time.time()

        # 1. Try L1 Cache (Local Memory)
        if agent_id in self._l1_cache:
            timestamp, context = self._l1_cache[agent_id]
            if now - timestamp < self.L1_TTL:
                return context

        # 2. Try L2 Cache (Redis)
        cached_context = cache_manager.get_session_context(agent_id)
        if cached_context:
            self._l1_cache[agent_id] = (now, cached_context)
            return cached_context

        query = """
            SELECT 
                a.id as app_id, 
                ai.db_host, ai.db_port, ai.db_user, ai.db_password, ai.db_name, ai.tier
            FROM agent_app_mapping aam
            JOIN apps a ON aam.app_id = a.id
            JOIN app_infrastructure ai ON a.id = ai.app_id
            WHERE aam.agent_id = :agent_id
            LIMIT 1
        """
        
        try:
            result = core_db_manager.execute_raw(query, {"agent_id": agent_id}).fetchone()
            if not result:
                logger.warning(f"No infrastructure mapping found for agent: {agent_id}")
                return None

            # Format the DB config for the DynamicDbManager
            config = {
                "app_id": result.app_id,
                "db_config": {
                    "host": result.db_host,
                    "port": result.db_port,
                    "user": result.db_user,
                    "password": result.db_password,
                    "dbname": result.db_name
                },
                "tier": result.tier
            }
            
            # Store in Redis (L2) and Local Memory (L1)
            cache_manager.set_session_context(agent_id, config, ttl=3600)
            self._l1_cache[agent_id] = (now, config)
            return config
        except Exception as e:
            logger.error(f"Error resolving app context for agent {agent_id}: {e}")
            return None

    def _invalidate_cache(self, agent_id: str):
        """Removes agent from all cache tiers."""
        self._l1_cache.pop(agent_id, None)
        if cache_manager.client:
            cache_manager.client.delete(f"session:{agent_id}")

    def get_app_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:

        """Retrieves the configuration of a specific app by its ID."""
        query = """
            SELECT a.name, ai.db_host, ai.db_port, ai.db_user, ai.db_password, ai.db_name, ai.tier
            FROM apps a
            JOIN app_infrastructure ai ON a.id = ai.app_id
            WHERE a.id = :app_id
        """
        try:
            result = core_db_manager.execute_raw(query, {"app_id": app_id}).mappings().first()
            if not result: return None
            
            # Return with structured db_config for DbManager compatibility
            return {
                "name": result.name,
                "tier": result.tier,
                "db_config": {
                    "host": result.db_host,
                    "port": result.db_port,
                    "user": result.db_user,
                    "password": result.db_password,
                    "dbname": result.db_name
                }
            }
        except Exception as e:
            logger.error(f"Error fetching app {app_id}: {e}")
            return None

    def update_app_tier(self, app_id: str, new_tier: str) -> bool:
        """Updates the tier (e.g., FREE -> PRO) of a SaaS instance."""
        try:
            sql = "UPDATE app_infrastructure SET tier = :tier WHERE app_id = :app_id"
            core_db_manager.execute_raw(sql, {"tier": new_tier.upper(), "app_id": app_id})
            
            # Invalidate all cache entries related to this app
            # In a production environment, we would track which agents belong to this app
            # For now, we clear the global cache or rely on TTL. 
            # Ideally, we'd use a pattern like 'app:{app_id}:agents' in Redis.
            logger.info(f"Tier updated to {new_tier} for app {app_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update tier for app {app_id}: {e}")
            return False

    def register_app(self, agent_id: str, app_name: str, db_config: Dict[str, Any], tier: str = "FREE") -> str:

        """
        Onboards a new SaaS instance and maps it to an agent.
        """
        import uuid
        app_id = str(uuid.uuid4())
        try:
            # 1. Create the app
            app_sql = "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner_id)"
            core_db_manager.execute_raw(app_sql, {"id": app_id, "name": app_name, "owner_id": agent_id})

            # 2. Create the infrastructure config
            infra_sql = """
                INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier)
                VALUES (:app_id, :host, :port, :user, :password, :dbname, :tier)
            """
            core_db_manager.execute_raw(infra_sql, {
                "app_id": app_id,
                "host": db_config['host'],
                "port": db_config['port'],
                "user": db_config['user'],
                "password": db_config['password'],
                "dbname": db_config['dbname'],
                "tier": tier
            })

            # 3. Map agent to app
            mapping_sql = "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id)"
            core_db_manager.execute_raw(mapping_sql, {"agent_id": agent_id, "app_id": app_id})

            # Invalidate existing cache for this agent since infra has changed
            if cache_manager.client:
                cache_manager.client.delete(f"session:{agent_id}")

            logger.info(f"Successfully registered app {app_name} for agent {agent_id} with ID {app_id}")
            return app_id
        except Exception as e:
            logger.error(f"Failed to register app: {e}")
            raise e

# Singleton
infrastructure_registry = InfrastructureRegistry()
