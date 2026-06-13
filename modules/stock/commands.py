import logging
from core.dispatcher.gateway import ai_gateway
from .stock_service import stock_service
from .import_service import import_service

logger = logging.getLogger("OmniCore.StockCommands")

def register_stock_commands():
    """
    Registers stock module functions into the AIGateway.
    This exposes the pure logic to the AI-Ready API.
    """
    # Basic Stock Operations
    ai_gateway.register_command("stock.add", stock_service.add_product)
    ai_gateway.register_command("stock.get", stock_service.get_product)
    ai_gateway.register_command("stock.update", stock_service.update_stock)
    ai_gateway.register_command("stock.list", stock_service.list_products)
    ai_gateway.register_command("stock.history", stock_service.get_stock_history)
    ai_gateway.register_command("stock.low", stock_service.get_low_stock)
    
    # Import Operations
    ai_gateway.register_command("stock.import.preview", import_service.preview_import)
    ai_gateway.register_command("stock.import.commit", import_service.commit_import)
    
    logger.info("📦 Stock module commands registered successfully.")
