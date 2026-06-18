import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.core.settings_service import settings_service

logger = logging.getLogger("OmniCore.SystemSettingsService")


class SystemSettingsService:
    """
    Domain Layer: Exposes business settings management as executable commands.
    These commands allow the owner to configure their business instance dynamically.
    """

    @command(
        name="system.settings.get",
        description="Retrieves all dynamic business settings for the current application.",
        params_model={},
    )
    def get_settings(self, session: Session, context: CoreContext) -> ServiceResponse:
        """
        Fetches all settings from the database (or cache).
        """
        try:
            settings = settings_service.get_all_settings(session, context.app_id)
            return ServiceResponse.success_res(
                data=settings, message="Business settings retrieved successfully."
            )
        except Exception as e:
            logger.error(f"Failed to retrieve settings for app {context.app_id}: {e}")
            return ServiceResponse.error_res(
                f"Error retrieving settings: {str(e)}", "SETTINGS_GET_ERROR"
            )

    @command(
        name="system.settings.set",
        description="Updates or creates a business setting.",
        params_model={"key": "string", "value": "string", "description": "string"},
    )
    def set_setting(
        self,
        session: Session,
        context: CoreContext,
        key: str,
        value: str,
        description: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Sets a configuration value and invalidates the cache.
        """
        try:
            success = settings_service.set_setting(
                session=session,
                app_id=context.app_id,
                key=key,
                value=value,
                description=description,
            )
            if success:
                return ServiceResponse.success_res(
                    message=f"Setting '{key}' has been updated."
                )
            return ServiceResponse.error_res(
                "Failed to update setting", "SETTINGS_SET_ERROR"
            )
        except Exception as e:
            logger.error(f"Error setting {key} for app {context.app_id}: {e}")
            return ServiceResponse.error_res(
                f"Error updating setting: {str(e)}", "SETTINGS_SET_ERROR"
            )

    @command(
        name="system.settings.delete",
        description="Removes a business setting.",
        params_model={"key": "string"},
    )
    def delete_setting(
        self, session: Session, context: CoreContext, key: str
    ) -> ServiceResponse:
        """
        Deletes a setting and invalidates the cache.
        """
        try:
            success = settings_service.delete_setting(
                session=session, app_id=context.app_id, key=key
            )
            if success:
                return ServiceResponse.success_res(
                    message=f"Setting '{key}' deleted successfully."
                )
            return ServiceResponse.error_res(
                "Failed to delete setting", "SETTINGS_DEL_ERROR"
            )
        except Exception as e:
            logger.error(f"Error deleting {key} for app {context.app_id}: {e}")
            return ServiceResponse.error_res(
                f"Error deleting setting: {str(e)}", "SETTINGS_DEL_ERROR"
            )


# Singleton
system_settings_service = SystemSettingsService()
