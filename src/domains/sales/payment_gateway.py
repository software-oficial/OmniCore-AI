import logging
from typing import Any, Dict

logger = logging.getLogger("OmniCore.PaymentGateway")


class PaymentGateway:
    """
    Base Interface for Payment Gateways.
    Developers can implement their own gateways by extending this class.
    """

    def create_payment_link(
        self, amount: float, reference: str, currency: str = "USD"
    ) -> Dict[str, Any]:
        raise NotImplementedError("Gateway must implement create_payment_link")

    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Gateway must implement verify_payment")


class MercadoPagoGateway(PaymentGateway):
    """
    Example Implementation: MercadoPago.
    In production, this would use the MP SDK.
    """

    def create_payment_link(
        self, amount: float, reference: str, currency: str = "USD"
    ) -> Dict[str, Any]:
        logger.info(f"Creating MP link for {amount} {currency}, Ref: {reference}")
        # Simulate MP API Response
        return {
            "payment_id": f"mp_{uuid.uuid4().hex[:10]}",
            "link": f"https://mercadopago.com/pay/{uuid.uuid4().hex}",
            "status": "pending",
        }

    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        logger.info(f"Verifying MP payment: {payment_id}")
        # Simulate verification
        return {"status": "approved", "amount": 100.0}


import uuid

payment_gateway = MercadoPagoGateway()
