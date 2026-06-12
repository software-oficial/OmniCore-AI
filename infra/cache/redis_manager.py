import redis
import json
import logging
from typing import Optional, Any

logger = logging.getLogger("OmniCore.Cache")

class RedisManager:
    """
    Handles ephemeral storage for AI Learning and Session Management.
    Implements Graceful Degradation: if Redis is down, the system remains 
    operational by falling back to primary storage.
    """
    def __init__(self, host='localhost', port=6379, db=0):
        self.host = host
        self.port = port
        self.db = db
        self._connect()

    def _connect(self):
        """Attempt to establish connection to Redis with strict validation."""
        try:
            self.client = redis.StrictRedis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            # FORCE synchronous validation
            if self.client.ping():
                logger.info("✅ Connected to Redis for Ephemeral Learning Store.")
            else:
                raise ConnectionError("Redis ping returned False")
        except Exception as e:
            logger.error(f"⚠️ Redis connection failed: {e}. System entering Degraded Mode.")
            self.client = None

    def is_available(self) -> bool:
        """Strictly returns True ONLY if Redis is responding to a ping."""
        if self.client is None:
            return False
        try:
            return bool(self.client.ping())
        except Exception as e:
            logger.warning(f"Redis connection lost: {e}")
            self.client = None # Invalidate client on failure
            return False

    def set_session_context(self, app_id: str, context: dict, ttl: int = 1800):
        """Caches the developer's profile and DB config to avoid Core DB hits."""
        if not self.is_available(): return
        try:
            self.client.setex(f"session:{app_id}", ttl, json.dumps(context))
        except Exception as e:
            logger.warning(f"Failed to write to Redis cache: {e}")

    def get_session_context(self, app_id: str) -> Optional[dict]:
        """Retrieves cached profile for instant validation."""
        if not self.is_available():
            return None
        try:
            data = self.client.get(f"session:{app_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache: {e}")
            return None

    def cache_learning_error(self, agent_id: str, func_name: str, error_pattern: str, correction: str):
        """Saves a common mistake for exponential learning."""
        if not self.is_available(): return
        try:
            key = f"learn:pattern:{agent_id}:{func_name}"
            self.client.hset(key, error_pattern, correction)
            self.client.expire(key, 86400) 
        except Exception as e:
            logger.warning(f"Failed to cache learning error in Redis: {e}")

    def get_learning_correction(self, agent_id: str, func_name: str, error_pattern: str) -> Optional[str]:
        """Returns a pre-calculated correction to save LLM tokens."""
        if not self.is_available():
            return None
        try:
            return self.client.hget(f"learn:pattern:{agent_id}:{func_name}", error_pattern)
        except Exception as e:
            logger.warning(f"Failed to retrieve learning correction from Redis: {e}")
            return None

# Singleton
cache_manager = RedisManager()
