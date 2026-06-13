import logging
from core.dispatcher.gateway import ai_gateway
from .stock_service import stock_service
from .import_service import import_service

logger = logging.getLogger("OmniCore.StockCommands")

def register_stock_commands():
    """
    Registers stock module functions into the AIGateway.
    This exposes the pure logic to the AI-Ready API with full semantic metadata.
    """
    # Basic Stock Operations
    ai_gateway.register_command(
        "stock.add", stock_service.add_product, 
        description="Adds a new product or updates an existing one in the inventory.",
        params_schema={"product_code": "string", "name": "string", "price": "float", "quantity": "int", "category": "string"}
    )
    ai_gateway.register_command(
        "stock.get", stock_service.get_product, 
        description="Retrieves detailed information for a specific product.",
        params_schema={"product_code": "string"}
    )
    ai_gateway.register_command(
        "stock.update", stock_service.update_stock, 
        description="Updates the quantity of an existing product (absolute value).",
        params_schema={"product_code": "string", "quantity": "int"}
    )
    ai_gateway.register_command(
        "stock.list", stock_service.list_products, 
        description="Returns a list of all products in the inventory.",
        params_schema={}
    )
    ai_gateway.register_command(
        "stock.history", stock_service.get_stock_history, 
        description="Retrieves the movement history of a specific product.",
        params_schema={"product_code": "string"}
    )
    ai_gateway.register_command(
        "stock.low", stock_service.get_low_stock, 
        description="Lists products that have fallen below their minimum stock threshold.",
        params_schema={"threshold": "int"}
    )
    
    # Import Operations
    ai_gateway.register_command(
        "stock.import.preview", import_service.preview_import, 
        description="Previews the results of a CSV/JSON import before committing to DB.",
        params_schema={"data": "list[dict]"}
    )
    ai_gateway.register_command(
        "stock.import.commit", import_service.commit_import, 
        description="Commits a previously previewed import to the inventory.",
        params_schema={"import_id": "string"}
    )
    
    logger.info("📦 Stock module commands registered successfully with full metadata.")
