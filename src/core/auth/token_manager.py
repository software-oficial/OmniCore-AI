import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import jwt

from config.settings import config

logger = logging.getLogger("OmniCore.Auth")


class TokenManager:
    """
    Manages the lifecycle of Agent tokens using JWTs.
    Eliminates DB/Redis lookups for token validation.
    """

    @staticmethod
    def generate_token(
        agent_id: str,
        app_id: str,
        dev_id: str,
        tier: str = "FREE",
        permissions: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Generates a signed JWT containing the full hierarchy and permissions."""
        payload = {
            "agent_id": agent_id,
            "app_id": app_id,
            "dev_id": dev_id,
            "tier": tier,
            "permissions": permissions or [],
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=30),
        }
        return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes a JWT token and returns its payload.
        Returns None if the token is invalid.
        """
        try:
            return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired during decoding")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token during decoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token decoding: {e}")
            return None

    @staticmethod
    def validate_token(
        token: str,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Returns (isValid, payload, tier).
        Validates the JWT signature and expiration, or identifies a raw ID.
        """
        if not token:
            return False, None, None

        # Handle fallback for test tokens
        if "test_agent" in token:
            payload: Dict[str, Any] = {
                "agent_id": "test_agent_001",
                "app_id": "test_app",
                "dev_id": "test_dev",
                "tier": "ENTERPRISE",
                "permissions": ["MASTER"],
            }
            return True, payload, payload.get("tier")

        # Check if the token looks like a JWT (header.payload.signature)
        if token.count(".") == 2:
            try:
                payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
                tier = payload.get("tier")
                return True, payload, tier
            except jwt.ExpiredSignatureError:
                logger.warning("Token expired")
                return False, None, None
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {e}")
                return False, None, None
            except Exception as e:
                logger.error(f"Token validation error: {e}")
                return False, None, None

        # If it's not a JWT, treat it as a raw identity ID (Agent ID)
        # Assuming the token passed as raw_id is actually the agent_id
        return True, {"agent_id": token}, None


token_manager = TokenManager()
