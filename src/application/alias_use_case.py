import logging

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.AliasUseCase")


class AliasUseCase:
    """
    Application Layer: Manages customer alias and credit limits.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SalesRepository(session)

    def add_alias(self, nombre: str, limite: float) -> ServiceResponse:
        try:
            import uuid

            alias_id = str(uuid.uuid4())[:8]
            self.repo.add_alias(alias_id, nombre, limite)
            return ServiceResponse.success_res(
                message=f"Alias {nombre} created successfully."
            )
        except Exception as e:
            logger.error(f"Error adding alias: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "ALIAS_ADD_ERROR"
            )

    def list_aliases(self) -> ServiceResponse:
        try:
            aliases = self.repo.list_all_aliases()
            return ServiceResponse.success_res(
                data=[dict(a) for a in aliases], message="Aliases listed successfully."
            )
        except Exception as e:
            logger.error(f"Error listing aliases: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "ALIAS_LIST_ERROR"
            )

    def delete_alias(self, alias_id: str) -> ServiceResponse:
        try:
            self.repo.delete_alias(alias_id)
            return ServiceResponse.success_res(
                message=f"Alias {alias_id} deleted successfully."
            )
        except Exception as e:
            logger.error(f"Error deleting alias: {e}")
            return ServiceResponse.error_res(
                f"Internal la error: {str(e)}", "ALIAS_DELETE_ERROR"
            )
