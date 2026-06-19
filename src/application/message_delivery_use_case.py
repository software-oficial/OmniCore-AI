import logging

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.gateways.whatsapp_api_gateway import WhatsappApiGateway
from src.infrastructure.repositories.whatsapp_repository import WhatsappRepository

logger = logging.getLogger("OmniCore.MessageDeliveryUseCase")


class MessageDeliveryUseCase:
    """
    Application Layer: Orchestrates the sending of messages and their auditing.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = WhatsappRepository(session)

        # Extract dynamic credentials from CoreContext
        whatsapp_cred = context.active_credentials.get("whatsapp", {})
        token = whatsapp_cred.get("api_key", "")
        phone_id = (
            whatsapp_cred.get("metadata", {}).get("phone_id", "")
            if isinstance(whatsapp_cred.get("metadata"), dict)
            else None
        )

        # Support for JSON-encoded metadata in DB
        if not phone_id and whatsapp_cred.get("metadata"):
            try:
                import json

                meta = json.loads(whatsapp_cred.get("metadata"))
                phone_id = meta.get("phone_id")
            except Exception:
                pass

        self.api = WhatsappApiGateway(token=token, phone_id=phone_id)

    def send_text_message(
        self, to: str, body: str, sender_type: str = "bot"
    ) -> ServiceResponse:
        try:
            self.api.send_text(to, body)
            self.repo.log_interaction(
                to, self.context.credential_id or "default", sender_type, body, "text"
            )
            return ServiceResponse.success_res(
                data={"to": to, "status": "sent"}, message="Message sent."
            )
        except Exception as e:
            logger.error(f"Delivery error for {to}: {e}")
            return ServiceResponse.error_res(
                f"Delivery failed: {str(e)}", "DELIVERY_ERROR"
            )

    def send_media_message(
        self,
        to: str,
        media_id: str,
        media_type: str,
        caption: str = "",
        filename: str = "",
        sender_type: str = "bot",
    ) -> ServiceResponse:
        try:
            self.api.send_media(to, media_id, media_type, caption, filename)
            log_text = f"📎 [Archivo: {media_type}] {caption}".strip()
            self.repo.log_interaction(
                to,
                self.context.credential_id or "default",
                sender_type,
                log_text,
                "media",
            )
            return ServiceResponse.success_res(
                data={"to": to, "status": "sent"}, message="Media sent."
            )
        except Exception as e:
            logger.error(f"Media delivery error for {to}: {e}")
            return ServiceResponse.error_res(
                f"Delivery failed: {str(e)}", "DELIVERY_ERROR"
            )

    def upload_media_file(
        self, filename: str, mime_type: str, file_content: bytes
    ) -> ServiceResponse:
        try:
            media_id = self.api.upload_media(filename, mime_type, file_content)
            return ServiceResponse.success_res(
                data={"media_id": media_id}, message="Media uploaded."
            )
        except Exception as e:
            logger.error(f"Upload error for {filename}: {e}")
            return ServiceResponse.error_res(f"Upload failed: {str(e)}", "UPLOAD_ERROR")
