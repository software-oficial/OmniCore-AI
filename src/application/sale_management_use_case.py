import logging
from typing import cast

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.domains.stock.stock_service import stock_service
from src.infrastructure.repositories.sales_repository import SalesRepository

logger = logging.getLogger("OmniCore.SaleManagementUseCase")


class SaleManagementUseCase:
    """
    Application Layer: Manages sale life cycle (cancellation, payment link generation).
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SalesRepository(session, context.business_id)

    def cancel_sale(self, sale_id: int) -> ServiceResponse:
        try:
            sale = self.repo.get_sale_by_id(sale_id)
            if not sale or sale["status"] == "COMPLETED":
                return ServiceResponse.error_res(
                    "Sale cannot be cancelled.", "SALE_INVALID"
                )

            self.repo.update_sale_status(sale_id, "CANCELLED")
            return ServiceResponse.success_res(message="Sale cancelled successfully.")
        except Exception as e:
            logger.error(f"Error cancelling sale {sale_id}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SALE_CANCEL_ERROR"
            )

    def create_payment_link(
        self, codigo: str, cantidad: int, cliente: str
    ) -> ServiceResponse:
        try:
            # 1. Validate product and calculate total
            product_res = stock_service.get_product(
                self.session, self.context, code=codigo
            )
            if not product_res.success:
                return product_res

            total = float(product_res.data["price"]) * cantidad

            # 2. Create pending sale in DB
            sale_id = self.repo.create_sale(
                client_name=cliente,
                total=total,
                method="MercadoPago",
                paga_con=0.0,
                vuelto=0.0,
                status="PENDING",
            )

            # 3. Add item to sale
            self.repo.add_sale_item(
                sale_id=sale_id,
                product_code=codigo,
                quantity=cantidad,
                price=product_res.data["price"],
                subtotal=total,
            )

            # 4. Generate MP Link
            from src.core.system_service import system_service

            token_res = system_service.get_setting(
                self.session, self.context, key="mp_access_token"
            )
            if not token_res.success:
                return token_res

            mp_token = token_res.data.get("value")
            if not mp_token:
                return ServiceResponse.error_res(
                    "MP Token not configured in system settings.", "CONFIG_MISSING"
                )

            from src.infrastructure.gateways.payment_gateway_adapter import (
                PaymentGatewayAdapter,
            )

            gateway = PaymentGatewayAdapter()
            try:
                mp_data = gateway.create_payment_preference(
                    access_token=mp_token,
                    amount=total,
                    description=f"Pago de producto {cast(dict, product_res.data)['name']}",
                    external_reference=str(sale_id),
                )
                return ServiceResponse.success_res(
                    data={"payment_url": mp_data["init_point"], "sale_id": sale_id},
                    message="Payment link generated successfully.",
                )
            except Exception as e:
                logger.error(f"Payment gateway error: {e}")
                return ServiceResponse.error_res(
                    f"Gateway failure: {str(e)}", "GATEWAY_ERROR"
                )
        except Exception as e:
            logger.error(f"Error creating payment link: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "MP_LINK_ERROR"
            )
