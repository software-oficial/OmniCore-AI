from fastapi import Request

from src.core.tenant_manager import TenantContext


async def context_middleware(request: Request, call_next):
    """
    Middleware que extrae el app_id y user_id del token y los inyecta
    en TenantContext.
    """
    app_id = request.headers.get("X-App-ID")
    user_id = request.headers.get("X-User-ID")

    tokens = TenantContext.set(app_id, user_id)

    try:
        response = await call_next(request)
        return response
    finally:
        TenantContext.reset(tokens)
