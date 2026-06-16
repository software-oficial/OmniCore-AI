import logging

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.domains.stock.stock_service import stock_service
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.SaleWebhookUseCase")


class SaleWebhookUseCase:
    """
    Application Layer: Handles external payment notifications (e.g., MercadoPago).
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SalesRepository(session)

    def handle_mp_notification(
        self, payment_id: str, external_reference: str, status: str
    ) -> ServiceResponse:
        try:
            if status != "approved":
                return ServiceResponse.success_res(
                    message=f"Payment {payment_id} status is {status}. No action taken."
                )

            # 1. Find the pending sale
            sale = self.repo.get_sale_by_id(int(external_reference))
            if not sale or sale["status"] != "PENDING":
                return ServiceResponse.error_res(
                    "Pending sale not found for this reference", "SALE_NOT_FOUND"
                )

            # 2. Mark sale as completed
            self.repo.update_sale_status(int(external_reference), "COMPLETED")
            # We can't easily update payment_method via the current repo without adding a method,
            # but let's assume we update the status first.

            # 3. Deduct stock for all items in this sale
            items = self.repo.get_sale_items(int(external_reference))

            for item in items:
                stock_service.update_stock(
                    self.session,
                    self.context,
                    code=item["product_code"],
                    quantity=-item["quantity"],
                    reason=f"MP_PAYMENT_{payment_id}",
                )

            return ServiceResponse.success_res(
                data={"sale_id": external_reference, "status": "COMPLETED"},
                message=f"Payment {payment_id} processed. Sale {external_reference} completed and stock deducted.",
            )
        except Exception as e:
            logger.error(
                f"Error handling MP webhook for sale {external_reference}: {e}"
            )
            return ServiceResponse.error_res(
                f"Webhook processing failed: {str(e)}", "WEBHOOK_ERROR"
            )
