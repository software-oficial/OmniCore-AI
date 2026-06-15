import logging
import os
from typing import Dict

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.WhatsappService")


class WhatsappService:
    """
    Pure Business Logic for WhatsApp Bot Orchestration.
    All operations are stateless and use the injected session.
    """

    def _get_api_config(self) -> Dict[str, str]:
        """Internal helper to load API credentials from environment."""
        return {
            "token": os.getenv("WHATSAPP_BUSINESS_API_TOKEN", ""),
            "phone_id": os.getenv("WHATSAPP_PHONE_ID", "880275461842101"),
        }

    @command(
        name="whatsapp.update_setting",
        description="Updates a specific bot configuration setting (e.g., welcome_message, main_menu_text).",
        params_schema={"key": "string", "value": "string"},
    )
    def update_setting(
        self, session: Session, context: CoreContext, key: str, value: str
    ) -> ServiceResponse:
        """Updates a bot configuration setting in the database."""
        try:
            session.execute(
                text(
                    "INSERT INTO bot_settings (key, value) VALUES (:key, :value) ON CONFLICT(key) DO UPDATE SET value = :value"
                ),
                {"key": key, "value": value},
            )
            return ServiceResponse.success_res(
                message=f"Setting '{key}' updated successfully."
            )
        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return ServiceResponse.error_res(
                f"Update failed: {str(e)}", "SETTING_UPDATE_ERROR"
            )

    @command(
        name="whatsapp.get_settings",
        description="Retrieves all current bot configuration settings.",
        params_schema={},
    )
    def get_settings(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Retrieves all bot settings."""
        try:
            result = (
                session.execute(text("SELECT * FROM bot_settings")).mappings().all()
            )
            settings = {row["key"]: row["value"] for row in result}
            return ServiceResponse.success_res(
                data=settings, message="Bot settings retrieved."
            )
        except Exception as e:
            logger.error(f"Error fetching settings: {e}")
            return ServiceResponse.error_res(
                f"Retrieval failed: {str(e)}", "SETTING_GET_ERROR"
            )

    @command(
        name="whatsapp.send_text",
        description="Sends a plain text message to a specific phone number via WhatsApp Business API.",
        params_schema={"to": "string", "body": "string", "sender_type": "string"},
    )
    def send_text(
        self,
        session: Session,
        context: CoreContext,
        to: str,
        body: str,
        sender_type: str = "bot",
    ) -> ServiceResponse:
        try:
            cfg = self._get_api_config()
            if not cfg["token"]:
                return ServiceResponse.error_res(
                    "API Token not configured in environment", "CONFIG_MISSING"
                )

            url = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/messages"
            headers = {
                "Authorization": f"Bearer {cfg['token']}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body},
            }

            r = requests.post(url, headers=headers, json=payload)
            r.raise_for_status()

            # Log the message in the developer's business DB
            self.log_message(session, context, to, sender_type, body, "text")

            return ServiceResponse.success_res(
                data={"to": to, "status": "sent"},
                message=f"Message sent successfully to {to}.",
            )
        except Exception as e:
            logger.error(f"Error sending WhatsApp text to {to}: {e}")
            return ServiceResponse.error_res(
                f"Failed to send message: {str(e)}", "WHATSAPP_API_ERROR"
            )

    @command(
        name="whatsapp.upload_media",
        description="Uploads a file to Meta servers and returns the media_id for later use.",
        params_schema={
            "filename": "string",
            "mime_type": "string",
            "file_content": "bytes",
        },
    )
    def upload_media(
        self,
        session: Session,
        context: CoreContext,
        filename: str,
        mime_type: str,
        file_content: bytes,
    ) -> ServiceResponse:
        try:
            cfg = self._get_api_config()
            url = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/media"
            headers = {"Authorization": f"Bearer {cfg['token']}"}

            from io import BytesIO

            files = {"file": (filename, BytesIO(file_content), mime_type)}
            data = {"messaging_product": "whatsapp"}

            r = requests.post(url, headers=headers, files=files, data=data)
            r.raise_for_status()

            media_id = r.json().get("id")
            return ServiceResponse.success_res(
                data={"media_id": media_id}, message="Media uploaded successfully."
            )
        except Exception as e:
            logger.error(f"Error uploading media {filename}: {e}")
            return ServiceResponse.error_res(
                f"Media upload failed: {str(e)}", "WHATSAPP_API_ERROR"
            )

    @command(
        name="whatsapp.send_media",
        description="Sends a previously uploaded media file (image, video, document) to a user.",
        params_schema={
            "to": "string",
            "media_id": "string",
            "media_type": "string",
            "caption": "string",
            "filename": "string",
        },
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
        try:
            cfg = self._get_api_config()
            url = f"https://graph.facebook.com/v19.0/{cfg['phone_id']}/messages"
            headers = {
                "Authorization": f"Bearer {cfg['token']}",
                "Content-Type": "application/json",
            }

            if "image" in media_type:
                wapp_type = "image"
            elif "video" in media_type:
                wapp_type = "video"
            elif "audio" in media_type:
                wapp_type = "audio"
            else:
                wapp_type = "document"

            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": wapp_type,
                wapp_type: {"id": media_id},
            }
            if caption:
                payload[wapp_type]["caption"] = caption
            if wapp_type == "document" and filename:
                payload[wapp_type]["filename"] = filename

            r = requests.post(url, headers=headers, json=payload)
            r.raise_for_status()

            log_text = f"📎 [Archivo: {wapp_type}] {caption}".strip()
            self.log_message(session, context, to, sender_type, log_text, "media")

            return ServiceResponse.success_res(
                data={"to": to, "status": "sent"},
                message=f"Media ({wapp_type}) sent successfully.",
            )
        except Exception as e:
            logger.error(f"Error sending WhatsApp media to {to}: {e}")
            return ServiceResponse.error_res(
                f"Failed to send media: {str(e)}", "WHATSAPP_API_ERROR"
            )

    @command(
        name="whatsapp.log_message",
        description="Logs a message interaction in the business database for auditing and history.",
        params_schema={
            "phone_number": "string",
            "sender": "string",
            "content": "string",
            "message_type": "string",
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
            session.execute(
                text(
                    "INSERT INTO whatsapp_contacts (phone_number) VALUES (:phone) ON CONFLICT (phone_number) DO NOTHING"
                ),
                {"phone": phone_number},
            )
            session.execute(
                text(
                    "INSERT INTO whatsapp_conversations (phone_number) VALUES (:phone) ON CONFLICT (phone_number) DO NOTHING"
                ),
                {"phone": phone_number},
            )
            session.execute(
                text(
                    "INSERT INTO whatsapp_messages (phone_number, sender, message_type, content, timestamp) VALUES (:phone, :sender, :type, :content, CURRENT_TIMESTAMP)"
                ),
                {
                    "phone": phone_number,
                    "sender": sender,
                    "type": message_type,
                    "content": content,
                },
            )
            return ServiceResponse.success_res(message="Message logged successfully.")
        except Exception as e:
            logger.error(f"Error logging message for {phone_number}: {e}")
            return ServiceResponse.error_res(f"Log failure: {str(e)}", "DB_ERROR")

    @command(
        name="whatsapp.set_human_mode",
        description="Toggles the human intervention mode for a specific conversation.",
        params_schema={"phone_number": "string", "status": "boolean"},
    )
    def set_human_mode(
        self, session: Session, context: CoreContext, phone_number: str, status: bool
    ) -> ServiceResponse:
        try:
            session.execute(
                text(
                    "UPDATE whatsapp_conversations SET is_human_intervening = :status, last_interaction = CURRENT_TIMESTAMP WHERE phone_number = :phone"
                ),
                {"status": status, "phone": phone_number},
            )
            return ServiceResponse.success_res(
                message=f"Conversation mode updated to {'Human' if status else 'Bot'}."
            )
        except Exception as e:
            logger.error(f"Error updating human mode for {phone_number}: {e}")
            return ServiceResponse.error_res(f"Update failed: {str(e)}", "DB_ERROR")

    @command(
        name="whatsapp.get_status",
        description="Retrieves the current state of a WhatsApp conversation (Bot/Human mode, current menu).",
        params_schema={"phone_number": "string"},
    )
    def get_status(
        self, session: Session, context: CoreContext, phone_number: str
    ) -> ServiceResponse:
        try:
            res = (
                session.execute(
                    text(
                        "SELECT is_human_intervening, current_menu FROM whatsapp_conversations WHERE phone_number = :phone"
                    ),
                    {"phone": phone_number},
                )
                .mappings()
                .first()
            )

            if not res:
                return ServiceResponse.error_res("Conversation not found", "NOT_FOUND")

            return ServiceResponse.success_res(
                data=dict(res), message="Conversation status retrieved."
            )
        except Exception as e:
            logger.error(f"Error getting status for {phone_number}: {e}")
            return ServiceResponse.error_res(f"Retrieval failed: {str(e)}", "DB_ERROR")

    @command(
        name="whatsapp.handle_bot_flow",
        description="Processes an incoming message and determines the bot's response based on current menu state and navigation logic.",
        params_schema={"phone_number": "string", "text": "string"},
    )
    def handle_bot_flow(
        self, session: Session, context: CoreContext, phone_number: str, text: str
    ) -> ServiceResponse:
        try:
            text_clean = text.strip().lower()

            # 1. Resolve Conversation State
            conv_res = (
                session.execute(
                    text(
                        "SELECT current_menu, is_human_intervening FROM whatsapp_conversations WHERE phone_number = :phone"
                    ),
                    {"phone": phone_number},
                )
                .mappings()
                .first()
            )

            if not conv_res:
                session.execute(
                    text(
                        "INSERT INTO whatsapp_conversations (phone_number, current_menu) VALUES (:phone, 'main')"
                    ),
                    {"phone": phone_number},
                )
                conv_res = {"current_menu": "main", "is_human_intervening": False}

            if conv_res["is_human_intervening"]:
                return ServiceResponse.success_res(
                    message="Conversation is in HUMAN mode. Bot will not respond."
                )

            # 2. Global Shortcuts
            if text_clean in [
                "/start",
                "hola",
                "buenas",
                "menu",
                "opciones",
                "volver",
                "menú",
            ]:
                return self._send_main_menu(session, phone_number)

            # 3. Menu Navigation
            current_menu_name = conv_res["current_menu"]
            all_menus = (
                session.execute(text("SELECT * FROM whatsapp_menus")).mappings().all()
            )
            menu_dict = {m["menu_name"].lower(): m for m in all_menus}

            if current_menu_name and current_menu_name.lower() in menu_dict:
                active_menu = menu_dict[current_menu_name.lower()]
                options = (
                    session.execute(
                        text("SELECT * FROM whatsapp_menu_options WHERE menu_id = :id"),
                        {"id": active_menu["menu_id"]},
                    )
                    .mappings()
                    .all()
                )

                for idx, opt in enumerate(options, 1):
                    if text_clean == str(idx) or text_clean == opt["value"].lower():
                        if opt["action_type"] == "NAVIGATE":
                            session.execute(
                                text(
                                    "UPDATE whatsapp_conversations SET current_menu = :menu, last_interaction = CURRENT_TIMESTAMP WHERE phone_number = :phone"
                                ),
                                {"menu": opt["value"], "phone": phone_number},
                            )
                            return self._get_menu_response(session, opt["value"])

                        if opt["action_type"] == "HUMAN":
                            self.set_human_mode(session, context, phone_number, True)
                            return ServiceResponse.success_res(
                                message="Transferring to a human agent..."
                            )

                        if opt["action_type"] == "COMMAND":
                            return ServiceResponse.success_res(
                                data={
                                    "action": "EXECUTE_COMMAND",
                                    "command": opt["command_name"],
                                },
                                message=f"Executing action: {opt['command_name']}",
                            )

            # 4. Category Switching
            for menu in all_menus:
                if text_clean == menu["menu_name"].lower():
                    session.execute(
                        text(
                            "UPDATE whatsapp_conversations SET current_menu = :menu, last_interaction = CURRENT_TIMESTAMP WHERE phone_number = :phone"
                        ),
                        {"menu": menu["menu_name"], "phone": phone_number},
                    )
                    return self._get_menu_response(session, menu["menu_name"])

            # 5. Fallback
            fallback_msg = (
                session.execute(
                    text(
                        "SELECT value FROM bot_settings WHERE key = 'fallback_message'"
                    )
                ).scalar()
                or "No he entendido ese mensaje. Escribe 'menu' para ver las opciones."
            )

            return ServiceResponse.success_res(message=fallback_msg)

        except Exception as e:
            logger.error(f"Error in handle_bot_flow for {phone_number}: {e}")
            return ServiceResponse.error_res(
                f"Bot flow error: {str(e)}", "BOT_FLOW_ERROR"
            )

    def _send_main_menu(self, session: Session, phone_number: str) -> ServiceResponse:
        session.execute(
            text(
                "UPDATE whatsapp_conversations SET current_menu = 'main' WHERE phone_number = :phone"
            ),
            {"phone": phone_number},
        )
        return self._get_menu_response(session, "main")

    def _get_menu_response(self, session: Session, menu_name: str) -> ServiceResponse:
        menu = (
            session.execute(
                text("SELECT text FROM whatsapp_menus WHERE menu_name = :name"),
                {"name": menu_name},
            )
            .mappings()
            .first()
        )

        if not menu:
            return ServiceResponse.error_res(
                f"Menu {menu_name} not found", "MENU_NOT_FOUND"
            )

        options = (
            session.execute(
                text(
                    "SELECT label FROM whatsapp_menu_options mo JOIN whatsapp_menus wm ON mo.menu_id = wm.menu_id WHERE wm.menu_name = :name ORDER BY mo.sort_order"
                ),
                {"name": menu_name},
            )
            .mappings()
            .all()
        )

        options_list = [f"{i+1}. {opt['label']}" for i, opt in enumerate(options)]
        full_text = f"""{menu['text']}

{chr(10).join(options_list)}"""
        return ServiceResponse.success_res(message=full_text)


# Singleton
whatsapp_service = WhatsappService()
