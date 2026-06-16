import logging

from sqlalchemy.orm import Session

from src.application.conversation_management_use_case import (
    ConversationManagementUseCase,
)
from src.application.menu_management_use_case import MenuManagementUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.infrastructure.repositories.whatsapp_repository import WhatsappRepository

logger = logging.getLogger("OmniCore.BotCommands")


@command(
    name="bot.navigate",
    description="Handles navigation between menus. Updates user state and returns the new menu.",
    params_model={"sender": "string", "menu_name": "string"},
)
def bot_navigate(
    session: Session, context: CoreContext, sender: str, menu_name: str
) -> ServiceResponse:
    """
    Handles navigation between menus. Updates user state and returns the new menu.
    """
    try:
        # 1. Update state in DB
        WhatsappRepository(session).update_conversation_menu(sender, menu_name)

        # 2. Retrieve and format the menu
        return MenuManagementUseCase(session).get_formatted_menu(menu_name)
    except Exception as e:
        logger.error(f"Error in bot_navigate: {e}")
        return ServiceResponse.error_res(f"Navigation error: {str(e)}", "NAV_ERROR")


@command(
    name="bot.welcome",
    description="Initiates the conversation, sets initial state to 'main' menu, and welcomes the user.",
    params_model={"sender": "string"},
)
def bot_welcome(
    session: Session, context: CoreContext, sender: str = "unknown"
) -> ServiceResponse:
    """
    Initiates the conversation, sets initial state to 'main' menu, and welcomes the user.
    """
    return bot_navigate(session, context, sender, "main")


@command(
    name="bot.show_menu",
    description="Shows a specific menu without necessarily changing the state.",
    params_model={"menu_name": "string"},
)
def bot_show_menu(
    session: Session, context: CoreContext, menu_name: str = "main"
) -> ServiceResponse:
    """
    Shows a specific menu without necessarily changing the state.
    """
    return MenuManagementUseCase(session).get_formatted_menu(menu_name)


@command(
    name="bot.set_human_mode",
    description="Sets the conversation to human intervention mode.",
    params_model={"phone": "string"},
)
def bot_set_human_mode(
    session: Session, context: CoreContext, phone: str
) -> ServiceResponse:
    """Sets the conversation to human intervention mode."""
    return ConversationManagementUseCase(session).toggle_human_mode(phone, True)


@command(
    name="bot.set_bot_mode",
    description="Sets the conversation back to bot mode.",
    params_model={"phone": "string"},
)
def bot_set_bot_mode(
    session: Session, context: CoreContext, phone: str
) -> ServiceResponse:
    """Sets the conversation back to bot mode."""
    return ConversationManagementUseCase(session).toggle_human_mode(phone, False)
