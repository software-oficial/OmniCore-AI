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
    Implementa un patrón Híbrido: Redis (Capa de Acceso Rápido) -> Tenant DB (Persistencia Final).
    """
    def __init__(self):
        from infra.cache.redis_manager import cache_manager
        self.cache = cache_manager
        self.logger = logging.getLogger("ConversationStateManager")

    def get_state(self, session: Session, context: CoreContext, sender: str) -> Dict[str, Any]:
        """
        Recupera el estado actual del usuario.
        Primero intenta Redis (L1), si falla o no existe, recupera de DB (L2) y repuebla Redis.
        """
        cache_key = f"bot_state:{context.app_id}:{sender}"
        try:
            # 1. Try Redis first
            cached_state = self.cache.get_session_context(cache_key)
            if cached_state:
                return cached_state

            # 2. Fallback to Tenant DB
            query = text("SELECT state_data FROM bot_states WHERE sender = :sender")
            res = session.execute(query, {"sender": sender}).mappings().first()
            if res and res['state_data']:
                state_data = json.loads(res['state_data'])
                # Repopulate Redis for next time (TTL 1 hour)
                self.cache.set_session_context(cache_key, state_data, ttl=3600)
                return state_data
            
            return {}
        except Exception as e:
            self.logger.error(f"Error recuperando estado para {sender}: {e}")
            return {}

    def set_state(self, session: Session, context: CoreContext, sender: str, state: Dict[str, Any]) -> ServiceResponse:
        """
        Guarda el estado del usuario.
        Actualiza Redis inmediatamente para consistencia instantánea y escribe en DB para persistencia.
        """
        try:
            # 1. Immediate Update to Redis (Ensures next GET is correct)
            cache_key = f"bot_state:{context.app_id}:{sender}"
            self.cache.set_session_context(cache_key, state, ttl=3600)

            # 2. Persistence to Tenant DB
            state_json = json.dumps(state)
            query = text('''
                INSERT INTO bot_states (sender, state_data, updated_at) 
                VALUES (:sender, :data, CURRENT_TIMESTAMP)
                ON CONFLICT (sender) DO UPDATE SET state_data = excluded.state_data, updated_at = CURRENT_TIMESTAMP
            ''')
            session.execute(query, {"sender": sender, "data": state_json})
            session.commit()
            
            return ServiceResponse.success_res(message="State updated and persisted successfully.")
        except Exception as e:
            self.logger.error(f"Error guardando estado para {sender}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STATE_SAVE_ERROR")

    @command(
        name="whatsapp.bot.state.clear",
        description="Wipes all saved state for a specific user (reset conversation).",
        params_schema={"user_id": "string"}
    )
    def clear_state(self, session: Session, context: CoreContext, sender: str) -> ServiceResponse:
        """Limpia el contexto del usuario tanto en Redis como en DB."""

        try:
            cache_key = f"bot_state:{context.app_id}:{sender}"
            if self.cache.client:
                self.cache.client.delete(cache_key)
                
            session.execute(text("DELETE FROM bot_states WHERE sender = :sender"), {"sender": sender})
            session.commit()
            return ServiceResponse.success_res(message="State cleared.")
        except Exception as e:
            self.logger.error(f"Error limpiando estado para {sender}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STATE_CLEAR_ERROR")

# Singleton
state_manager = ConversationStateManager()
 ConversationStateManager()
