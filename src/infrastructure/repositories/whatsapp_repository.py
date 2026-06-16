import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("OmniCore.WhatsappRepository")


class WhatsappRepository:
    """
    Infrastructure Layer: Encapsulates all SQL operations for the WhatsApp domain.
    Standardizes access to conversations, menus, settings and states.
    """

    def __init__(self, session: Session):
        self.session = session

    # --- Configuration & Settings ---
    def update_setting(self, key: str, value: str) -> None:
        self.session.execute(
            text(
                "INSERT INTO bot_settings (key, value) VALUES (:key, :value) ON CONFLICT(key) DO UPDATE SET value = :value"
            ),
            {"key": key, "value": value},
        )

    def get_all_settings(self) -> Dict[str, str]:
        result = (
            self.session.execute(text("SELECT key, value FROM bot_settings"))
            .mappings()
            .all()
        )
        return {row["key"]: row["value"] for row in result}

    def get_setting(self, key: str) -> Optional[str]:
        return self.session.execute(
            text("SELECT value FROM bot_settings WHERE key = :key"), {"key": key}
        ).scalar()

    # --- Conversation Management ---
    def get_conversation(self, phone_number: str) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(
                text(
                    "SELECT * FROM whatsapp_conversations WHERE phone_number = :phone"
                ),
                {"phone": phone_number},
            )
            .mappings()
            .first()
        )

    def create_conversation(
        self, phone_number: str, current_menu: str = "main"
    ) -> None:
        self.session.execute(
            text(
                "INSERT INTO whatsapp_conversations (phone_number, current_menu) VALUES (:phone, :menu) ON CONFLICT DO NOTHING"
            ),
            {"phone": phone_number, "menu": current_menu},
        )

    def update_conversation_menu(self, phone_number: str, menu_name: str) -> None:
        self.session.execute(
            text(
                "UPDATE whatsapp_conversations SET current_menu = :menu, last_interaction = CURRENT_TIMESTAMP WHERE phone_number = :phone"
            ),
            {"menu": menu_name, "phone": phone_number},
        )

    def set_human_mode(self, phone_number: str, status: bool) -> None:
        self.session.execute(
            text(
                "UPDATE whatsapp_conversations SET is_human_intervening = :status, last_interaction = CURRENT_TIMESTAMP WHERE phone_number = :phone"
            ),
            {"status": status, "phone": phone_number},
        )

    # --- Menu Management ---
    def get_menu_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        # Using ILIKE for flexibility as per previous implementation
        menu = (
            self.session.execute(
                text("SELECT * FROM whatsapp_menus WHERE menu_name ILIKE :name"),
                {"name": name},
            )
            .mappings()
            .first()
        )

        if not menu:
            return None

        options = (
            self.session.execute(
                text(
                    "SELECT * FROM whatsapp_menu_options WHERE menu_id = :id ORDER BY sort_order"
                ),
                {"id": menu["menu_id"]},
            )
            .mappings()
            .all()
        )

        menu_dict = dict(menu)
        menu_dict["options"] = [dict(o) for o in options]
        return menu_dict

    def list_all_menus(self) -> List[Dict[str, Any]]:
        menus = (
            self.session.execute(text("SELECT * FROM whatsapp_menus")).mappings().all()
        )
        full_menus = []
        for m in menus:
            options = (
                self.session.execute(
                    text(
                        "SELECT * FROM whatsapp_menu_options WHERE menu_id = :id ORDER BY sort_order"
                    ),
                    {"id": m["menu_id"]},
                )
                .mappings()
                .all()
            )
            m_dict = dict(m)
            m_dict["options"] = [dict(o) for o in options]
            full_menus.append(m_dict)
        return full_menus

    # --- Messaging Logs ---
    def log_interaction(
        self, phone_number: str, sender: str, content: str, message_type: str
    ) -> None:
        # Ensure contact exists
        self.session.execute(
            text(
                "INSERT INTO whatsapp_contacts (phone_number) VALUES (:phone) ON CONFLICT (phone_number) DO NOTHING"
            ),
            {"phone": phone_number},
        )
        # Ensure conversation exists
        self.session.execute(
            text(
                "INSERT INTO whatsapp_conversations (phone_number) VALUES (:phone) ON CONFLICT (phone_number) DO NOTHING"
            ),
            {"phone": phone_number},
        )
        # Log message
        self.session.execute(
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

    # --- State Persistence ---
    def save_state(self, sender: str, state_json: str) -> None:
        self.session.execute(
            text(
                """
                INSERT INTO bot_states (sender, state_data, updated_at) 
                VALUES (:sender, :data, CURRENT_TIMESTAMP)
                ON CONFLICT (sender) DO UPDATE SET state_data = excluded.state_data, updated_at = CURRENT_TIMESTAMP
            """
            ),
            {"sender": sender, "data": state_json},
        )

    def get_state(self, sender: str) -> Optional[str]:
        return self.session.execute(
            text("SELECT state_data FROM bot_states WHERE sender = :sender"),
            {"sender": sender},
        ).scalar()

    def delete_state(self, sender: str) -> None:
        self.session.execute(
            text("DELETE FROM bot_states WHERE sender = :sender"),
            {"sender": sender},
        )
