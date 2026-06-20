from sqlalchemy.orm import Session

from src.core.dispatcher.exceptions import InfrastructureException
from src.core.tenant_manager import TenantContext


class BaseRepository:
    """
    Base Repository for multi-tenant isolation.
    Automatically injects app_id from TenantContext.
    """

    def __init__(self, session: Session):
        self.session = session

    @property
    def app_id(self) -> str:
        ctx = TenantContext.get()
        app_id = ctx["app_id"]
        if app_id == "SYSTEM":
            raise InfrastructureException(
                "No application context found. Ensure middleware is configured.",
                "CONTEXT_MISSING",
            )
        return app_id
