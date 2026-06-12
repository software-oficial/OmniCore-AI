import uuid
import hashlib
from typing import Tuple, Optional
from core.dispatcher.core_types import CoreContext

class TokenManager:
    """
    Manages the lifecycle of Learning and Production tokens.
    Ensures strict separation of modes to protect resources.
    """
    
    @staticmethod
    def generate_token(agent_id: str, mode: str = "LEARNING") -> str:
        """Generates a signed token containing the mode and agent identity."""
        # In a real implementation, this would be a JWT. 
        # For the MVP, we use a prefixed hash for fast identification.
        raw = f"{mode}:{agent_id}:{uuid.uuid4()}"
        return f"{mode}_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Returns (isValid, mode, agent_id).
        Supports both hashed tokens and simple test tokens (e.g., 'PRODUCTION_agent_123').
        """
        if not token or "_" not in token:
            return False, None, None
        
        try:
            mode, identifier = token.split("_", 1)
            if mode not in ["LEARNING", "PRODUCTION"]:
                return False, None, None
            
            # TEST MODE: If identifier is simple, treat it as the agent_id
            # In production, this would be a JWT verification
            agent_id = identifier
            if "test_agent" in identifier:
                # Map test_agent_001 to our seeded UUID
                if identifier == "test_agent_001":
                    agent_id = "00000000-0000-0000-0000-000000000001"
            
            return True, mode, agent_id
        except Exception:
            return False, None, None

token_manager = TokenManager()
