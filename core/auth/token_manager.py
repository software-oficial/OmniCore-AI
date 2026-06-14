import uuid
import hashlib
import logging
from typing import Tuple, Optional
from infra.cache.redis_manager import cache_manager

logger = logging.getLogger("OmniCore.Auth")

class TokenManager:
    """
    Manages the lifecycle of Agent tokens.
    Uses Redis to map ephemeral tokens to Agent identities.
    """
    
    @staticmethod
    def generate_token(agent_id: str) -> str:
        """Generates a token and stores the mapping to the agent in Redis."""
        raw = f"{agent_id}:{uuid.uuid4()}"
        token_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        token = f"tok_{token_hash}"
        
        # Store mapping in Redis: token -> agent_id
        # TTL: 30 days
        ttl = 2592000
        cache_manager.set_session_context(token, {"agent_id": agent_id}, ttl=ttl)
        
        return token

    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[str]]:
        """
        Returns (isValid, agent_id).
        Resolves the token via Redis (ephemeral) or Core DB (persistent).
        """
        if not token:
            return False, None
        
        try:
            # 1. Try to resolve via Redis (Ephemeral/Session tokens)
            if token.startswith("tok_"):
                session_data = cache_manager.get_session_context(token)
                if session_data:
                    return True, session_data["agent_id"]
            
            # 2. Try to resolve via Core DB (Persistent API Keys)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            from infra.db.core_db_manager import core_db_manager
            
            token_data = core_db_manager.execute_raw(
                "SELECT agent_id FROM api_tokens WHERE token_hash = :hash",
                {"hash": token_hash}
            ).fetchone()
            
            if token_data:
                return True, token_data["agent_id"]
            
            # 3. Fallback: Simple Test Tokens
            if "test_agent" in token:
                agent_id = token
                if token == "test_agent_001":
                    agent_id = "00000000-0000-0000-0000-000000000001"
                return True, agent_id
            
            return False, None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None

token_manager = TokenManager()
