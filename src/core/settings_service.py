import logging
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.cache.redis_manager import cache_manager

logger = logging.getLogger("OmniCore.SettingsService")


class SettingsService:
    """
    Service for managing dynamic business settings stored in the client's database.
    Allows real-time configuration changes without server restarts.
    """

    def get_setting(self, session: Session, key: str, default: Any = None) -> Any:
        """
        Retrieves a specific setting value by its key.
        """
        try:
            query = text(
                "SELECT setting_value FROM business_settings WHERE setting_key = :key"
            )
            result = session.execute(query, {"key": key}).fetchone()

            if result:
                return result[0]
            return default
        except Exception as e:
            logger.error(f"Error retrieving setting {key}: {e}")
            return default

    def set_setting(
        self,
        session: Session,
        app_id: str,
        key: str,
        value: Any,
        description: Optional[str] = None,
    ) -> bool:
        """
        Creates or updates a business setting and invalidates the cache.
        """
        try:
            exists = self.get_setting(session, key)
            if exists is not None:
                query = text(
                    "UPDATE business_settings SET setting_value = :value, updated_at = CURRENT_TIMESTAMP WHERE setting_key = :key"
                )
                session.execute(query, {"value": str(value), "key": key})
            else:
                query = text(
                    "INSERT INTO business_settings (setting_key, setting_value, description) VALUES (:key, :value, :desc)"
                )
                session.execute(
                    query, {"key": key, "value": str(value), "desc": description}
                )

            session.commit()

            # Invalidate cache
            (
                cache_manager.client.delete(f"settings:{app_id}")
                if cache_manager.is_available()
                else None
            )

            return True
        except Exception as e:
            logger.error(f"Error saving setting {key}: {e}")
            return False

    def get_all_settings(self, session: Session, app_id: str) -> Dict[str, Any]:
        """
        Retrieves all configured settings for the current business instance using Cache-Aside pattern.
        """
        cache_key = f"settings:{app_id}"

        # 1. Try to get from cache
        cached_settings = cache_manager.get(cache_key)
        if cached_settings is not None:
            return cached_settings

        # 2. Fallback to DB
        try:
            query = text("SELECT setting_key, setting_value FROM business_settings")
            results = session.execute(query).all()
            settings = {row[0]: row[1] for row in results}

            # 3. Save to cache (TTL 1 hour)
            cache_manager.set(cache_key, settings, ttl=3600)

            return settings
        except Exception as e:
            logger.error(f"Error fetching all settings for app {app_id}: {e}")
            return {}

    def delete_setting(self, session: Session, app_id: str, key: str) -> bool:
        """
        Removes a setting from the database and invalidates the cache.
        """
        try:
            query = text("DELETE FROM business_settings WHERE setting_key = :key")
            session.execute(query, {"key": key})
            session.commit()

            # Invalidate cache
            (
                cache_manager.client.delete(f"settings:{app_id}")
                if cache_manager.is_available()
                else None
            )

            return True
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            return False


# Singleton
settings_service = SettingsService()
