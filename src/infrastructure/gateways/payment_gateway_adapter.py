import logging
from typing import Any, Dict

import requests

logger = logging.getLogger("OmniCore.PaymentGatewayAdapter")


class PaymentGatewayAdapter:
    """
    Infrastructure Layer: Acts as the bridge between the Application layer and external Payment Providers.
    Implements a standardized interface for different payment gateways (MP, Stripe, PayPal, etc.).
    """

    def __init__(self):
        self.base_url = "https://api.mercadopago.com"

    def create_payment_preference(
        self,
        access_token: str,
        amount: float,
        description: str,
        external_reference: str,
        currency: str = "ARS",
    ) -> Dict[str, Any]:
        """
        Creates a payment preference in MercadoPago.
        Returns the init_point and preference_id.
        """
        url = f"{self.base_url}/checkout/preferences"
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
                    "currency_id": currency,
                }
            ],
            "external_reference": external_reference,
            "auto_return": "approved",
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return {
            "init_point": data.get("init_point"),
            "preference_id": data.get("id"),
        }

    def verify_payment_status(
        self, access_token: str, payment_id: str
    ) -> Dict[str, Any]:
        """
        Verifies the status of a payment via MP API.
        """
        url = f"{self.base_url}/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        return {
            "state": data.get("state"),
            "external_reference": data.get("external_reference"),
        }

    def process_refund(self, access_token: str, payment_id: str) -> Dict[str, Any]:
        """
        Processes a refund in MercadoPago.
        """
        # Placeholder for actual refund API call
        raise NotImplementedError("Refund logic not yet implemented in adapter.")
