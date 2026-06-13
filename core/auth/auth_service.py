import hashlib
import uuid
import logging
from typing import Tuple, Optional, Dict, Any
from fastapi import HTTPException
from infra.db.core_db_manager import core_db_manager
from core.dispatcher.core_types import ServiceResponse

# In a real production env, use bcrypt or argon2
# For this implementation, we use a secure salted sha256 for demonstration
# but the architecture allows swapping for any password hasher.
logger = logging.getLogger("OmniCore.AuthService")

class AuthService:
    """
    Handles User Identity, Registration, and Session Management.
    """
    def __init__(self):
        self.logger = logging.getLogger("AuthService")

    def _hash_password(self, password: str, salt: str = "OMNICORE_SALT_2026") -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def register_user(self, email: str, password: str) -> ServiceResponse:
        """Registers a new user in the system."""
        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        
        try:
            core_db_manager.execute_raw(
                "INSERT INTO users (id, email, password_hash) VALUES (:id, :email, :pass)",
                {"id": user_id, "email": email, "pass": password_hash}
            )
            return ServiceResponse.success_res(
                data={"user_id": user_id}, 
                message="User registered successfully."
            )
        except Exception as e:
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                return ServiceResponse.error_res("Email already registered", "USER_ALREADY_EXISTS")
            return ServiceResponse.error_res(f"Registration error: {str(e)}", "AUTH_ERROR")

    def login(self, email: str, password: str) -> ServiceResponse:
        """Validates credentials and returns a session indicator."""
        password_hash = self._hash_password(password)
        
        try:
            result = core_db_manager.execute_raw(
                "SELECT id, email FROM users WHERE email = :email AND password_hash = :pass",
                {"email": email, "pass": password_hash}
            )
            user = result.fetchone()
            
            if not user:
                return ServiceResponse.error_res("Invalid email or password", "INVALID_CREDENTIALS")
            
            # Acceso estrictamente por índice para evitar errores de tupla
            user_id = user[0]
            user_email = user[1]
            
            return ServiceResponse.success_res(
                data={"user_id": user_id, "email": user_email}, 
                message="Login successful."
            )
        except Exception as e:
            return ServiceResponse.error_res(f"Login error: {str(e)}", "AUTH_ERROR")

    def create_api_token(self, user_id: str, agent_id: str, token_name: str, mode: str = "PRODUCTION") -> ServiceResponse:
        """
        Generates a new API token for a user's agent.
        Supports both LEARNING (ephemeral/Redis) and PRODUCTION (persistent/DB).
        """
        from core.auth.token_manager import token_manager

        # 1. Handle LEARNING Mode (Ephemeral)
        if mode.upper() == "LEARNING":
            # Los tokens de learning son puramente efímeros (Redis)
            # No intentamos guardarlos en la DB para evitar errores de Foreign Key con agentes no registrados
            token = token_manager.generate_token(agent_id, mode="LEARNING")
            return ServiceResponse.success_res(
                data={"api_token": token, "mode": "LEARNING"}, 
                message=f"Ephemeral token '{token_name}' generated (Expires in 24h)."
            )

        # 2. Handle PRODUCTION Mode (Persistent)
        # Check Token Limit
        result = core_db_manager.execute_raw(
            "SELECT count(*) as count FROM api_tokens WHERE user_id = :uid",
            {"uid": user_id}
        )
        token_count = result.fetchone()[0]
        
        if token_count >= 10:
            return ServiceResponse.error_res("Token limit reached. You can have a maximum of 10 Production API tokens.", "TOKEN_LIMIT_EXCEEDED")
        
        # Generate Persistent Token
        raw_token = f"oc_{uuid.uuid4().hex}"
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            core_db_manager.execute_raw(
                "INSERT INTO api_tokens (token_hash, user_id, agent_id, token_name) VALUES (:hash, :uid, :aid, :name)",
                {"hash": token_hash, "uid": user_id, "aid": agent_id, "name": token_name}
            )
            return ServiceResponse.success_res(
                data={"api_token": raw_token, "mode": "PRODUCTION"}, 
                message=f"Persistent token '{token_name}' generated successfully."
            )
        except Exception as e:
            return ServiceResponse.error_res(f"Token generation error: {str(e)}", "TOKEN_ERROR")

    def list_user_tokens(self, user_id: str) -> ServiceResponse:
        """Lists all tokens associated with a user."""
        try:
            result = core_db_manager.execute_raw(
                "SELECT token_name, agent_id, created_at FROM api_tokens WHERE user_id = :uid",
                {"uid": user_id}
            )
            rows = result.fetchall()
            # Convert tuple to dict explicitly to avoid dictionary update sequence error
            tokens = [
                {"token_name": row[0], "agent_id": row[1], "created_at": str(row[2])} 
                for row in rows
            ]
            return ServiceResponse.success_res(data=tokens, message="Tokens retrieved.")
        except Exception as e:
            return ServiceResponse.error_res(f"Error retrieving tokens: {str(e)}", "TOKEN_ERROR")

    def revoke_token(self, token_hash: str) -> ServiceResponse:
        """Revokes an API token."""
        try:
            core_db_manager.execute_raw("DELETE FROM api_tokens WHERE token_hash = :hash", {"hash": token_hash})
            return ServiceResponse.success_res(message="Token revoked successfully.")
        except Exception as e:
            return ServiceResponse.error_res(f"Error revoking token: {str(e)}", "TOKEN_ERROR")

# Singleton
auth_service = AuthService()
