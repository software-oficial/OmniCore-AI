import logging

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.CashBoxUseCase")


class CashBoxUseCase:
    """
    Application Layer: Manages the physical and digital cash box state.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SalesRepository(session, context.business_id)

    def open_box(self, monto_inicial: float) -> ServiceResponse:
        try:
            count = self.repo.open_cash_box(monto_inicial)
            if count == 0:
                return ServiceResponse.error_res(
                    "Cash box not found", "CASH_BOX_NOT_FOUND"
                )
            return ServiceResponse.success_res(
                message=f"Cash box opened successfully with ${monto_inicial}."
            )
        except Exception as e:
            logger.error(f"Error opening cash box: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "CASH_BOX_ERROR"
            )

    def close_box(self, monto_real: float) -> ServiceResponse:
        try:
            state = self.repo.get_cash_box()
            if not state or not state["abierta"]:
                return ServiceResponse.error_res(
                    "Cash box is closed or not found", "CASH_BOX_CLOSED"
                )

            self.repo.close_cash_box(monto_real)

            expected = float(state["efectivo_inicial"]) + float(
                state["ventas_efectivo"]
            )
            resumen = {
                "expected": expected,
                "actual": monto_real,
                "difference": monto_real - expected,
            }
            return ServiceResponse.success_res(
                data=resumen, message="Cash box closed and balanced."
            )
        except Exception as e:
            logger.error(f"Error closing cash box: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "CASH_BOX_ERROR"
            )

    def get_status(self) -> ServiceResponse:
        try:
            status = self.repo.get_cash_box()
            return ServiceResponse.success_res(
                data=dict(status) if status else None,
                message="Cash box status retrieved.",
            )
        except Exception as e:
            logger.error(f"Error getting cash box status: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "CASH_BOX_ERROR"
            )
