import logging

from sqlalchemy.orm import Session

from src.application.conversation_management_use_case import (
    ConversationManagementUseCase,
)
from src.application.message_delivery_use_case import MessageDeliveryUseCase
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.infrastructure.repositories.whatsapp_repository import WhatsappRepository

logger = logging.getLogger("OmniCore.WhatsappService")


class WhatsappService:
    """
    Thin Delegate for WhatsApp Bot Orchestration.
    Orchestrates delivery, conversation management and settings.
    """

    @command(
        name="whatsapp.send_text",
        description="Sends a plain text message via WhatsApp Business API.",
        params_model={
            "to": "string",
            "body": "string",
            "sender_type": "string",
            "credential_id": "string",
        },
        api_provider="whatsapp",
    )
    def send_text(
        self,
        session: Session,
        context: CoreContext,
        to: str,
        body: str,
        sender_type: str = "bot",
    ) -> ServiceResponse:
        return MessageDeliveryUseCase(session, context).send_text_message(
            to, body, sender_type
        )

    @command(
        name="whatsapp.upload_media",
        description="Uploads a file to Meta servers.",
        params_model={
            "filename": "string",
            "mime_type": "string",
            "file_content": "bytes",
            "credential_id": "string",
        },
        api_provider="whatsapp",
    )
    def upload_media(
        self,
        session: Session,
        context: CoreContext,
        filename: str,
        mime_type: str,
        file_content: bytes,
    ) -> ServiceResponse:
        return MessageDeliveryUseCase(session, context).upload_media_file(
            filename, mime_type, file_content
        )

    @command(
        name="whatsapp.send_media",
        description="Sends a previously uploaded media file.",
        params_model={
            "to": "string",
            "media_id": "string",
            "media_type": "string",
            "caption": "string",
            "filename": "string",
            "credential_id": "string",
        },
        api_provider="whatsapp",
    )
    def send_media(
        self,
        session: Session,
        context: CoreContext,
        to: str,
        media_id: str,
        media_type: str,
        caption: str = "",
        filename: str = "",
        sender_type: str = "bot",
    ) -> ServiceResponse:
        return MessageDeliveryUseCase(session, context).send_media_message(
            to, media_id, media_type, caption, filename, sender_type
        )

    @command(
        name="whatsapp.log_message",
        description="Logs a message interaction in the business database.",
        params_model={
            "phone_number": "string",
            "sender": "string",
            "content": "string",
            "message_type": "string",
            "credential_id": "string",
        },
    )
    def log_message(
        self,
        session: Session,
        context: CoreContext,
        phone_number: str,
        sender: str,
        content: str,
        message_type: str = "text",
    ) -> ServiceResponse:
        try:
            WhatsappRepository(session).log_interaction(
                phone_number,
                context.credential_id or "default",
                sender,
                content,
                message_type,
            )
            return ServiceResponse.success_res(message="Message logged successfully.")
        except Exception as e:
            return ServiceResponse.error_res(f"Log failure: {str(e)}", "DB_ERROR")

    @command(
        name="whatsapp.set_human_mode",
        description="Toggles the human intervention mode.",
        params_model={
            "phone_number": "string",
            "status": "boolean",
            "credential_id": "string",
        },
    )
    def set_human_mode(
        self, session: Session, context: CoreContext, phone_number: str, status: bool
    ) -> ServiceResponse:
        return ConversationManagementUseCase(session).toggle_human_mode(
            phone_number, status, context.credential_id or "default"
        )

    @command(
        name="whatsapp.get_status",
        description="Retrieves the current state of a WhatsApp conversation.",
        params_model={"phone_number": "string", "credential_id": "string"},
    )
    def get_status(
        self, session: Session, context: CoreContext, phone_number: str
    ) -> ServiceResponse:
        return ConversationManagementUseCase(session).get_conversation_status(
            phone_number, context.credential_id or "default"
        )

    @command(
        name="whatsapp.handle_bot_flow",
        description="Processes an incoming message and determines response.",
        params_model={
            "phone_number": "string",
            "text": "string",
            "credential_id": "string",
        },
    )
    def handle_bot_flow(
        self,
        session: Session,
        context: CoreContext,
        phone_number: str,
        text_content: str,
    ) -> ServiceResponse:
        from src.application.bot_orchestration_use_case import BotOrchestrationUseCase

        return BotOrchestrationUseCase(session).process_incoming_message(
            context, phone_number, text_content
        )


# Singleton
whatsapp_service = WhatsappService()
