import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.domains.stock.stock_service import stock_service
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.ProcessSaleUseCase")


class ProcessSaleUseCase:
    """
    Application Layer: Orquestrates the atomic process of a sale.
    Coordinates Stock, Alias, and Sales repositories to ensure integrity.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.sales_repo = SalesRepository(session)

    def execute(
        self,
        cliente: str,
        items: List[Dict[str, Any]],
        payment_method: str,
        paga_con: float = 0.0,
        alias: Optional[str] = None,
    ) -> ServiceResponse:
        try:
            total_amount = 0.0
            processed_items = []

            # 1. Validation and Total Calculation (Inter-domain orchestration)
            for item in items:
                product_code = item["product_code"]
                qty = item["quantity"]

                # Note: In a full migration, we would use a StockRepository
                product_res = stock_service.get_product(
                    self.session, self.context, code=product_code
                )

                if not product_res.success:
                    return ServiceResponse.error_res(
                        f"Product {product_code} not found", "PRODUCT_NOT_FOUND"
                    )

                product = product_res.data
                if product["quantity"] < qty:
                    return ServiceResponse.error_res(
                        f"Insufficient stock for {product['name']}",
                        "STOCK_INSUFFICIENT",
                    )

                subtotal = float(product["price"]) * qty
                total_amount += subtotal
                processed_items.append(
                    {
                        "product_code": product_code,
                        "qty": qty,
                        "price": float(product["price"]),
                        "subtotal": subtotal,
                    }
                )

            # 2. Alias Limit Validation
            if payment_method == "Transferencia" and alias:
                alias_data = self.sales_repo.get_alias_by_name(alias)
                if not alias_data:
                    return ServiceResponse.error_res(
                        "Alias not registered.", "ALIAS_NOT_FOUND"
                    )

                if (float(alias_data["acumulado"] or 0)) + total_amount > float(
                    alias_data["limite"]
                ):
                    return ServiceResponse.error_res(
                        f"Limit exceeded for alias {alias}.", "ALIAS_LIMIT_EXCEEDED"
                    )

            # 3. Cash Payment Validation
            vuelto = 0.0
            if payment_method == "Efectivo":
                if paga_con < total_amount:
                    return ServiceResponse.error_res(
                        "Insufficient cash amount.", "CASH_INSUFFICIENT"
                    )
                vuelto = paga_con - total_amount

            # 4. Atomic Persistence via Repository
            sale_id = self.sales_repo.create_sale(
                client_name=cliente,
                total=total_amount,
                method=payment_method,
                paga_con=paga_con,
                vuelto=vuelto,
            )

            for pi in processed_items:
                self.sales_repo.add_sale_item(
                    sale_id=sale_id,
                    product_code=pi["product_code"],
                    quantity=pi["qty"],
                    price=pi["price"],
                    subtotal=pi["subtotal"],
                )

            # 5. Update Cash Box
            is_digital = payment_method != "Efectivo"
            self.sales_repo.update_cash_box_totals(
                amount=total_amount, is_digital=is_digital
            )

            # 6. Update Alias Accumulator
            if payment_method == "Transferencia" and alias:
                self.sales_repo.update_alias_accumulation(
                    nombre=alias, amount=total_amount
                )

            # 7. Deduct Stock
            for pi in processed_items:
                stock_service.update_stock(
                    self.session,
                    self.context,
                    code=pi["product_code"],
                    quantity=-pi["qty"],
                    reason=f"SALE_{sale_id}",
                )

            return ServiceResponse.success_res(
                data={"sale_id": sale_id, "total": total_amount, "vuelto": vuelto},
                message="Sale processed and stock deducted successfully.",
            )
        except Exception as e:
            logger.error(f"ProcessSaleUseCase critical failure: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SALES_PROCESS_ERROR"
            )
