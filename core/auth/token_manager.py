import uuid
import hashlib
import logging
from typing import Tuple, Optional
from infra.cache.redis_manager import cache_manager

logger = logging.getLogger("OmniCore.Auth")

class TokenManager:
    """
    Manages the lifecycle of Learning and Production tokens.
    Uses Redis to map ephemeral tokens to Agent identities.
    """
    
    @staticmethod
    def generate_token(agent_id: str, mode: str = "LEARNING") -> str:
        """Generates a token and stores the mapping to the agent in Redis."""
        raw = f"{mode}:{agent_id}:{uuid.uuid4()}"
        token_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        token = f"{mode}_{token_hash}"
        
        # Store mapping in Redis: token -> agent_id
        # TTL: 24 hours for Learning, 30 days for Production
        ttl = 86400 if mode == "LEARNING" else 2592000
        cache_manager.set_session_context(token, {"agent_id": agent_id, "mode": mode}, ttl=ttl)
        
        return token

    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Returns (isValid, mode, agent_id).
        Resolves the token via Redis (ephemeral) or Core DB (persistent).
        """
        if not token:
            return False, None, None
        
        try:
            # 1. Try to resolve via Redis (Ephemeral/Session tokens)
            if "_" in token:
                session_data = cache_manager.get_session_context(token)
                if session_data:
                    return True, session_data["mode"], session_data["agent_id"]
            
            # 2. Try to resolve via Core DB (Persistent API Keys)
            # We hash the provided token to match the storage in api_tokens table
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            from infra.db.core_db_manager import core_db_manager
            
            token_data = core_db_manager.execute_raw(
                "SELECT agent_id FROM api_tokens WHERE token_hash = :hash",
                {"hash": token_hash}
            ).fetchone()
            
            if token_data:
                # Persistent tokens are always PRODUCTION mode
                return True, "PRODUCTION", token_data["agent_id"]
            
            # 3. Fallback: Simple Test Tokens (for development/seeding)
            if "_" in token:
                mode, identifier = token.split("_", 1)
                if mode in ["LEARNING", "PRODUCTION"] and "test_agent" in identifier:
                    agent_id = identifier
                    if identifier == "test_agent_001":
                        agent_id = "00000000-0000-0000-0000-000000000001"
                    return True, mode, agent_id
            
            return False, None, None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None, None

token_manager = TokenManager()
