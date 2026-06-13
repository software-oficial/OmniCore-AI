import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse
from .state_manager import state_manager
from .menu_manager import menu_manager

logger = logging.getLogger("OmniCore.BotEngine")

class BotEngine:
    """
    The Brain of the Bot.
    Orchestrates incoming messages and delegates actions to the CommandDispatcher.
    Stateless: relies on injected session and context.
    """
    def __init__(self):
        self.logger = logging.getLogger("BotEngine")

    def process_message(self, session: Session, context: CoreContext, message_data: Dict[str, Any]) -> ServiceResponse:
        """
        Main entry point for every message received.
        """
        sender = message_data.get("sender")
        text = message_data.get("text", "").strip().lower()
        msg_id = message_data.get("message_id")

        if not sender or not text:
            return ServiceResponse.error_res("Invalid message: missing sender or text.", "INVALID_MSG")

        # 1. Human Intervention Check
        if self._is_human_intervening(session, context, sender):
            return ServiceResponse.success_res(message="Human mode active", data={"silence": True})

        # 2. Quick Global Commands
        if text == "/menu":
            return self._handle_global_command("bot.show_menu", context, {"menu_name": "main"})
        if text == "volver":
            return self._handle_global_command("bot.navigate", context, {"sender": sender, "menu_name": "main"})
        if text == "!humano":
            return self._handle_global_command("bot.set_human_mode", context, {"phone": sender})
        if text == "!bot":
            return self._handle_global_command("bot.set_bot_mode", context, {"phone": sender})

        # 3. Active Menu Management
        state = state_manager.get_state(session, context, sender)
        current_menu_name = state.get("current_menu")

        if current_menu_name:
            return self._process_menu_option(session, context, sender, text, current_menu_name)

        # 4. Welcome
        if text in ["hola", "buenos dias", "buenas tardes", "inicio", "/start"]:
            return self._handle_global_command("bot.welcome", context, {})

        return ServiceResponse.success_res(
            message="I didn't understand. Type '/menu' for options."
        )

    def _is_human_intervening(self, session: Session, context: CoreContext, sender: str) -> bool:
        res = session.execute(
            text("SELECT is_human_intervening FROM whatsapp_conversations WHERE phone_number = :phone"),
            {"phone": sender}
        ).mappings().first()
        return res['is_human_intervening'] if res else False

    def _process_menu_option(self, session: Session, context: CoreContext, sender: str, text: str, menu_name: str) -> ServiceResponse:
        menu = menu_manager.get_menu_by_name(session, context, menu_name)
        if not menu:
            return ServiceResponse.error_res("Menu not found.", "MENU_NOT_FOUND")

        options = menu.get('options', [])
        chosen_opt = None
        
        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(options):
                chosen_opt = options[idx]
        
        if not chosen_opt:
            for opt in options:
                if opt['label'].lower() == text:
                    chosen_opt = opt
                    break

        if not chosen_opt:
            return ServiceResponse.success_res(
                message=f"Invalid option for {menu_name}. Choose 1 to {len(options)}."
            )

        action_type = chosen_opt['action_type']
        action_value = chosen_opt['action_value']

        if action_type == "text":
            return ServiceResponse.success_res(message=action_value)
        
        if action_type == "submenu":
            # Navigation logic handled via dispatcher commands for traceability
            return self._handle_global_command("bot.navigate", context, {"sender": sender, "menu_name": action_value})
        
        if action_type == "command":
            # This is the key: the bot delegates to the global dispatcher
            return self._handle_global_command(action_value, context, params={"sender": sender})

        return ServiceResponse.error_res("Action type not supported.", "ACTION_ERROR")

    def _handle_global_command(self, cmd_name: str, ctx: CoreContext, params: Dict[str, Any]) -> ServiceResponse:
        # In OmniCore-AI, the dispatcher is injected or accessed via the gateway
        from core.dispatcher.gateway import ai_gateway
        return ai_gateway.execute(cmd_name, ctx, params=params)

# Singleton
bot_engine = BotEngine()
