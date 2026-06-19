import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("OmniCore.WhatsappRepository")


class WhatsappRepository:
    """
    Infrastructure Layer: Encapsulates all SQL operations for the WhatsApp domain.
    Aligned with Multi-Account Architecture.
    """

    def __init__(self, session: Session):
        self.session = session

    # --- Conversation Management ---
    def get_conversation(
        self, phone_number: str, credential_id: str
    ) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(
                text(
                    "SELECT * FROM chat_sessions WHERE phone = :phone AND credential_id = :cid"
                ),
                {"phone": phone_number, "cid": credential_id},
            )
            .mappings()
            .first()
        )

    def create_conversation(
        self, phone_number: str, credential_id: str, current_node: str = "main"
    ) -> None:
        # Ensure contact exists first
        self.session.execute(
            text(
                "INSERT INTO contacts (phone) VALUES (:phone) ON CONFLICT (phone) DO NOTHING"
            ),
            {"phone": phone_number},
        )

        self.session.execute(
            text(
                """
                INSERT INTO chat_sessions (session_id, phone, credential_id, current_node, status) 
                VALUES (:sid, :phone, :cid, :node, 'ACTIVE') 
                ON CONFLICT (session_id) DO NOTHING
                """
            ),
            {
                "sid": f"sess_{phone_number}_{credential_id}",
                "phone": phone_number,
                "cid": credential_id,
                "node": current_node,
            },
        )

    def update_conversation_node(
        self, phone_number: str, credential_id: str, node_name: str
    ) -> None:
        self.session.execute(
            text(
                """
                UPDATE chat_sessions 
                SET current_node = :node, updated_at = CURRENT_TIMESTAMP 
                WHERE phone = :phone AND credential_id = :cid
                """
            ),
            {"node": node_name, "phone": phone_number, "cid": credential_id},
        )

    def set_human_mode(
        self, phone_number: str, credential_id: str, status: bool
    ) -> None:
        # In blueprint, status is 'ACTIVE', 'COMPLETED', 'PENDING_HUMAN'
        status_val = "PENDING_HUMAN" if status else "ACTIVE"
        self.session.execute(
            text(
                """
                UPDATE chat_sessions 
                SET status = :status, updated_at = CURRENT_TIMESTAMP 
                WHERE phone = :phone AND credential_id = :cid
                """
            ),
            {"status": status_val, "phone": phone_number, "cid": credential_id},
        )

    # --- Bot Flow Management ---
    def get_flow_node(
        self, node_id: str, credential_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        # If credential_id is provided, look for specific flow, else look for global (NULL)
        query = "SELECT * FROM bot_flows WHERE node_id = :nid"
        params = {"nid": node_id}

        if credential_id:
            query += " AND (credential_id = :cid OR credential_id IS NULL)"
            params["cid"] = credential_id
        else:
            query += " AND credential_id IS NULL"

        res = self.session.execute(text(query), params).mappings().first()
        return dict(res) if res else None

    def list_all_nodes(self, credential_id: str) -> List[Dict[str, Any]]:
        res = (
            self.session.execute(
                text(
                    "SELECT * FROM bot_flows WHERE credential_id = :cid OR credential_id IS NULL"
                ),
                {"cid": credential_id},
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in res]

    # --- Messaging Logs ---
    def log_interaction(
        self,
        phone_number: str,
        credential_id: str,
        sender: str,
        content: str,
        message_type: str,
    ) -> None:
        # 1. Ensure contact exists
        self.session.execute(
            text(
                "INSERT INTO contacts (phone) VALUES (:phone) ON CONFLICT (phone) DO NOTHING"
            ),
            {"phone": phone_number},
        )

        # 2. Get or create session
        session_id = f"sess_{phone_number}_{credential_id}"
        self.session.execute(
            text(
                """
                INSERT INTO chat_sessions (session_id, phone, credential_id, current_node) 
                VALUES (:sid, :phone, :cid, 'main') 
                ON CONFLICT (session_id) DO NOTHING
                """
            ),
            {"sid": session_id, "phone": phone_number, "cid": credential_id},
        )

        # 3. Log message
        self.session.execute(
            text(
                """
                INSERT INTO messages (session_id, credential_id, sender, content, status) 
                VALUES (:sid, :cid, :sender, :content, 'sent')
                """
            ),
            {
                "sid": session_id,
                "cid": credential_id,
                "sender": sender,
                "content": content,
            },
        )

    # --- State Persistence ---
    def save_state(
        self, phone_number: str, credential_id: str, state_json: str
    ) -> None:
        self.session.execute(
            text(
                """
                UPDATE chat_sessions 
                SET context_data = :data, updated_at = CURRENT_TIMESTAMP 
                WHERE phone = :phone AND credential_id = :cid
                """
            ),
            {"data": state_json, "phone": phone_number, "cid": credential_id},
        )

    def get_state(self, phone_number: str, credential_id: str) -> Optional[str]:
        return self.session.execute(
            text(
                "SELECT context_data FROM chat_sessions WHERE phone = :phone AND credential_id = :cid"
            ),
            {"phone": phone_number, "cid": credential_id},
        ).scalar()

    def delete_state(self, phone_number: str, credential_id: str) -> None:
        self.session.execute(
            text(
                "UPDATE chat_sessions SET context_data = NULL WHERE phone = :phone AND credential_id = :cid"
            ),
            {"phone": phone_number, "cid": credential_id},
        )
