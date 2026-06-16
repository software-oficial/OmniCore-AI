import logging
from typing import Any, Dict, cast

from sqlalchemy.orm import Session

from src.application.bot_orchestration_use_case import BotOrchestrationUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.BotEngine")


class BotEngine:
    """
    The Brain of the Bot.
    Delegates message processing to the BotOrchestrationUseCase.
    """

    def __init__(self):
        self.logger = logging.getLogger("BotEngine")

    @command(
        name="whatsapp.bot.process_message",
        description="Main entry point for bot interactions. Processes a message and returns a response.",
        params_model={"user_id": "string", "message": "string", "context": "string"},
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

        # 1. Quick Global Commands (Direct Dispatcher calls)
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

        # 2. Delegate everything else to the Orchestration Use Case
        return BotOrchestrationUseCase(session).process_incoming_message(
            context, sender, text
        )

    async def _handle_global_command(
        self, cmd_name: str, ctx: CoreContext, params: Dict[str, Any]
    ) -> ServiceResponse:
        from fastapi import Request

        from src.core.dispatcher.gateway import ai_gateway

        dummy_request = cast(Any, Request({}))
        dummy_request.method = "POST"
        dummy_request.url = "http://internal/bot"

        token = ctx.agent_id

        return await ai_gateway.execute(
            command_name=cmd_name, token=token, params=params, request=dummy_request
        )


# Singleton
bot_engine = BotEngine()
