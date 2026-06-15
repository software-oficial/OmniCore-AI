import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.StockService")

class StockService:
    """
    Pure Business Logic for Stock Management.
    Agnostic to the database source; relies on the injected session.
    Ported from plataforma-stock.
    """

    @command(
        name="stock.sync_delta",
        description="Retrieves only the products that have changed since a given timestamp. Optimized for mobile app synchronization.",
        params_schema={"since": "string"}
    )
    def get_sync_delta(self, session: Session, context: CoreContext, since: str) -> ServiceResponse:
        """Returns products updated after the 'since' timestamp."""
        try:
            query = text("SELECT * FROM products WHERE updated_at > :since")
            result = session.execute(query, {"since": since}).mappings().all()
            return ServiceResponse.success_res(
                data=[dict(r) for r in result], 
                message=f"Sync delta retrieved. {len(result)} items updated."
            )
        except Exception as e:
            logger.error(f"Error fetching sync delta: {e}")
            return ServiceResponse.error_res(f"Sync failed: {str(e)}", "STOCK_SYNC_ERROR")

    @command(
        name="stock.import_validated",
        description="Imports products from a list, performing a pre-validation check to avoid partial corruption.",
        params_schema={"products": "list[dict]"}
    )
    def import_validated(self, session: Session, context: CoreContext, products: List[Dict[str, Any]]) -> ServiceResponse:
        """Imports products with pre-validation."""
        try:
            # 1. Pre-validation phase
            for p in products:
                if not p.get('code') or not p.get('name') or p.get('price') is None:
                    return ServiceResponse.error_res(
                        f"Validation failed for product {p.get('code', 'Unknown')}: Missing required fields.", 
                        "IMPORT_VALIDATION_ERROR"
                    )

            # 2. Execution phase (uses bulk_add for efficiency)
            return self.bulk_add_products(session, context, products)
        except Exception as e:
            logger.error(f"Error in validated import: {e}")
            return ServiceResponse.error_res(f"Import failed: {str(e)}", "IMPORT_ERROR")

    @command(
        name="stock.import_with_mapping",
        description="Imports products using a dynamic mapping definition. Translates user-defined column names to internal fields.",
        params_schema={"data": "list[dict]", "mapping": "dict"}
    )
    def import_with_mapping(self, session: Session, context: CoreContext, data: List[Dict[str, Any]], mapping: Dict[str, str]) -> ServiceResponse:
        """
        Imports products by mapping external keys to internal fields.
        Example mapping: {'code': 'SKU', 'name': 'Product Name', 'price': 'Cost'}
        """
        try:
            normalized_products = []
            for row in data:
                # Translate row based on mapping
                normalized = {
                    "code": row.get(mapping.get("code")),
                    "name": row.get(mapping.get("name")),
                    "price": row.get(mapping.get("price")),
                    "quantity": row.get(mapping.get("quantity"), 0),
                    "category": row.get(mapping.get("category")),
                    "is_weight": row.get(mapping.get("is_weight"), False)
                }
                
                # Basic validation of translated data
                if not normalized["code"] or not normalized["name"] or normalized["price"] is None:
                    return ServiceResponse.error_res(
                        f"Mapping error: Row missing required data. Row: {row}", 
                        "MAPPING_VALIDATION_ERROR"
                    )
                normalized_products.append(normalized)
            
            # Use existing bulk_add logic for the final insertion
            return self.bulk_add_products(session, context, normalized_products)
        except Exception as e:
            logger.error(f"Error in import_with_mapping: {e}")
            return ServiceResponse.error_res(f"Import failed: {str(e)}", "IMPORT_MAPPING_ERROR")

    @command(
        name="stock.add",
 
        description="Adds a new product and records the initial movement in the ledger. Upserts if code exists.",
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
            
            return ServiceResponse.success_res(
                data={"product_id": product_id, "code": code},
                message=f"Product {name} processed successfully."
            )
        except Exception as e:
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
        """Updates the quantity of a product. Prevents negative stock."""
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
            
            return ServiceResponse.success_res(
                data={"new_quantity": new_qty},
                message=f"Stock updated for {code}. New total: {new_qty}. Reason: {reason}."
            )
        except Exception as e:
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
            query = text("SELECT * FROM products WHERE quantity < :threshold ORDER by quantity ASC")
            result = session.execute(query, {"threshold": threshold}).mappings().all()
            return ServiceResponse.success_res(data=[dict(r) for r in result], message="Low stock products retrieved.")
        except Exception as e:
            logger.error(f"Error fetching low stock: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_LOW_STOCK_ERROR")

    @command(
        name="stock.delete", 
        description="Deletes a product from the inventory.",
        params_schema={"code": "string"}
    )
    def delete_product(self, session: Session, context: CoreContext, code: str) -> ServiceResponse:
        """Deletes a product from the inventory."""
        try:
            query = text("DELETE FROM products WHERE code = :code")
            result = session.execute(query, {"code": code})
            
            if result.rowcount == 0:
                return ServiceResponse.error_res(f"Product {code} not found", "PRODUCT_NOT_FOUND")
                
            return ServiceResponse.success_res(message=f"Product {code} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting product {code}: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_DELETE_ERROR")

    @command(
        name="stock.bulk_add", 
        description="Adds multiple products in a single transaction. Optimized for large imports.",
        params_schema={"products": "list[dict]"}
    )
    def bulk_add_products(self, session: Session, context: CoreContext, products: List[Dict[str, Any]]) -> ServiceResponse:
        """Adds multiple products in a single transaction."""
        try:
            success_count = 0
            error_count = 0
            
            for p in products:
                res = self.add_product(
                    session, 
                    context, 
                    code=p.get('code'), 
                    name=p.get('name'), 
                    price=p.get('price'), 
                    quantity=p.get('cantidad', p.get('quantity', 0)), 
                    category=p.get('category'), 
                    is_weight=p.get('is_weight', False)
                )
                if res.success:
                    success_count += 1
                else:
                    error_count += 1
            
            return ServiceResponse.success_res(
                data={"success": success_count, "errors": error_count}, 
                message=f"Bulk processing completed. {success_count} added, {error_count} failed."
            )
        except Exception as e:
            logger.error(f"Error in bulk_add_products: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "STOCK_BULK_ADD_ERROR")

    @command(
        name="stock.audit_inventory", 
        description="Performs a full inventory audit by comparing recorded stock with a physical count. Records discrepancies in the ledger.",
        params_schema={"audit_data": "list[dict]"}
    )
    def audit_inventory(self, session: Session, context: CoreContext, audit_data: List[Dict[str, Any]]) -> ServiceResponse:
        """
        Performs an inventory audit. 
        audit_data: List of {'code': '...', 'physical_count': 10}
        """
        try:
            results = []
            discrepancies = 0
            
            for entry in audit_data:
                code = entry.get('code')
                physical_qty = entry.get('physical_count')
                
                if not code or physical_qty is None:
                    continue
                
                res = session.execute(text("SELECT quantity FROM products WHERE code = :code"), {"code": code}).scalar()
                if res is None:
                    results.append({"code": code, "status": "NOT_FOUND", "message": "Product not found in database"})
                    continue
                
                recorded_qty = res
                diff = physical_qty - recorded_qty
                
                if diff != 0:
                    discrepancies += 1
                    session.execute(
                        text("UPDATE products SET quantity = :qty, updated_at = CURRENT_TIMESTAMP WHERE code = :code"),
                        {"qty": physical_qty, "code": code}
                    )
                    session.execute(
                        text("INSERT INTO stock_movements (product_code, amount, reason, user_id) VALUES (:code, :amount, :reason, :user_id)"),
                        {"code": code, "amount": diff, "reason": "AUDIT_DISCREPANCY", "user_id": context.user_id}
                    )
                    results.append({"code": code, "status": "ADJUSTED", "diff": diff, "new_qty": physical_qty})
                else:
                    results.append({"code": code, "status": "MATCHED", "qty": recorded_qty})
            
            return ServiceResponse.success_res(
                data={"results": results, "total_discrepancies": discrepancies},
                message=f"Audit completed. {discrepancies} discrepancies adjusted."
            )
        except Exception as e:
            logger.error(f"Error during stock audit: {e}")
            return ServiceResponse.error_res(f"Audit failure: {str(e)}", "STOCK_AUDIT_ERROR")

    @command(
        name="stock.transfer", 
        description="Transfers stock between different warehouse locations or zones.",
        params_schema={"code": "string", "amount": "int", "from_zone": "string", "to_zone": "string"}
    )
    def transfer_stock(self, session: Session, context: CoreContext, code: str, amount: int, from_zone: str, to_zone: str) -> ServiceResponse:
        """Transfers stock between zones."""
        try:
            res = session.execute(text("SELECT quantity FROM products WHERE code = :code"), {"code": code}).scalar()
            if res is None:
                return ServiceResponse.error_res(f"Product {code} not found", "PRODUCT_NOT_FOUND")
            
            if res < amount:
                return ServiceResponse.error_res("Insufficient stock for transfer", "STOCK_INSUFFICIENT")
            
            reason = f"TRANSFER: {from_zone} -> {to_zone}"
            session.execute(
                text("INSERT INTO stock_movements (product_code, amount, reason, user_id) VALUES (:code, :amount, :reason, :user_id)"),
                {"code": code, "amount": 0, "reason": reason, "user_id": context.user_id}
            )
            
            return ServiceResponse.success_res(message=f"Transfer of {amount} units of {code} from {from_zone} to {to_zone} recorded.")
        except Exception as e:
            logger.error(f"Error in stock transfer for {code}: {e}")
            return ServiceResponse.error_res(f"Transfer failed: {str(e)}", "STOCK_TRANSFER_ERROR")

# Singleton for the module
stock_service = StockService()
