import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.dispatcher.core_types import CoreContext, ServiceResponse

logger = logging.getLogger("OmniCore.WhatsappService")

class WhatsappService:
    """
    Pure Business Logic for WhatsApp Bot Orchestration.
    """

    def get_or_create_conversation(self, session: Session, phone: str) -> Dict[str, Any]:
        res = session.execute(text("SELECT * FROM whatsapp_conversations WHERE phone_number = :phone"), {"phone": phone}).mappings().first()
        if res:
            return dict(res)
        query = text("INSERT INTO whatsapp_conversations (phone_number) VALUES (:phone) RETURNING *")
        result = session.execute(query, {"phone": phone}).mappings().first()
        session.commit()
        return dict(result)

    @command(
        name="whatsapp.service.process_message",
        description="Low-level gateway to process raw incoming WhatsApp messages.",
        params_schema={"payload": "dict"}
    )
    def process_incoming_message(self, session: Session, context: CoreContext, phone: str, text: str) -> ServiceResponse:
        try:
            conv = self.get_or_create_conversation(session, phone)
            if conv['is_human_intervening']:
                return ServiceResponse.success_res(message="Human mode active. Message forwarded to agent.")
            current_menu = conv['current_menu']
            option_query = text("""
                SELECT mo.value, mo.action_type, mo.command_name 
                FROM whatsapp_menu_options mo
                JOIN whatsapp_menus wm ON mo.menu_id = wm.menu_id
                WHERE wm.menu_name = :menu AND (mo.label ILIKE :text OR mo.value ILIKE :text)
            """)
            option = session.execute(option_query, {"menu": current_menu, "text": f"%{text}%"}).mappings().first()
            if not option:
                return self._handle_unknown_input(session, phone, current_menu)
            if option['action_type'] == 'NAVIGATE':
                session.execute(text("UPDATE whatsapp_conversations SET current_menu = :menu, last_interaction = CURRENT_TIMESTAMP WHERE phone_number = :phone"), 
                                {"menu": option['value'], "phone": phone})
                session.commit()
                return self._get_menu_response(session, option['value'])
            if option['action_type'] == 'COMMAND':
                return ServiceResponse.success_res(
                    data={"action": "EXECUTE_COMMAND", "command": option['command_name']},
                    message=f"Executing action: {option['command_name']}"
                )
            if option['action_type'] == 'HUMAN':
                session.execute(text("UPDATE whatsapp_conversations SET is_human_intervening = TRUE WHERE phone_number = :phone"), {"phone": phone})
                session.commit()
                return ServiceResponse.success_res(message="Transferring to a human agent...")
            return ServiceResponse.error_res("Action not implemented", "ACTION_NOT_SUPPORTED")
        except Exception as e:
            logger.error(f"Error processing message from {phone}: {e}")
            return ServiceResponse.error_res(f"Bot error: {str(e)}", "BOT_INTERNAL_ERROR")

    def _get_menu_response(self, session: Session, menu_name: str) -> ServiceResponse:
        menu = session.execute(text("SELECT text FROM whatsapp_menus WHERE menu_name = :name"), {"name": menu_name}).mappings().first()
        if not menu:
            return ServiceResponse.error_res(f"Menu {menu_name} not found", "MENU_NOT_FOUND")
        options = session.execute(text("""
            SELECT mo.label 
            FROM whatsapp_menu_options mo 
            JOIN whatsapp_menus wm ON mo.menu_id = wm.menu_id 
            WHERE wm.menu_name = :name ORDER BY mo.sort_order
        """), {"name": menu_name}).mappings().all()
        options_list = [f"{i+1}. {opt['label']}" for i, opt in enumerate(options)]
        options_text = " | ".join(options_list)
        full_text = f"{menu['text']} Options: {options_text}"
        return ServiceResponse.success_res(message=full_text)

    def _handle_unknown_input(self, session: Session, phone: str, current_menu: str) -> ServiceResponse:
        menu = session.execute(text("SELECT text FROM whatsapp_menus WHERE menu_name = :name"), {"name": current_menu}).mappings().first()
        msg = menu['text'] if menu else "I didn't understand that. Please choose a valid option."
        return ServiceResponse.success_res(message=f"Sorry, I didn't get that. {msg}")

# Singleton
whatsapp_service = WhatsappService()
