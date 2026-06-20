from sqlalchemy.orm import Session

from src.core.dispatcher.context_middleware import current_app_id
from src.core.dispatcher.exceptions import InfrastructureException


class BaseRepository:
    """
    Base Repository for multi-tenant isolation.
    Automatically injects app_id into queries.
    """

    def __init__(self, session: Session):
        self.session = session

    @property
    def app_id(self) -> str:
        app_id = current_app_id.get()
        if not app_id:
            raise InfrastructureException(
                "No application context found. Ensure middleware is configured.",
                "CONTEXT_MISSING",
            )
        return app_id
