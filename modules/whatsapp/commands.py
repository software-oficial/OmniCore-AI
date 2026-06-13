import logging
from core.dispatcher.gateway import ai_gateway
from .whatsapp_service import whatsapp_service
from .bot_engine import bot_engine
from .state_manager import state_manager
from .menu_manager import menu_manager
from . import bot_commands

logger = logging.getLogger("OmniCore.WhatsappCommands")

def register_whatsapp_commands():
    """
    Registers WhatsApp and Bot functions into the AIGateway.
    Exposes conversation and state logic with full semantic metadata.
    """
    # Core Bot Engine
    ai_gateway.register_command(
        "whatsapp.bot.process_message", bot_engine.process_message, 
        description="Main entry point for bot interactions. Processes a message and returns a response.",
        params_schema={"user_id": "string", "message": "string", "context": "string"}
    )

    # Bot Orchestration (NEW: Fixing State Persistence)
    ai_gateway.register_command(
        "whatsapp.bot.navigate", bot_commands.bot_navigate, 
        description="Changes the current menu state for a user and returns the new menu content.",
        params_schema={"sender": "string", "menu_name": "string"}
    )
    ai_gateway.register_command(
        "whatsapp.bot.welcome", bot_commands.bot_welcome, 
        description="Initiates conversation and sets state to main menu.",
        params_schema={"sender": "string"}
    )
    ai_gateway.register_command(
        "whatsapp.bot.show_menu", bot_commands.bot_show_menu, 
        description="Displays a menu without changing state.",
        params_schema={"menu_name": "string"}
    )
    ai_gateway.register_command(
        "whatsapp.bot.set_human_mode", bot_commands.bot_set_human_mode, 
        description="Activates human intervention mode for a phone number.",
        params_schema={"phone": "string"}
    )
    ai_gateway.register_command(
        "whatsapp.bot.set_bot_mode", bot_commands.bot_set_bot_mode, 
        description="Returns control to the bot for a phone number.",
        params_schema={"phone": "string"}
    )

    # State Management
    ai_gateway.register_command(
        "whatsapp.bot.state.get", state_manager.get_state, 
        description="Retrieves the current conversation state for a specific user.",
        params_schema={"user_id": "string", "key": "string"}
    )
    ai_gateway.register_command(
        "whatsapp.bot.state.set", state_manager.set_state, 
        description="Saves a value in the conversation state for a specific user.",
        params_schema={"user_id": "string", "key": "string", "value": "any"}
    )
    ai_gateway.register_command(
        "whatsapp.bot.state.clear", state_manager.clear_state, 
        description="Wipes all saved state for a specific user (reset conversation).",
        params_schema={"user_id": "string"}
    )

    # Menu Management
    ai_gateway.register_command(
        "whatsapp.bot.menu.list", menu_manager.get_all_menus, 
        description="Returns all configured menus in the tenant DB.",
        params_schema={}
    )
    ai_gateway.register_command(
        "whatsapp.bot.menu.get", menu_manager.get_menu_by_name, 
        description="Retrieves the structure of a specific menu by name.",
        params_schema={"menu_name": "string"}
    )

    # WhatsApp Service (Basic Gateway)
    ai_gateway.register_command(
        "whatsapp.service.process_message", whatsapp_service.process_incoming_message, 
        description="Low-level gateway to process raw incoming WhatsApp messages.",
        params_schema={"payload": "dict"}
    )


    logger.info("💬 WhatsApp and Bot commands registered successfully with full metadata.")


