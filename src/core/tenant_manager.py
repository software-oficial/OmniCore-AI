from contextvars import ContextVar
from typing import Dict, Optional


# Contexto unificado global
class TenantContext:
    app_id: ContextVar[Optional[str]] = ContextVar("app_id", default=None)
    user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

    @classmethod
    def set(cls, app_id: Optional[str], user_id: Optional[str]):
        return cls.app_id.set(app_id), cls.user_id.set(user_id)

    @classmethod
    def get(cls) -> Dict[str, str]:
        return {
            "app_id": cls.app_id.get() or "SYSTEM",
            "user_id": cls.user_id.get() or "SYSTEM",
        }

    @classmethod
    def reset(cls, tokens):
        cls.app_id.reset(tokens[0])
        cls.user_id.reset(tokens[1])
