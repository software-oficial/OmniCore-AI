import logging

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.UserManagementUseCase")


class UserManagementUseCase:
    """
    Application Layer: Manages employee users and their granular permissions.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SalesRepository(session)

    def create_employee(
        self, username: str, password: str, role: str = "employee"
    ) -> ServiceResponse:
        try:
            self.repo.create_user(username, password)
            return ServiceResponse.success_res(
                message=f"Employee {username} created successfully."
            )
        except Exception as e:
            logger.error(f"Error creating employee {username}: {e}")
            return ServiceResponse.error_res(
                f"User creation failed: {str(e)}", "USER_CREATE_ERROR"
            )

    def change_role(self, username: str, new_role: str) -> ServiceResponse:
        try:
            count = self.repo.update_user_role(username, new_role)
            if count == 0:
                return ServiceResponse.error_res("User not found", "USER_NOT_FOUND")
            return ServiceResponse.success_res(
                message=f"Role for {username} updated to {new_role}."
            )
        except Exception as e:
            logger.error(f"Error updating role for {username}: {e}")
            return ServiceResponse.error_res(
                f"Update failed: {str(e)}", "USER_ROLE_ERROR"
            )

    def grant_permission(self, username: str, permission_key: str) -> ServiceResponse:
        try:
            user = self.repo.get_user_by_username(username)
            if not user:
                return ServiceResponse.error_res("User not found", "USER_NOT_FOUND")

            self.repo.grant_permission(user["id"], permission_key)
            return ServiceResponse.success_res(
                message=f"Permission {permission_key} granted to {username}."
            )
        except Exception as e:
            logger.error(f"Error granting permission to {username}: {e}")
            return ServiceResponse.error_res(f"Grant failed: {str(e)}", "PERM_ERROR")

    def revoke_permission(self, username: str, permission_key: str) -> ServiceResponse:
        try:
            user = self.repo.get_user_by_username(username)
            if not user:
                return ServiceResponse.error_res("User not found", "USER_NOT_FOUND")

            self.repo.revoke_permission(user["id"], permission_key)
            return ServiceResponse.success_res(
                message=f"Permission {permission_key} revoked from {username}."
            )
        except Exception as e:
            logger.error(f"Error revoking permission from {username}: {e}")
            return ServiceResponse.error_res(
                f"Revocation failed: {str(e)}", "PERM_ERROR"
            )
