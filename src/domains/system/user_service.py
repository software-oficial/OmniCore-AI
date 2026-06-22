import logging

from sqlalchemy.orm import Session

from src.application.user_management_use_case import UserManagementUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.infrastructure.repositories.user_repository import UserRepository

logger = logging.getLogger("OmniCore.UserService")


class UserService:
    """
    Domain Layer: Exposes employee and permission management as executable commands.
    Allows the owner to build their team and define granular access controls.
    """

    @command(
        name="system.users.create",
        description="Creates a new employee user in the business database.",
        params_model={"username": "string", "password": "string", "role": "string"},
    )
    def create_user(
        self,
        session: Session,
        context: CoreContext,
        username: str,
        password: str,
        role: str = "employee",
    ) -> ServiceResponse:
        """
        Instantiates the use case and creates a new user.
        """
        try:
            return UserManagementUseCase(session, context).create_employee(
                username, password, role
            )
        except Exception as e:
            logger.error(f"Error in create_user command for {username}: {e}")
            return ServiceResponse.error_res(
                f"Unexpected error during user creation: {str(e)}", "USER_CREATE_ERROR"
            )

    @command(
        name="system.users.update_role",
        description="Updates the role of an existing employee.",
        params_model={"username": "string", "role": "string"},
    )
    def update_role(
        self, session: Session, context: CoreContext, username: str, role: str
    ) -> ServiceResponse:
        """
        Updates the user's role (e.g., employee -> manager).
        """
        try:
            return UserManagementUseCase(session, context).change_role(username, role)
        except Exception as e:
            logger.error(f"Error in update_role command for {username}: {e}")
            return ServiceResponse.error_res(
                f"Unexpected error updating role: {str(e)}", "USER_ROLE_ERROR"
            )

    @command(
        name="system.users.grant_permission",
        description="Grants a specific permission key to a user.",
        params_model={"username": "string", "permission_key": "string"},
    )
    def grant_permission(
        self, session: Session, context: CoreContext, username: str, permission_key: str
    ) -> ServiceResponse:
        """
        Grants a granular permission to the user.
        """
        try:
            return UserManagementUseCase(session, context).grant_permission(
                username, permission_key
            )
        except Exception as e:
            logger.error(f"Error in grant_permission command for {username}: {e}")
            return ServiceResponse.error_res(
                f"Unexpected error granting permission: {str(e)}", "PERM_GRANT_ERROR"
            )

    @command(
        name="system.users.revoke_permission",
        description="Revokes a specific permission key from a user.",
        params_model={"username": "string", "permission_key": "string"},
    )
    def revoke_permission(
        self, session: Session, context: CoreContext, username: str, permission_key: str
    ) -> ServiceResponse:
        """
        Revokes a granular permission from the user.
        """
        try:
            return UserManagementUseCase(session, context).revoke_permission(
                username, permission_key
            )
        except Exception as e:
            logger.error(f"Error in revoke_permission command for {username}: {e}")
            return ServiceResponse.error_res(
                f"Unexpected error revoking permission: {str(e)}", "PERM_REVOKE_ERROR"
            )

    @command(
        name="system.users.list",
        description="Lists all employees and their assigned permissions.",
        params_model={},
    )
    def list_users(self, session: Session, context: CoreContext) -> ServiceResponse:
        """
        Returns a comprehensive list of users and their current access levels.
        """
        try:
            repo = UserRepository(session, context.business_id)
            users = repo.list_users()

            detailed_users = []
            for user in users:
                user_data = dict(user)
                user_data["permissions"] = repo.get_user_permissions(user["id"])
                detailed_users.append(user_data)

            return ServiceResponse.success_res(
                data=detailed_users, message="Employee list retrieved successfully."
            )
        except Exception as e:
            logger.error(f"Error listing users for app {context.app_id}: {e}")
            return ServiceResponse.error_res(
                f"Error retrieving team: {str(e)}", "USER_LIST_ERROR"
            )


# Singleton
user_service = UserService()
