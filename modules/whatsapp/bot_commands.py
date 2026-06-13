import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse
from .state_manager import state_manager
from .menu_manager import menu_manager

logger = logging.getLogger("OmniCore.BotCommands")

def bot_navigate(session: Session, context: CoreContext, sender: str, menu_name: str) -> ServiceResponse:
    """
    Handles navigation between menus. Updates user state and returns the new menu.
    """
    try:
        # 1. Update State to the new menu
        current_state = state_manager.get_state(session, context, sender)
        current_state["current_menu"] = menu_name
        state_manager.set_state(session, context, sender, current_state)

        # 2. Retrieve the Menu Content
        menu = menu_manager.get_menu_by_name(session, context, menu_name)
        if not menu:
            return ServiceResponse.error_res(f"Menu '{menu_name}' not found.", "MENU_NOT_FOUND")

        # 3. Format the response (Same logic as whatsapp_service)
        options = menu.get('options', [])
        options_list = [f"{i+1}. {opt['label']}" for i, opt in enumerate(options)]
        options_text = " | ".join(options_list)
        
        full_text = f"{menu['text']}

Options: {options_text}"
        
        return ServiceResponse.success_res(
            data={"current_menu": menu_name},
            message=full_text
        )
    except Exception as e:
        logger.error(f"Error in bot_navigate: {e}")
        return ServiceResponse.error_res(f"Navigation error: {str(e)}", "NAV_ERROR")

def bot_welcome(session: Session, context: CoreContext, sender: str = "unknown") -> ServiceResponse:
    """
    Initiates the conversation, sets initial state to 'main' menu, and welcomes the user.
    """
    try:
        # Default to main menu
        return bot_navigate(session, context, sender, "main")
    except Exception as e:
        logger.error(f"Error in bot_welcome: {e}")
        return ServiceResponse.error_res("Welcome error", "WELCOME_ERROR")

def bot_show_menu(session: Session, context: CoreContext, menu_name: str = "main") -> ServiceResponse:
    """
    Shows a specific menu without necessarily changing the state.
    """
    try:
        menu = menu_manager.get_menu_by_name(session, context, menu_name)
        if not menu:
            return ServiceResponse.error_res(f"Menu '{menu_name}' not found.", "MENU_NOT_FOUND")

        options = menu.get('options', [])
        options_list = [f"{i+1}. {opt['label']}" for i, opt in enumerate(options)]
        options_text = " | ".join(options_list)
        
        return ServiceResponse.success_res(
            message=f"""{menu['text']}

Options: {options_text}"""
        )

    except Exception as e:
        logger.error(f"Error in bot_show_menu: {e}")
        return ServiceResponse.error_res("Menu display error", "DISPLAY_ERROR")

def bot_set_human_mode(session: Session, context: CoreContext, phone: str) -> ServiceResponse:
    """Sets the conversation to human intervention mode."""
    try:
        session.execute(
            text("UPDATE whatsapp_conversations SET is_human_intervening = TRUE WHERE phone_number = :phone"),
            {"phone": phone}
        )
        session.commit()
        return ServiceResponse.success_res(message=f"Conversation {phone} transferred to human agent.")
    except Exception as e:
        logger.error(f"Error setting human mode: {e}")
        return ServiceResponse.error_res("Mode change error", "MODE_ERROR")

def bot_set_bot_mode(session: Session, context: CoreContext, phone: str) -> ServiceResponse:
    """Sets the conversation back to bot mode."""
    try:
        session.execute(
            text("UPDATE whatsapp_conversations SET is_human_intervening = FALSE WHERE phone_number = :phone"),
            {"phone": phone}
        )
        session.commit()
        return ServiceResponse.success_res(message=f"Conversation {phone} returned to bot control.")
    except Exception as e:
        logger.error(f"Error setting bot mode: {e}")
        return ServiceResponse.error_res("Mode change error", "MODE_ERROR")
