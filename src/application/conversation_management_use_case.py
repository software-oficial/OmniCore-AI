import json
import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.cache.redis_manager import cache_manager
from src.infrastructure.repositories.whatsapp_repository import WhatsappRepository

logger = logging.getLogger("OmniCore.ConversationManagementUseCase")


class ConversationManagementUseCase:
    """
    Application Layer: Manages conversation state, human intervention, and user context.
    """

    def __init__(self, session: Session):
        self.repo = WhatsappRepository(session)
        self.cache = cache_manager

    def toggle_human_mode(self, phone_number: str, status: bool) -> ServiceResponse:
        try:
            self.repo.set_human_mode(phone_number, status)
            return ServiceResponse.success_res(
                message=f"Conversation mode updated to {'Human' if status else 'Bot'}."
            )
        except Exception as e:
            logger.error(f"Error updating human mode for {phone_number}: {e}")
            return ServiceResponse.error_res(f"Update failed: {str(e)}", "DB_ERROR")

    def get_conversation_status(self, phone_number: str) -> ServiceResponse:
        try:
            conv = self.repo.get_conversation(phone_number)
            if not conv:
                return ServiceResponse.error_res("Conversation not found", "NOT_FOUND")

            return ServiceResponse.success_res(
                data=dict(conv), message="Conversation status retrieved."
            )
        except Exception as e:
            logger.error(f"Error getting status for {phone_number}: {e}")
            return ServiceResponse.error_res(f"Retrieval failed: {str(e)}", "DB_ERROR")

    def get_state(self, context: CoreContext, sender: str) -> Dict[str, Any]:
        """Hybrid state recovery: Redis L1 -> DB L2."""
        cache_key = f"bot_state:{context.app_id}:{sender}"
        try:
            cached_state = self.cache.get_session_context(cache_key)
            if cached_state:
                return cached_state

            state_json = self.repo.get_state(sender)
            if state_json:
                state_data = json.loads(state_json)
                self.cache.set_session_context(cache_key, state_data, ttl=3600)
                return state_data

            return {}
        except Exception as e:
            logger.error(f"Error recovering state for {sender}: {e}")
            return {}

    def set_state(
        self, context: CoreContext, sender: str, state: Dict[str, Any]
    ) -> ServiceResponse:
        """Hybrid state persistence: Redis L1 + DB L2."""
        try:
            cache_key = f"bot_state:{context.app_id}:{sender}"
            self.cache.set_session_context(cache_key, state, ttl=3600)

            self.repo.save_state(sender, json.dumps(state))
            return ServiceResponse.success_res(message="State updated and persisted.")
        except Exception as e:
            logger.error(f"Error saving state for {sender}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STATE_SAVE_ERROR"
            )

    def clear_state(self, context: CoreContext, sender: str) -> ServiceResponse:
        try:
            cache_key = f"bot_state:{context.app_id}:{sender}"
            if self.cache.client:
                self.cache.client.delete(cache_key)

            self.repo.delete_state(sender)
            return ServiceResponse.success_res(message="State cleared.")
        except Exception as e:
            logger.error(f"Error clearing state for {sender}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STATE_CLEAR_ERROR"
            )
