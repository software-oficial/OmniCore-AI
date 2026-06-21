import logging
from typing import Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.repositories.stock_repository import StockRepository

logger = logging.getLogger("OmniCore.InventoryManagementUseCase")


class InventoryManagementUseCase:
    """
    Application Layer: Orchestrates product and stock level management.
    Ensures business rules (like non-negative stock) are enforced before persistence.
    """

    def __init__(self, session: Session, business_id: str):
        self.repo = StockRepository(session, business_id)

    def execute_add_product(
        self,
        context: CoreContext,
        code: str,
        name: str,
        price: float,
        quantity: int,
        category: Optional[str] = None,
        is_weight: bool = False,
    ) -> ServiceResponse:
        try:
            product_id = self.repo.upsert_product(
                code, name, price, quantity, category, is_weight
            )

            # Record initial load or update in ledger
            reason = "INITIAL_LOAD" if quantity > 0 else "UPDATE"
            self.repo.record_movement(code, quantity, reason, context.user_id)

            return ServiceResponse.success_res(
                data={"product_id": product_id, "code": code},
                message=f"Product {name} processed successfully.",
            )
        except Exception as e:
            logger.error(f"Error adding product {code}: {e}")
            return ServiceResponse.error_res(
                f"Failed to process product: {str(e)}", "STOCK_ADD_ERROR"
            )

    def execute_get_product(self, code: str) -> ServiceResponse:
        try:
            product = self.repo.get_product_by_code(code)
            if not product:
                return ServiceResponse.error_res(
                    f"Product {code} not found", "PRODUCT_NOT_FOUND"
                )

            return ServiceResponse.success_res(
                data=dict(product), message="Product retrieved successfully."
            )
        except Exception as e:
            logger.error(f"Error fetching product {code}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STOCK_GET_ERROR"
            )

    def execute_update_stock(
        self, context: CoreContext, code: str, quantity: int, reason: str = "MANUAL"
    ) -> ServiceResponse:
        try:
            # Row-level lock and check current quantity
            current_qty = self.repo.get_product_quantity_for_update(code)
            if current_qty is None:
                return ServiceResponse.error_res(
                    f"Product {code} not found", "PRODUCT_NOT_FOUND"
                )

            new_qty = current_qty + quantity
            if new_qty < 0:
                return ServiceResponse.error_res(
                    "Insufficient stock to complete the operation", "STOCK_INSUFFICIENT"
                )

            self.repo.update_product_quantity(code, new_qty)
            self.repo.record_movement(code, quantity, reason, context.user_id)

            return ServiceResponse.success_res(
                data={"new_quantity": new_qty},
                message=f"Stock updated for {code}. New total: {new_qty}. Reason: {reason}.",
            )
        except Exception as e:
            logger.error(f"Error updating stock for {code}: {e}")
            return ServiceResponse.error_res(
                f"Failed to update stock: {str(e)}", "STOCK_UPDATE_ERROR"
            )

    def execute_list_products(
        self, category: Optional[str] = None, filter_text: Optional[str] = None
    ) -> ServiceResponse:
        try:
            products = self.repo.list_products(category, filter_text)
            return ServiceResponse.success_res(
                data=[dict(p) for p in products],
                message="Products listed successfully.",
            )
        except Exception as e:
            logger.error(f"Error listing products: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STOCK_LIST_ERROR"
            )

    def execute_get_history(self, code: str) -> ServiceResponse:
        try:
            history = self.repo.get_movement_history(code)
            return ServiceResponse.success_res(
                data=[dict(h) for h in history], message="Movement history retrieved."
            )
        except Exception as e:
            logger.error(f"Error fetching history for {code}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STOCK_GET_HISTORY_ERROR"
            )

    def execute_get_low_stock(self, threshold: float = 5.0) -> ServiceResponse:
        try:
            products = self.repo.get_low_stock(threshold)
            return ServiceResponse.success_res(
                data=[dict(p) for p in products],
                message="Low stock products retrieved.",
            )
        except Exception as e:
            logger.error(f"Error fetching low stock: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STOCK_LOW_STOCK_ERROR"
            )

    def execute_delete_product(self, code: str) -> ServiceResponse:
        try:
            affected = self.repo.delete_product(code)
            if affected == 0:
                return ServiceResponse.error_res(
                    f"Product {code} not found", "PRODUCT_NOT_FOUND"
                )

            return ServiceResponse.success_res(
                message=f"Product {code} deleted successfully."
            )
        except Exception as e:
            logger.error(f"Error deleting product {code}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "STOCK_DELETE_ERROR"
            )

    def execute_transfer(
        self, context: CoreContext, code: str, amount: int, from_zone: str, to_zone: str
    ) -> ServiceResponse:
        try:
            product = self.repo.get_product_by_code(code)
            if not product:
                return ServiceResponse.error_res(
                    f"Product {code} not found", "PRODUCT_NOT_FOUND"
                )

            if product["quantity"] < amount:
                return ServiceResponse.error_res(
                    "Insufficient stock for transfer", "STOCK_INSUFFICIENT"
                )

            reason = f"TRANSFER: {from_zone} -> {to_zone}"
            # According to original logic, transfer records a movement but doesn't change quantity in products table
            self.repo.record_movement(code, 0, reason, context.user_id)

            return ServiceResponse.success_res(
                message=f"Transfer of {amount} units of {code} from {from_zone} to {to_zone} recorded."
            )
        except Exception as e:
            logger.error(f"Error in stock transfer for {code}: {e}")
            return ServiceResponse.error_res(
                f"Transfer failed: {str(e)}", "STOCK_TRANSFER_ERROR"
            )
