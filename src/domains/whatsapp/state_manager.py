import logging
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.application.conversation_management_use_case import (
    ConversationManagementUseCase,
)
from src.core.dispatcher.core_types import CoreContext, ServiceResponse

logger = logging.getLogger("OmniCore.ConversationStateManager")


class ConversationStateManager:
    """
    Thin Delegate for Conversation State Management.
    Delegates all state operations to ConversationManagementUseCase.
    """

    def __init__(self):
        pass

    def get_state(
        self, session: Session, context: CoreContext, sender: str
    ) -> Dict[str, Any]:
        return ConversationManagementUseCase(session).get_state(context, sender)

    def set_state(
        self, session: Session, context: CoreContext, sender: str, state: Dict[str, Any]
    ) -> ServiceResponse:
        return ConversationManagementUseCase(session).set_state(context, sender, state)

    def clear_state(
        self, session: Session, context: CoreContext, sender: str
    ) -> ServiceResponse:
        return ConversationManagementUseCase(session).clear_state(context, sender)


# Singleton
state_manager = ConversationStateManager()
