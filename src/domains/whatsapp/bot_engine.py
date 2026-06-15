import logging
from typing import Any, Dict, cast

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

from .menu_manager import menu_manager
from .state_manager import state_manager

logger = logging.getLogger("OmniCore.BotEngine")


class BotEngine:
    """
    The Brain of the Bot.
    Orchestrates incoming messages and delegates actions to the CommandDispatcher.
    Stateless: relies on injected session and context.
    """

    def __init__(self):
        self.logger = logging.getLogger("BotEngine")

    @command(
        name="whatsapp.bot.process_message",
        description="Main entry point for bot interactions. Processes a message and returns a response.",
        params_schema={"user_id": "string", "message": "string", "context": "string"},
    )
    async def process_message(
        self, session: Session, context: CoreContext, message_data: Dict[str, Any]
    ) -> ServiceResponse:
        """
        Main entry point for every message received.
        """
        sender = message_data.get("sender")
        text = message_data.get("text", "").strip().lower()

        if not sender or not text:
            return ServiceResponse.error_res(
                "Invalid message: missing sender or text.", "INVALID_MSG"
            )

        # 1. Human Intervention Check
        if self._is_human_intervening(session, context, sender):
            return ServiceResponse.success_res(
                message="Human mode active", data={"silence": True}
            )

        # 2. Quick Global Commands
        if text == "/menu":
            return await self._handle_global_command(
                "bot.show_menu", context, {"menu_name": "main"}
            )
        if text == "volver":
            return await self._handle_global_command(
                "bot.navigate", context, {"sender": sender, "menu_name": "main"}
            )
        if text == "!humano":
            return await self._handle_global_command(
                "bot.set_human_mode", context, {"phone": sender}
            )
        if text == "!bot":
            return await self._handle_global_command(
                "bot.set_bot_mode", context, {"phone": sender}
            )

        # 3. Active Menu Management
        state = state_manager.get_state(session, context, sender)
        current_menu_name = state.get("current_menu")

        if current_menu_name:
            return await self._process_menu_option(
                session, context, sender, text, current_menu_name
            )

        # 4. Welcome
        if text in ["hola", "buenos dias", "buenas tardes", "inicio", "/start"]:
            return await self._handle_global_command("bot.welcome", context, {})

        return ServiceResponse.success_res(
            message="I didn't understand. Type '/menu' for options."
        )

    def _is_human_intervening(
        self, session: Session, context: CoreContext, sender: str
    ) -> bool:
        res = (
            session.execute(
                text(
                    "SELECT is_human_intervening FROM whatsapp_conversations WHERE phone_number = :phone"
                ),
                {"phone": sender},
            )
            .mappings()
            .first()
        )
        return res["is_human_intervening"] if res else False

    async def _process_menu_option(
        self,
        session: Session,
        context: CoreContext,
        sender: str,
        text: str,
        menu_name: str,
    ) -> ServiceResponse:
        menu = menu_manager.get_menu_by_name(session, context, menu_name)
        if not menu:
            return ServiceResponse.error_res("Menu not found.", "MENU_NOT_FOUND")

        options = menu.get("options", [])
        chosen_opt = None

        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(options):
                chosen_opt = options[idx]

        if not chosen_opt:
            for opt in options:
                if opt["label"].lower() == text:
                    chosen_opt = opt
                    break

        if not chosen_opt:
            return ServiceResponse.success_res(
                message=f"Invalid option for {menu_name}. Choose 1 to {len(options)}."
            )

        action_type = chosen_opt["action_type"]
        action_value = chosen_opt["action_value"]

        if action_type == "text":
            return ServiceResponse.success_res(message=action_value)

        if action_type == "submenu":
            # Navigation logic handled via dispatcher commands for traceability
            return await self._handle_global_command(
                "bot.navigate", context, {"sender": sender, "menu_name": action_value}
            )

        if action_type == "command":
            # This is the key: the bot delegates to the global dispatcher
            return await self._handle_global_command(
                action_value, context, params={"sender": sender}
            )

        return ServiceResponse.error_res("Action type not supported.", "ACTION_ERROR")

    async def _handle_global_command(
        self, cmd_name: str, ctx: CoreContext, params: Dict[str, Any]
    ) -> ServiceResponse:
        # In OmniCore-AI, the dispatcher is injected or accessed via the gateway
        from fastapi import Request

        from src.core.dispatcher.gateway import ai_gateway

        # Create a dummy request since the bot doesn't have a real HTTP request
        dummy_request = cast(Any, Request({}))
        # Manually set necessary attributes if the Gateway uses them
        dummy_request.method = "POST"
        dummy_request.url = "http://internal/bot"

        # In the BotEngine, the token is typically the agent_id or a fixed bot token
        token = ctx.agent_id

        return await ai_gateway.execute(
            command_name=cmd_name, token=token, params=params, request=dummy_request
        )


# Singleton
bot_engine = BotEngine()
