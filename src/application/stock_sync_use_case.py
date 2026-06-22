from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.stock_repository import StockRepository


class StockSyncUseCase:
    """
    Application Layer: Handles optimized synchronization for external clients.
    """

    def __init__(self, session: Session):
        self.session = session

    def execute_get_delta(self, context: CoreContext, since: str) -> ServiceResponse:
        try:
            repo = StockRepository(self.session, context.app_id)
            result = repo.get_sync_delta(since)
            return ServiceResponse.success_res(
                data=[dict(r) for r in result],
                message=f"Sync delta retrieved. {len(result)} items updated.",
            )
        except Exception as e:
            return ServiceResponse.error_res(
                f"Sync failed: {str(e)}", "STOCK_SYNC_ERROR"
            )
