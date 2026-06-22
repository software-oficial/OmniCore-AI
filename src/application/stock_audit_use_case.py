import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.stock_repository import StockRepository

logger = logging.getLogger("OmniCore.StockAuditUseCase")


class StockAuditUseCase:
    """
    Application Layer: Handles physical inventory audits and adjusts discrepancies.
    """

    def __init__(self, session: Session):
        self.session = session

    def execute_audit(
        self, context: CoreContext, audit_data: List[Dict[str, Any]]
    ) -> ServiceResponse:
        try:
            repo = StockRepository(self.session, context.app_id)
            results = []
            discrepancies = 0

            for entry in audit_data:
                code = entry.get("code")
                physical_qty = entry.get("physical_count")

                if not code or physical_qty is None:
                    continue

                # Lock product and get current quantity
                recorded_qty = repo.get_product_quantity_for_update(code)

                if recorded_qty is None:
                    results.append(
                        {
                            "code": code,
                            "status": "NOT_FOUND",
                            "message": "Product not found in database",
                        }
                    )
                    continue

                diff = physical_qty - recorded_qty

                if diff != 0:
                    discrepancies += 1
                    repo.update_product_quantity(code, physical_qty)
                    repo.record_movement(
                        code, diff, "AUDIT_DISCREPANCY", context.user_id
                    )
                    results.append(
                        {
                            "code": code,
                            "status": "ADJUSTED",
                            "diff": diff,
                            "new_qty": physical_qty,
                        }
                    )
                else:
                    results.append(
                        {"code": code, "status": "MATCHED", "qty": recorded_qty}
                    )

            return ServiceResponse.success_res(
                data={"results": results, "total_discrepancies": discrepancies},
                message=f"Audit completed. {discrepancies} discrepancies adjusted.",
            )
        except Exception as e:
            logger.error(f"Error during stock audit: {e}")
            return ServiceResponse.error_res(
                f"Audit failure: {str(e)}", "STOCK_AUDIT_ERROR"
            )
