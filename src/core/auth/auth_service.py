import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.auth.token_manager import token_manager
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.AuthService")


class AuthService:
    """
    Service to manage users, roles, and granular permissions (PBAC).
    Ported from plataforma-stock.
    """

    def login(self, session: Session, email: str, password: str) -> ServiceResponse:
        """Authenticates a user and returns their user_id."""
        try:
            import hashlib

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = (
                session.execute(
                    text(
                        "SELECT id FROM users WHERE email = :email AND password_hash = :hash"
                    ),
                    {"email": email, "hash": password_hash},
                )
                .mappings()
                .first()
            )

            if not user:
                return ServiceResponse.error_res(
                    "Invalid email or password", "AUTH_INVALID_CREDENTIALS"
                )

            return ServiceResponse.success_res(
                data={"user_id": user["id"]}, message="Login successful."
            )
        except Exception as e:
            logger.error(f"Login error: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_LOGIN_ERROR"
            )

    def register_user(
        self, session: Session, email: str, password: str, role: str = "user"
    ) -> ServiceResponse:
        """Registers a new system user."""
        try:
            import hashlib

            from sqlalchemy.exc import IntegrityError

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            result = session.execute(
                text(
                    "INSERT INTO users (id, email, password_hash) VALUES (gen_random_uuid(), :email, :hash) RETURNING id"
                ),
                {"email": email, "hash": password_hash},
            )
            user_id = result.scalar()
            session.commit()
            return ServiceResponse.success_res(
                data={"user_id": user_id}, message="User registered successfully."
            )
        except IntegrityError as e:
            session.rollback()
            if "users_email_key" in str(e.orig):
                return ServiceResponse.error_res(
                    "This email is already registered. Please login or use a different email.",
                    "AUTH_EMAIL_EXISTS",
                )
            logger.error(f"Integrity error during registration: {e}")
            return ServiceResponse.error_res(
                f"Internal database error: {str(e)}", "AUTH_REG_ERROR"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Registration error: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_REG_ERROR"
            )

    def validate_user_exists(self, session: Session, user_id: str) -> bool:
        """Checks if a user exists in the core database."""
        try:
            result = session.execute(
                text("SELECT 1 FROM users WHERE id = :uid"), {"uid": user_id}
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error validating user existence: {e}")
            return False

    def create_api_token(
        self,
        session: Session,
        user_id: str,
        agent_id: str,
        token_name: str,
        mode: str = "PRODUCTION",
    ) -> ServiceResponse:
        """Creates a new API token for an agent."""
        try:
            if not self.validate_user_exists(session, user_id):
                return ServiceResponse.error_res(
                    "The specified user does not exist.", "AUTH_USER_NOT_FOUND"
                )

            # Generate a JWT token instead of an opaque string to match TokenManager.validate_token
            token = token_manager.generate_token(
                agent_id=agent_id, app_id="SYSTEM", dev_id="SYSTEM", user_id=user_id
            )

            session.execute(
                text(
                    "INSERT INTO user_tokens (id, user_id, agent_id, token, token_name, mode) VALUES (gen_random_uuid(), :uid, :aid, :token, :name, :mode)"
                ),
                {
                    "uid": user_id,
                    "aid": agent_id,
                    "token": token,
                    "name": token_name,
                    "mode": mode,
                },
            )
            session.commit()
            return ServiceResponse.success_res(
                data={"api_token": token}, message="API token created."
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Token creation error: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_TOKEN_ERROR"
            )

    def list_user_tokens(self, session: Session, user_id: str) -> ServiceResponse:
        """Lists all tokens for a user."""
        try:
            tokens = (
                session.execute(
                    text(
                        "SELECT token_name, agent_id, mode FROM user_tokens WHERE user_id = :uid"
                    ),
                    {"uid": user_id},
                )
                .mappings()
                .all()
            )
            return ServiceResponse.success_res(
                data=[dict(t) for t in tokens], message="Tokens listed."
            )
        except Exception as e:
            logger.error(f"Error listing tokens: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_TOKEN_LIST_ERROR"
            )

    def revoke_token(self, session: Session, token_id: str) -> ServiceResponse:
        """Revokes an API token."""
        try:
            session.execute(
                text("DELETE FROM user_tokens WHERE id = :tid"), {"tid": token_id}
            )
            session.commit()
            return ServiceResponse.success_res(message="Token revoked.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error revoking token: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_TOKEN_REVOKE_ERROR"
            )

    @command(
        name="user.invite_employee",
        description="Invites a new employee to the tenant with specific role.",
        params_model={"username": "string", "password": "string", "role": "string"},
    )
    def create_employee_account(
        self,
        session: Session,
        context: CoreContext,
        username: str,
        password: str,
        role: str = "empleado",
    ) -> ServiceResponse:
        """Invites a new employee."""
        try:
            import hashlib

            from sqlalchemy.exc import IntegrityError

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query = text(
                """
                INSERT INTO users (id, email, password_hash)
                VALUES (gen_random_uuid(), :username, :hash)
                """
            )
            session.execute(query, {"username": username, "hash": password_hash})
            session.commit()
            return ServiceResponse.success_res(
                message=f"Employee {username} created successfully."
            )
        except IntegrityError as e:
            session.rollback()
            if "users_email_key" in str(e.orig):
                return ServiceResponse.error_res(
                    f"The email/username {username} is already registered.",
                    "AUTH_EMAIL_EXISTS",
                )
            logger.error(f"Integrity error during employee creation: {e}")
            return ServiceResponse.error_res(
                f"Internal database error: {str(e)}", "AUTH_CREATE_ERROR"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating employee: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_CREATE_ERROR"
            )

    @command(
        name="user.set_permission",
        description="Assigns or revokes a granular permission key for a user.",
        params_model={
            "user_id": "string",
            "permission_key": "string",
            "granted": "boolean",
        },
    )
    def set_user_permission(
        self,
        session: Session,
        context: CoreContext,
        user_id: str,
        permission_key: str,
        granted: bool,
    ) -> ServiceResponse:
        """Sets a user permission."""
        try:
            if granted:
                query = text(
                    """
                    INSERT INTO user_permissions (user_id, permission_key) 
                    VALUES (:uid, :pk) ON CONFLICT DO NOTHING
                """
                )
            else:
                query = text(
                    "DELETE FROM user_permissions WHERE user_id = :uid AND permission_key = :pk"
                )

            session.execute(query, {"uid": user_id, "pk": permission_key})
            session.commit()
            return ServiceResponse.success_res(
                message="Permission updated successfully."
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting permission: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_PERMISSION_ERROR"
            )

    @command(
        name="user.list",
        description="Lists all users/employees of the tenant.",
        params_model={},
    )
    def list_users(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Lists users."""
        try:
            query = text("SELECT id, email, role FROM users")
            users = session.execute(query).mappings().all()
            return ServiceResponse.success_res(
                data=[dict(u) for u in users], message="Users listed."
            )
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_LIST_ERROR"
            )

    @command(
        name="user.revoke_access",
        description="Revokes access for a user.",
        params_model={"user_id": "string"},
    )
    def revoke_user_access(
        self, session: Session, context: CoreContext, user_id: str
    ) -> ServiceResponse:
        """Revokes user access."""
        try:
            session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            session.commit()
            return ServiceResponse.success_res(message="Access revoked.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error revoking access: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "AUTH_REVOKE_ERROR"
            )


# Singleton
auth_service = AuthService()
