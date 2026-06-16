import logging

import requests

from src.core.dispatcher.core_types import CoreContext, ServiceResponse

logger = logging.getLogger("OmniCore.MPService")


class MercadoPagoService:
    """
    Pure Business Logic for Mercado Pago Integration.
    Handles payment preference creation and API communication.
    Stateless: All credentials are retrieved from the client's own database via CoreContext.
    """

    def __init__(self):
        self.base_url = "https://api.mercadopago.com"

    def create_payment(
        self,
        context: CoreContext,
        amount: float,
        description: str,
        external_reference: str,
        access_token: str,
    ) -> ServiceResponse:
        """
        Creates a payment preference in Mercado Pago.
        The access_token is provided by the caller (retrieved from client's settings).
        """
        try:
            url = f"{self.base_url}/preferences"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "items": [
                    {
                        "title": description,
                        "quantity": 1,
                        "unit_price": amount,
                        "currency_id": "ARS",  # Default to ARS, could be a setting in CoreContext
                    }
                ],
                "external_reference": external_reference,
                "notification_url": "https://your-api-gateway.com/api/sales/handle_mp_webhook",  # Should be a setting
                "back_urls": {
                    "success": "https://your-app.com/payment/success",
                    "failure": "https://your-app.com/payment/failure",
                    "pending": "https://your-app.com/payment/pending",
                },
                "auto_return": "approved",
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            return ServiceResponse.success_res(
                data={
                    "init_point": data.get("init_point"),
                    "preference_id": data.get("id"),
                },
                message="Mercado Pago preference created successfully.",
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"MP API Error: {e.response.text}")
            return ServiceResponse.error_res(
                f"Mercado Pago API Error: {e.response.status_code}", "MP_API_ERROR"
            )
        except Exception as e:
            logger.error(f"Critical error creating MP payment: {e}")
            return ServiceResponse.error_res(
                f"Internal payment error: {str(e)}", "MP_INTERNAL_ERROR"
            )


# Singleton for the dispatcher
mp_service = MercadoPagoService()
