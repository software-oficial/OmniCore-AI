import logging
import json
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse

logger = logging.getLogger("OmniCore.ConversationStateManager")

class ConversationStateManager:
    """
    Gestiona el estado efímero de las conversaciones de los usuarios.
    Persiste el estado en la tabla 'bot_states' del esquema del tenant.
    """
    def __init__(self):
        self.logger = logging.getLogger("ConversationStateManager")

    def get_state(self, session: Session, context: CoreContext, sender: str) -> Dict[str, Any]:
        """
        Recupera el estado actual del usuario desde la DB del tenant.
        """
        try:
            query = text("SELECT state_data FROM bot_states WHERE sender = :sender")
            res = session.execute(query, {"sender": sender}).mappings().first()
            if res and res['state_data']:
                return json.loads(res['state_data'])
            return {}
        except Exception as e:
            self.logger.error(f"Error recuperando estado para {sender}: {e}")
            return {}

    def set_state(self, session: Session, context: CoreContext, sender: str, state: Dict[str, Any]) -> ServiceResponse:
        """
        Guarda o actualiza el estado del usuario en la DB del tenant.
        """
        try:
            state_json = json.dumps(state)
            query = text('''
                INSERT INTO bot_states (sender, state_data, updated_at) 
                VALUES (:sender, :data, CURRENT_TIMESTAMP)
                ON CONFLICT (sender) DO UPDATE SET state_data = excluded.state_data, updated_at = CURRENT_TIMESTAMP
            ''')
            session.execute(query, {"sender": sender, "data": state_json})
            session.commit()
            return ServiceResponse.success_res(message="State updated successfully.")
        except Exception as e:
            self.logger.error(f"Error guardando estado para {sender}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STATE_SAVE_ERROR")

    def clear_state(self, session: Session, context: CoreContext, sender: str) -> ServiceResponse:
        """Limpia el contexto del usuario (Reset de flujo)."""
        try:
            session.execute(text("DELETE FROM bot_states WHERE sender = :sender"), {"sender": sender})
            session.commit()
            return ServiceResponse.success_res(message="State cleared.")
        except Exception as e:
            self.logger.error(f"Error limpiando estado para {sender}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STATE_CLEAR_ERROR")

# Singleton
state_manager = ConversationStateManager()
