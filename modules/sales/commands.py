import logging
from core.dispatcher.gateway import ai_gateway
from .sales_service import sales_service
from .mp_service import mp_service

logger = logging.getLogger("OmniCore.SalesCommands")

def register_sales_commands():
    """
    Registers sales, cash box, and payment functions into the AIGateway.
    """
    # Sales & Cash
    ai_gateway.register_command("sales.process", sales_service.process_sale)
    ai_gateway.register_command("sales.pending", sales_service.create_pending_sale)
    ai_gateway.register_command("sales.confirm", sales_service.confirm_payment)
    ai_gateway.register_command("cash.open", sales_service.open_cash_box)
    ai_gateway.register_command("cash.close", sales_service.close_cash_box)
    
    # MercadoPago
    ai_gateway.register_command("pay.mp.create", mp_service.create_payment)
    ai_gateway.register_command("pay.mp.verify", mp_service.verify_payment)
    ai_gateway.register_command("pay.mp.refund", mp_service.refund_payment)
    
    logger.info("💰 Sales and Payments module commands registered successfully.")
