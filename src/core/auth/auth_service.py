import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.AuthService")


class AuthService:
    """
    Service to manage users, roles, and granular permissions (PBAC).
    Ported from plataforma-stock.
    """

    @command(
        name="user.invite_employee",
        description="Invites a new employee to the tenant with specific role.",
        params_schema={"username": "string", "password": "string", "role": "string"},
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
            # Hash password (simplified for this porting phase)
            import hashlib

            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query = text("""
                INSERT INTO users (id, email, password_hash, role) 
                VALUES (gen_random_uuid(), :username, :hash, :role)
            """)
            session.execute(
                query, {"username": username, "hash": password_hash, "role": role}
            )
            session.commit()
            return ServiceResponse.success_res(
                message=f"Employee {username} created with role {role}."
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
        params_schema={
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
                query = text("""
                    INSERT INTO user_permissions (user_id, permission_key) 
                    VALUES (:uid, :pk) ON CONFLICT DO NOTHING
                """)
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
        params_schema={},
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
        params_schema={"user_id": "string"},
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
