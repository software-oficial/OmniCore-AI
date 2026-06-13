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
    """
    # Core Bot Engine
    ai_gateway.register_command("bot.process_message", bot_engine.process_message)

    # State Management
    ai_gateway.register_command("bot.state.get", state_manager.get_state)
    ai_gateway.register_command("bot.state.set", state_manager.set_state)
    ai_gateway.register_command("bot.state.clear", state_manager.clear_state)

    # Menu Management
    ai_gateway.register_command("bot.menu.list", menu_manager.get_all_menus)
    ai_gateway.register_command("bot.menu.get", menu_manager.get_menu_by_name)

    # WhatsApp Service (Basic Gateway)
    ai_gateway.register_command("wa.process_message", whatsapp_service.process_incoming_message)

    logger.info("💬 WhatsApp and Bot commands registered successfully.")

