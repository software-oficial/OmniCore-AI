import requests
import logging
from typing import Dict, Any, Optional
from src.core.dispatcher.core_types import ServiceResponse, CoreContext
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.MercadoPagoService")

class MercadoPagoService:
    """
    Integration with MercadoPago API.
    Stateless service: Tokens and configurations are passed per request.
    """
    def __init__(self):
        self.logger = logging.getLogger("MercadoPagoService")

    def create_payment(self, context: CoreContext, amount: float, description: str, external_reference: str, access_token: str, **kwargs) -> ServiceResponse:
        """
        Creates a payment preference in MercadoPago.
        """
        url = "https://api.mercadopago.com/checkout/preferences"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {
            "items": [{"title": description, "quantity": kwargs.get("quantity", 1), "unit_price": amount, "currency_id": "ARS"}],
            "external_reference": external_reference,
            "auto_return": "approved"
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return ServiceResponse.success_res(
                data={"init_point": data.get("init_point"), "preference_id": data.get("id")},
                message="Payment preference created successfully."
            )
        except Exception as e:
            return ServiceResponse.error_res(str(e), "MP_API_ERROR")

    @command(
        name="sales.pay.mp.verify",
        description="Verifies the status of a Mercado Pago transaction via payment_id.",
        params_schema={"payment_id": "string"}
    )
    def verify_payment(self, context: CoreContext, payment_id: str, access_token: str, **kwargs) -> ServiceResponse:
        """
        Verifies the status of a payment via MP API.
        """
        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return ServiceResponse.success_res(
                data={"state": data.get("state"), "external_reference": data.get("external_reference")},
                message="Payment status verified."
            )
        except Exception as e:
            return ServiceResponse.error_res(str(e), "MP_API_ERROR")

    def refund_payment(self, context: CoreContext, payment_id: str, access_token: str, **kwargs) -> ServiceResponse:
        """
        Processes a refund in MercadoPago.
        """
        # Implementation of MP refund logic would go here
        return ServiceResponse.error_res("Refund function not yet implemented for MercadoPago.", "NOT_IMPLEMENTED")

# Singleton
mp_service = MercadoPagoService()
