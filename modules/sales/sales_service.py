import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse
from modules.stock.stock_service import stock_service

logger = logging.getLogger("OmniCore.SalesService")

class SalesService:
    """
    Pure Business Logic for Sales and Order Management.
    Implements Cash Box management and atomic Sale processing.
    Stateless and depends on injected session.
    """

    # --- Cash Box Management ---

    def open_cash_box(self, session: Session, context: CoreContext, cash_box_id: int, initial_amount: float) -> ServiceResponse:
        """Opens a physical cash box for the day."""
        try:
            query = text("""
                UPDATE cash_box 
                SET abierta = true, efectivo_inicial = :monto, ventas_efectivo = 0, ventas_digital = 0, hora_apertura = CURRENT_TIMESTAMP 
                WHERE id = :id
            """)
            result = session.execute(query, {"monto": initial_amount, "id": cash_box_id})
            session.commit()
            
            if result.rowcount == 0:
                return ServiceResponse.error_res("Cash box not found", "CASH_BOX_NOT_FOUND")
                
            return ServiceResponse.success_res(message=f"Cash box {cash_box_id} opened successfully.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error opening cash box: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "CASH_BOX_ERROR")

    def close_cash_box(self, session: Session, context: CoreContext, cash_box_id: int, actual_amount: float) -> ServiceResponse:
        """Closes the cash box and calculates the difference (Surcharge/Shortage)."""
        try:
            # 1. Get current state
            query = text("SELECT * FROM cash_box WHERE id = :id")
            state = session.execute(query, {"id": cash_box_id}).mappings().first()
            
            if not state or not state['abierta']:
                return ServiceResponse.error_res("Cash box is closed or not found", "CASH_BOX_CLOSED")
            
            # 2. Close and record real amount
            update_query = text("""
                UPDATE cash_box 
                SET abierta = false, hora_cierre = CURRENT_TIMESTAMP, monto_cierre_real = :real 
                WHERE id = :id
            """)
            session.execute(update_query, {"real": actual_amount, "id": cash_box_id})
            
            # 3. Calculate Balance
            expected = float(state['efectivo_inicial']) + float(state['ventas_efectivo'])
            resumen = {
                "expected": expected,
                "actual": actual_amount,
                "difference": actual_amount - expected
            }
            
            session.commit()
            return ServiceResponse.success_res(data=resumen, message="Cash box closed and balanced.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error closing cash box: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "CASH_BOX_ERROR")

    # --- Sales Processing ---

    def process_sale(self, session: Session, context: CoreContext, client_name: str, items: List[Dict[str, Any]], payment_method: str, cash_box_id: Optional[int] = None, paga_con: float = 0.0) -> ServiceResponse:
        """
        Atomic sale process: Validates stock, creates sale, deducts inventory, and updates cash box.
        Items: [{"product_code": "PROD1", "quantity": 2}, ...]
        """
        try:
            total_amount = 0.0
            processed_items = []

            # 1. Validation and Calculation
            for item in items:
                product_code = item['product_code']
                qty = item['quantity']
                
                # Call stock_service logic internally using SAME session for atomicity
                product_query = text("SELECT name, price, quantity FROM products WHERE code = :code FOR UPDATE")
                product = session.execute(product_query, {"code": product_code}).mappings().first()
                
                if not product:
                    return ServiceResponse.error_res(f"Product {product_code} not found", "PRODUCT_NOT_FOUND")
                
                if product['quantity'] < qty:
                    return ServiceResponse.error_res(f"Insufficient stock for {product['name']}", "STOCK_INSUFFICIENT")
                
                subtotal = float(product['price']) * qty
                total_amount += subtotal
                processed_items.append({
                    "product_code": product_code, "qty": qty, "price": float(product['price']), "subtotal": subtotal
                })

            # 2. Create Sale Record
            sale_query = text("""
                INSERT INTO sales (client_name, total_amount, status, payment_method, paga_con) 
                VALUES (:name, :total, 'COMPLETED', :method, :paga_con) 
                RETURNING id
            """)
            sale_id = session.execute(sale_query, {
                "name": client_name, "total": total_amount, "method": payment_method, "paga_con": paga_con
            }).scalar()

            # 3. Create Sale Items
            for pi in processed_items:
                item_query = text("""
                    INSERT INTO sale_items (sale_id, product_code, quantity, unit_price, subtotal) 
                    VALUES (:sale_id, :code, :qty, :price, :sub)
                """)
                session.execute(item_query, {
                    "sale_id": sale_id, "code": pi['product_code'], "qty": pi['qty'], "price": pi['price'], "sub": pi['subtotal']
                })

            # 4. Deduct Stock
            for pi in processed_items:
                stock_update = text("UPDATE products SET quantity = quantity - :qty WHERE code = :code")
                session.execute(stock_update, {"qty": pi['qty'], "code": pi['product_code']})

            # 5. Update Cash Box if applicable
            if cash_box_id:
                col = "ventas_efectivo" if payment_method == "CASH" else "ventas_digital"
                cash_query = text(f"UPDATE cash_box SET {col} = {col} + :total WHERE id = :id")
                session.execute(cash_query, {"total": total_amount, "id": cash_box_id})

            # Calculate change
            vuelto = paga_con - total_amount if payment_method == "CASH" else 0.0
            session.execute(text("UPDATE sales SET vuelto = :vuelto WHERE id = :id"), {"vuelto": vuelto, "id": sale_id})

            session.commit()
            return ServiceResponse.success_res(
                data={"sale_id": sale_id, "total": total_amount, "vuelto": vuelto},
                message="Sale processed successfully."
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing sale: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "SALES_PROCESS_ERROR")

    @command(
        name="sales.pending",
        description="Creates a pending sale (draft) to be confirmed later.",
        params_schema={"items": "list[dict {product_code: string, quantity: int}]", "customer_id": "string"}
    )
    def create_pending_sale(self, session: Session, context: CoreContext, client_name: str, items: List[Dict[str, Any]], payment_method: str) -> ServiceResponse:
        """Creates a sale in 'PENDING' status, without deducting stock yet."""
        try:
            total_amount = 0.0
            processed_items = []

            for item in items:
                product_code = item['product_code']
                product = session.execute(text("SELECT price FROM products WHERE code = :code"), {"code": product_code}).mappings().first()
                if not product: return ServiceResponse.error_res(f"Product {product_code} not found", "PRODUCT_NOT_FOUND")
                subtotal = float(product['price']) * item['quantity']
                total_amount += subtotal
                processed_items.append({"product_code": item['product_code'], "qty": item['quantity'], "price": float(product['price']), "subtotal": subtotal})

            sale_query = text("""
                INSERT INTO sales (client_name, total_amount, status, payment_method) 
                VALUES (:name, :total, 'PENDING', :method) 
                RETURNING id
            """)
            sale_id = session.execute(sale_query, {"name": client_name, "total": total_amount, "method": payment_method}).scalar()

            for pi in processed_items:
                session.execute(text("""
                    INSERT INTO sale_items (sale_id, product_code, quantity, unit_price, subtotal) 
                    VALUES (:sale_id, :code, :qty, :price, :sub)
                """), {"sale_id": sale_id, "code": pi['product_code'], "qty": pi['qty'], "price": pi['price'], "sub": pi['subtotal']})

            session.commit()
            return ServiceResponse.success_res(data={"sale_id": sale_id}, message="Pending sale created.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating pending sale: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "SALES_PENDING_ERROR")

    def confirm_payment(self, session: Session, context: CoreContext, sale_id: int) -> ServiceResponse:
        """Confirms payment for a pending sale and deducts stock."""
        try:
            sale = session.execute(text("SELECT * FROM sales WHERE id = :id"), {"id": sale_id}).mappings().first()
            if not sale or sale['status'] != 'PENDING':
                return ServiceResponse.error_res("Sale is invalid or already processed", "SALE_INVALID")
            
            items = session.execute(text("SELECT product_code, quantity FROM sale_items WHERE sale_id = :id"), {"id": sale_id}).mappings().all()
            
            for item in items:
                # Lock and update stock
                session.execute(text("UPDATE products SET quantity = quantity - :qty WHERE code = :code"), {"qty": item['quantity'], "code": item['product_code']})
            
            session.execute(text("UPDATE sales SET status = 'COMPLETED', updated_at = CURRENT_TIMESTAMP WHERE id = :id"), {"id": sale_id})
            session.commit()
            return ServiceResponse.success_res(message="Payment confirmed and stock deducted successfully.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error confirming payment: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "SALES_CONFIRM_ERROR")

# Singleton
sales_service = SalesService()
")

# Singleton
sales_service = SalesService()
