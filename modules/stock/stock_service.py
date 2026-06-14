import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse
from core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.StockService")

class StockService:
    """
    Pure Business Logic for Stock Management.
    Agnostic to the database source; relies on the injected session.
    """

    @command(
        name="stock.add", 
        description="Adds a new product and records the initial movement in the ledger.",
        params_schema={"code": "string", "name": "string", "price": "float", "quantity": "int", "category": "string", "is_weight": "boolean"}
    )
    def add_product(self, session: Session, context: CoreContext, code: str, name: str, price: float, quantity: int, category: Optional[str] = None, is_weight: bool = False) -> ServiceResponse:
        """Adds a new product and records the initial movement in the ledger."""
        try:
            # Upsert product
            query = text("""
                INSERT INTO products (code, name, price, quantity, category, is_weight) 
                VALUES (:code, :name, :price, :quantity, :category, :is_weight) 
                ON CONFLICT(code) DO UPDATE SET 
                    name=excluded.name, price=excluded.price, quantity=excluded.quantity, 
                    category=excluded.category, is_weight=excluded.is_weight, updated_at=CURRENT_TIMESTAMP
                RETURNING id
            """)
            result = session.execute(query, {
                "code": code, "name": name, "price": price, 
                "quantity": quantity, "category": category, "is_weight": is_weight
            })
            product_id = result.scalar()
            
            # Record ledger movement
            movement_query = text("""
                INSERT INTO stock_movements (product_code, amount, reason, user_id) 
                VALUES (:code, :amount, :reason, :user_id)
            """)
            session.execute(movement_query, {
                "code": code, "amount": quantity, "reason": "INITIAL_LOAD" if quantity > 0 else "UPDATE", "user_id": context.user_id
            })
            
            session.commit()
            return ServiceResponse.success_res(
                data={"product_id": product_id, "code": code},
                message=f"Product {name} processed successfully."
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding product {code}: {e}")
            return ServiceResponse.error_res(f"Failed to process product: {str(e)}", "STOCK_ADD_ERROR")

    @command(
        name="stock.get", 
        description="Retrieves a single product by its unique code.",
        params_schema={"code": "string"}
    )
    def get_product(self, session: Session, context: CoreContext, code: str) -> ServiceResponse:
        """Retrieves a single product by its unique code."""
        try:
            query = text("SELECT * FROM products WHERE code = :code")
            result = session.execute(query, {"code": code}).mappings().first()
            
            if not result:
                return ServiceResponse.error_res(f"Product {code} not found", "PRODUCT_NOT_FOUND")
            
            return ServiceResponse.success_res(data=dict(result), message="Product retrieved successfully.")
        except Exception as e:
            logger.error(f"Error fetching product {code}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_GET_ERROR")

    @command(
        name="stock.update", 
        description="Updates the quantity of a product using atomic transactions. Prevents negative stock.",
        params_schema={"code": "string", "quantity": "int", "reason": "string"}
    )
    def update_stock(self, session: Session, context: CoreContext, code: str, quantity: int, reason: str = "MANUAL") -> ServiceResponse:
        """
        Updates the quantity of a product using atomic transactions.
        Prevents negative stock.
        """
        try:
            # 1. Lock row and check current quantity
            lock_query = text("SELECT quantity FROM products WHERE code = :code FOR UPDATE")
            current_qty = session.execute(lock_query, {"code": code}).scalar()
            
            if current_qty is None:
                return ServiceResponse.error_res(f"Product {code} not found", "PRODUCT_NOT_FOUND")
            
            new_qty = current_qty + quantity
            if new_qty < 0:
                return ServiceResponse.error_res("Insufficient stock to complete the operation", "STOCK_INSUFFICIENT")
            
            # 2. Update product
            update_query = text("""
                UPDATE products 
                SET quantity = :new_qty, updated_at = CURRENT_TIMESTAMP 
                WHERE code = :code
            """)
            session.execute(update_query, {"new_qty": new_qty, "code": code})
            
            # 3. Record movement in ledger
            movement_query = text("""
                INSERT INTO stock_movements (product_code, amount, reason, user_id) 
                VALUES (:code, :amount, :reason, :user_id)
            """)
            session.execute(movement_query, {"code": code, "amount": quantity, "reason": reason, "user_id": context.user_id})
            
            session.commit()
            return ServiceResponse.success_res(
                data={"new_quantity": new_qty},
                message=f"Stock updated for {code}. New total: {new_qty}. Reason: {reason}."
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating stock for {code}: {e}")
            return ServiceResponse.error_res(f"Failed to update stock: {str(e)}", "STOCK_UPDATE_ERROR")

    @command(
        name="stock.list", 
        description="Lists products, optionally filtered by category or text search.",
        params_schema={"category": "string", "filter_text": "string"}
    )
    def list_products(self, session: Session, context: CoreContext, category: Optional[str] = None, filter_text: Optional[str] = None) -> ServiceResponse:
        """Lists products, optionally filtered by category or text search."""
        try:
            query_str = "SELECT * FROM products WHERE 1=1"
            params = {}
            
            if category:
                query_str += " AND category = :category"
                params["category"] = category
            
            if filter_text:
                query_str += " AND (name LIKE :filter OR code LIKE :filter)"
                params["filter"] = f"%{filter_text}%"
            
            result = session.execute(text(query_str), params).mappings().all()
            return ServiceResponse.success_res(data=[dict(r) for r in result], message="Products listed successfully.")
        except Exception as e:
            logger.error(f"Error listing products: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_LIST_ERROR")

    @command(
        name="stock.history", 
        description="Retrieves the movement history for a specific product.",
        params_schema={"code": "string"}
    )
    def get_stock_history(self, session: Session, context: CoreContext, code: str) -> ServiceResponse:
        """Retrieves the movement history for a specific product."""
        try:
            query = text("SELECT * FROM stock_movements WHERE product_code = :code ORDER BY created_at DESC")
            result = session.execute(query, {"code": code}).mappings().all()
            return ServiceResponse.success_res(data=[dict(r) for r in result], message="Movement history retrieved.")
        except Exception as e:
            logger.error(f"Error fetching history for {code}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_GET_HISTORY_ERROR")

    @command(
        name="stock.low", 
        description="Lists products that are below the critical threshold.",
        params_schema={"threshold": "float"}
    )
    def get_low_stock(self, session: Session, context: CoreContext, threshold: float = 5.0) -> ServiceResponse:
        """Lists products that are below the critical threshold."""
        try:
            query = text("SELECT * FROM products WHERE quantity < :threshold ORDER BY quantity ASC")
            result = session.execute(query, {"threshold": threshold}).mappings().all()
            return ServiceResponse.success_res(data=[dict(r) for r in result], message="Low stock products retrieved.")
        except Exception as e:
            logger.error(f"Error fetching low stock: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_LOW_STOCK_ERROR")

# Singleton for the module
stock_service = StockService()
