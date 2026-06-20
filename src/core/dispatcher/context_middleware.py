from contextvars import ContextVar
from typing import Optional

from fastapi import Request

# ContextVar para almacenar el contexto de forma segura por cada solicitud (request)
# Esto evita la necesidad de pasar el contexto manualmente por todas las funciones.
current_app_id: ContextVar[Optional[str]] = ContextVar("current_app_id", default=None)
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


async def context_middleware(request: Request, call_next):
    """
    Middleware que extrae el app_id y user_id del token y los inyecta
    en las ContextVars para que estén disponibles en todo el flujo.
    """
    # Aquí asumimos que el token ya fue validado y los headers están presentes
    # O podemos llamar al servicio de auth aquí si es necesario
    app_id = request.headers.get("X-App-ID")
    user_id = request.headers.get("X-User-ID")

    token_app_id = current_app_id.set(app_id)
    token_user_id = current_user_id.set(user_id)

    try:
        response = await call_next(request)
        return response
    finally:
        current_app_id.reset(token_app_id)
        current_user_id.reset(token_user_id)
