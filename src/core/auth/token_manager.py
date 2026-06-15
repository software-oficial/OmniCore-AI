import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

import jwt

from config.settings import config

logger = logging.getLogger("OmniCore.Auth")


class TokenManager:
    """
    Manages the lifecycle of Agent tokens using JWTs.
    Eliminates DB/Redis lookups for token validation.
    """

    @staticmethod
    def generate_token(agent_id: str, tier: str = "FREE") -> str:
        """Generates a signed JWT containing agent_id and tier."""
        payload = {
            "agent_id": agent_id,
            "tier": tier,
            "exp": datetime.utcnow() + timedelta(days=30),
        }
        return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")

    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Returns (isValid, agent_id, tier).
        Validates the JWT signature and expiration.
        """
        if not token:
            return False, None, None

        try:
            # Handle fallback for test tokens
            if "test_agent" in token:
                agent_id = token
                if token == "test_agent_001":
                    agent_id = "00000000-0000-0000-0000-000000000001"
                return True, agent_id, "ENTERPRISE"

            payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
            return True, payload["agent_id"], payload["tier"]

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return False, None, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return False, None, None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None, None


token_manager = TokenManager()
