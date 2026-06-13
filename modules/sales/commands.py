import logging
from core.dispatcher.gateway import ai_gateway
from .sales_service import sales_service
from .mp_service import mp_service

logger = logging.getLogger("OmniCore.SalesCommands")

def register_sales_commands():
    """
    Registers sales, cash box, and payment functions into the AIGateway.
    Exposes business logic with full semantic metadata for AI and Developer discovery.
    """
    # Sales & Cash
    ai_gateway.register_command(
        "sales.process", sales_service.process_sale, 
        description="Initializes a new sale process, validating stock and calculating totals.",
        params_schema={"items": "list[dict {product_code: string, quantity: int}]", "customer_id": "string", "payment_method": "string"}
    )
    ai_gateway.register_command(
        "sales.pending", sales_service.create_pending_sale, 
        description="Creates a pending sale (draft) to be confirmed later.",
        params_schema={"items": "list[dict {product_code: string, quantity: int}]", "customer_id": "string"}
    )
    ai_gateway.register_command(
        "sales.confirm", sales_service.confirm_payment, 
        description="Confirms a sale as paid and finalizes the transaction in the DB.",
        params_schema={"sale_id": "string", "transaction_id": "string"}
    )
    ai_gateway.register_command(
        "sales.cash.open", sales_service.open_cash_box, 
        description="Opens the daily cash box with an initial balance.",
        params_schema={"amount": "float", "user_id": "string"}
    )
    ai_gateway.register_command(
        "sales.cash.close", sales_service.close_cash_box, 
        description="Closes the cash box and calculates the final balance vs expected.",
        params_schema={"user_id": "string", "actual_amount": "float"}
    )
    
    # MercadoPago
    ai_gateway.register_command(
        "sales.pay.mp.create", mp_service.create_payment, 
        description="Generates a Mercado Pago payment link for a specific amount.",
        params_schema={"amount": "float", "external_reference": "string", "description": "string"}
    )
    ai_gateway.register_command(
        "sales.pay.mp.verify", mp_service.verify_payment, 
        description="Verifies the status of a Mercado Pago transaction via payment_id.",
        params_schema={"payment_id": "string"}
    )
    ai_gateway.register_command(
        "sales.pay.mp.refund", mp_service.refund_payment, 
        description="Processes a refund for a specific Mercado Pago transaction.",
        params_schema={"payment_id": "string", "reason": "string"}
    )

    
    logger.info("💰 Sales and Payments module commands registered successfully with full metadata.")
