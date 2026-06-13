import logging
from core.dispatcher.gateway import ai_gateway
from .whatsapp_service import whatsapp_service
from .bot_engine import bot_engine
from .state_manager import state_manager
from .menu_manager import menu_manager

logger = logging.getLogger("OmniCore.WhatsappCommands")

def register_whatsapp_commands():
    """
    Registers WhatsApp and Bot functions into the AIGateway.
    Exposes conversation and state logic with full semantic metadata.
    """
    # Core Bot Engine
    ai_gateway.register_command(
        "bot.process_message", bot_engine.process_message, 
        description="Main entry point for bot interactions. Processes a message and returns a response.",
        params_schema={"user_id": "string", "message": "string", "context": "string"}
    )

    # State Management
    ai_gateway.register_command(
        "bot.state.get", state_manager.get_state, 
        description="Retrieves the current conversation state for a specific user.",
        params_schema={"user_id": "string", "key": "string"}
    )
    ai_gateway.register_command(
        "bot.state.set", state_manager.set_state, 
        description="Saves a value in the conversation state for a specific user.",
        params_schema={"user_id": "string", "key": "string", "value": "any"}
    )
    ai_gateway.register_command(
        "bot.state.clear", state_manager.clear_state, 
        description="Wipes all saved state for a specific user (reset conversation).",
        params_schema={"user_id": "string"}
    )

    # Menu Management
    ai_gateway.register_command(
        "bot.menu.list", menu_manager.get_all_menus, 
        description="Returns all available conversation menus and their structures.",
        params_schema={}
    )
    ai_gateway.register_command(
        "bot.menu.get", menu_manager.get_menu_by_name, 
        description="Retrieves the structure of a specific menu by its name.",
        params_schema={"menu_name": "string"}
    )

    # WhatsApp Service (Basic Gateway)
    ai_gateway.register_command(
        "wa.process_message", whatsapp_service.process_incoming_message, 
        description="Low-level gateway to process raw incoming WhatsApp messages.",
        params_schema={"payload": "dict"}
    )

    logger.info("💬 WhatsApp and Bot commands registered successfully with full metadata.")

