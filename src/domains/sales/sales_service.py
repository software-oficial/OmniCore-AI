import logging
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.domains.stock.stock_service import stock_service

logger = logging.getLogger("OmniCore.SalesService")


class SaleItem(BaseModel):
    """Strict model for a sale item to avoid 'list[dict]' ambiguity."""

    product_code: str = Field(..., description="The unique SKU/code of the product")
    quantity: int = Field(..., gt=0, description="Quantity must be greater than zero")


class SaleCobrarModel(BaseModel):
    """Strict contract for the 'venta.cobrar' command."""

    cliente: str = Field(..., description="Customer name or ID")
    items: List[SaleItem] = Field(
        ..., min_length=1, description="List of products to sell"
    )
    metodo_pago: str = Field(
        ..., description="Payment method (e.g., Efectivo, Transferencia)"
    )
    paga_con: float = Field(0.0, ge=0, description="Amount paid by customer")
    alias: Optional[str] = Field(None, description="Alias for transfer payments")


class SalesService:
    """
    Pure Business Logic for Sales and Order Management.
    Implements Cash Box management, Alias credit limits, and atomic Sale processing.
    Stateless and depends on injected session.
    Ported from plataforma-stock.
    """

    # --- Cash Box Management ---

    @command(
        name="user.create_employee",
        description="Creates a new employee user for the business with a specific role.",
        params_model={"username": "string", "password": "string", "role": "string"},
    )
    def create_employee(
        self,
        session: Session,
        context: CoreContext,
        username: str,
        password: str,
        role: str = "employee",
    ) -> ServiceResponse:
        """Creates an employee user in the business database."""
        try:
            # In a real scenario, password would be hashed
            session.execute(
                text("INSERT INTO users (username, password) VALUES (:user, :pass)"),
                {"user": username, "pass": password},
            )
            return ServiceResponse.success_res(
                message=f"Employee {username} created successfully."
            )
        except Exception as e:
            logger.error(f"Error creating employee {username}: {e}")
            return ServiceResponse.error_res(
                f"User creation failed: {str(e)}", "USER_CREATE_ERROR"
            )

    @command(
        name="user.change_role",
        description="Updates the role of an existing employee.",
        params_model={"username": "string", "new_role": "string"},
    )
    def change_role(
        self, session: Session, context: CoreContext, username: str, new_role: str
    ) -> ServiceResponse:
        """Updates user role."""
        try:
            session.execute(
                text("UPDATE users SET role = :role WHERE username = :user"),
                {"role": new_role, "user": username},
            )
            return ServiceResponse.success_res(
                message=f"Role for {username} updated to {new_role}."
            )
        except Exception as e:
            logger.error(f"Error updating role for {username}: {e}")
            return ServiceResponse.error_res(
                f"Update failed: {str(e)}", "USER_ROLE_ERROR"
            )

    @command(
        name="sales.report_daily",
        description="Generates a detailed financial report of the day, split by payment method.",
        params_model={"date": "string"},
    )
    def report_daily(
        self, session: Session, context: CoreContext, date: str
    ) -> ServiceResponse:
        """Generates a daily financial report."""
        try:
            # Total Sales
            total_res = session.execute(
                text(
                    "SELECT SUM(total_amount) as total FROM sales WHERE DATE(created_at) = :date"
                ),
                {"date": date},
            ).scalar()

            # Split by method
            split_res = (
                session.execute(
                    text(
                        "SELECT payment_method, SUM(total_amount) as sum FROM sales WHERE DATE(created_at) = :date GROUP BY payment_method"
                    ),
                    {"date": date},
                )
                .mappings()
                .all()
            )

            split_data = {row["payment_method"]: float(row["sum"]) for row in split_res}

            return ServiceResponse.success_res(
                data={"total": float(total_res or 0), "breakdown": split_data},
                message=f"Financial report for {date} generated successfully.",
            )
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return ServiceResponse.error_res(
                f"Report failure: {str(e)}", "REPORT_ERROR"
            )

    @command(
        name="sales.handle_mp_webhook",
        description="Processes an incoming MercadoPago webhook notification to automatically complete a pending sale and deduct stock.",
        params_model={
            "payment_id": "string",
            "external_reference": "string",
            "status": "string",
        },
    )
    def handle_mp_webhook(
        self,
        session: Session,
        context: CoreContext,
        payment_id: str,
        external_reference: str,
        status: str,
    ) -> ServiceResponse:
        """
        Handles MP payment notifications.
        external_reference is the sale_id.
        """
        try:
            if status != "approved":
                return ServiceResponse.success_res(
                    message=f"Payment {payment_id} status is {status}. No action taken."
                )

            # 1. Find the pending sale
            sale = (
                session.execute(
                    text("SELECT * FROM sales WHERE id = :id AND status = 'PENDING'"),
                    {"id": external_reference},
                )
                .mappings()
                .first()
            )

            if not sale:
                return ServiceResponse.error_res(
                    "Pending sale not found for this reference", "SALE_NOT_FOUND"
                )

            # 2. Mark sale as completed
            session.execute(
                text(
                    "UPDATE sales SET status = 'COMPLETED', payment_method = 'MercadoPago' WHERE id = :id"
                ),
                {"id": external_reference},
            )

            # 3. Deduct stock for all items in this sale
            items = (
                session.execute(
                    text(
                        "SELECT product_code, quantity FROM sale_items WHERE sale_id = :id"
                    ),
                    {"id": external_reference},
                )
                .mappings()
                .all()
            )

            for item in items:
                stock_service.update_stock(
                    session,
                    context,
                    code=item["product_code"],
                    quantity=-item["quantity"],
                    reason=f"MP_PAYMENT_{payment_id}",
                )

            return ServiceResponse.success_res(
                data={"sale_id": external_reference, "status": "COMPLETED"},
                message=f"Payment {payment_id} processed. Sale {external_reference} completed and stock deducted.",
            )
        except Exception as e:
            logger.error(
                f"Error handling MP webhook for sale {external_reference}: {e}"
            )
            return ServiceResponse.error_res(
                f"Webhook processing failed: {str(e)}", "WEBHOOK_ERROR"
            )

    @command(
        name="user.grant_permission",
        description="Grants a specific granular permission to a user.",
        params_model={"username": "string", "permission_key": "string"},
    )
    def grant_permission(
        self, session: Session, context: CoreContext, username: str, permission_key: str
    ) -> ServiceResponse:
        """Grants a specific permission key to a user."""
        try:
            # First resolve user_id
            user = (
                session.execute(
                    text("SELECT id FROM users WHERE username = :u"), {"u": username}
                )
                .mappings()
                .first()
            )
            if not user:
                return ServiceResponse.error_res("User not found", "USER_NOT_FOUND")

            # Grant permission
            session.execute(
                text(
                    "INSERT INTO user_permissions (user_id, permission_key) VALUES (:uid, :perm) ON CONFLICT DO NOTHING"
                ),
                {"uid": user["id"], "perm": permission_key},
            )
            return ServiceResponse.success_res(
                message=f"Permission {permission_key} granted to {username}."
            )
        except Exception as e:
            logger.error(f"Error granting permission to {username}: {e}")
            return ServiceResponse.error_res(f"Grant failed: {str(e)}", "PERM_ERROR")

    @command(
        name="user.revoke_permission",
        description="Revokes a specific granular permission from a user.",
        params_model={"username": "string", "permission_key": "string"},
    )
    def revoke_permission(
        self, session: Session, context: CoreContext, username: str, permission_key: str
    ) -> ServiceResponse:
        """Revokes a specific permission key from a user."""
        try:
            user = (
                session.execute(
                    text("SELECT id FROM users WHERE username = :u"), {"u": username}
                )
                .mappings()
                .first()
            )
            if not user:
                return ServiceResponse.error_res("User not found", "USER_NOT_FOUND")

            session.execute(
                text(
                    "DELETE FROM user_permissions WHERE user_id = :uid AND permission_key = :perm"
                ),
                {"uid": user["id"], "perm": permission_key},
            )
            return ServiceResponse.success_res(
                message=f"Permission {permission_key} revoked from {username}."
            )
        except Exception as e:
            logger.error(f"Error revoking permission from {username}: {e}")
            return ServiceResponse.error_res(
                f"Revocation failed: {str(e)}", "PERM_ERROR"
            )

    @command(
        name="cash.open",
        description="Opens a physical cash box for the day with an initial amount.",
        params_model={"monto_inicial": "float", "credential_id": "string"},
    )
    def open_cash_box(
        self, session: Session, context: CoreContext, monto_inicial: float
    ) -> ServiceResponse:
        """Opens a physical cash box for the day."""
        if not context.credential_id:
            return ServiceResponse.error_res(
                "credential_id is required for cash box operations.",
                "CREDENTIAL_REQUIRED",
            )
        try:
            query = text(
                """
                UPDATE cash_box 
                SET abierta = true, efectivo_inicial = :monto, ventas_efectivo = 0, ventas_digital = 0, hora_apertura = CURRENT_TIMESTAMP 
                WHERE credential_id = :cid
            """
            )
            result = cast(
                CursorResult,
                session.execute(
                    query, {"monto": monto_inicial, "cid": context.credential_id}
                ),
            )

            if result.rowcount == 0:
                return ServiceResponse.error_res(
                    "Cash box not found for the specified credential",
                    "CASH_BOX_NOT_FOUND",
                )

            return ServiceResponse.success_res(
                message=f"Cash box opened successfully with ${monto_inicial}."
            )
        except Exception as e:
            logger.error(f"Error opening cash box: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "CASH_BOX_ERROR"
            )

    @command(
        name="cash.close",
        description="Closes the cash box and calculates the difference (Surcharge/Shortage).",
        params_model={"monto_real": "float"},
    )
    def close_cash_box(
        self, session: Session, context: CoreContext, monto_real: float
    ) -> ServiceResponse:
        """Closes the cash box and calculates the difference."""
        try:
            # 1. Get current state
            query = text("SELECT * FROM cash_box WHERE id = 1")
            state = session.execute(query).mappings().first()

            if not state or not state["abierta"]:
                return ServiceResponse.error_res(
                    "Cash box is closed or not found", "CASH_BOX_CLOSED"
                )

            # 2. Close and record real amount
            update_query = text(
                """
                UPDATE cash_box 
                SET abierta = false, hora_cierre = CURRENT_TIMESTAMP, monto_cierre_real = :real 
                WHERE id = 1
            """
            )
            session.execute(update_query, {"real": monto_real})

            # 3. Calculate Balance
            expected = float(state["efectivo_inicial"]) + float(
                state["ventas_efectivo"]
            )
            resumen = {
                "expected": expected,
                "actual": monto_real,
                "difference": monto_real - expected,
            }

            return ServiceResponse.success_res(
                data=resumen, message="Cash box closed and balanced."
            )
        except Exception as e:
            logger.error(f"Error closing cash box: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "CASH_BOX_ERROR"
            )

    @command(
        name="cash.status",
        description="Retrieves the current status of the cash box.",
        params_model={},
    )
    def get_cash_box_status(
        self, session: Session, context: CoreContext
    ) -> ServiceResponse:
        """Retorna el estado actual de la caja."""
        try:
            query = text("SELECT * FROM cash_box WHERE id = 1")
            status = session.execute(query).mappings().first()
            return ServiceResponse.success_res(
                data=dict(status) if status else None,
                message="Cash box status retrieved.",
            )
        except Exception as e:
            logger.error(f"Error getting cash box status: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "CASH_BOX_ERROR"
            )

    # --- Sales Processing ---

    @command(
        name="venta.nueva",
        description="Initializes a new sale session (draft).",
        params_model={},
    )
    def create_new_sale_session(
        self, session: Session, context: CoreContext
    ) -> ServiceResponse:
        """Initializes a sale session."""
        return ServiceResponse.success_res(
            message="Sale session initialized. Use venta.add to add products."
        )

    @command(
        name="venta.add",
        description="Adds a product to the current pending sale.",
        params_model={"codigo": "string", "cantidad": "int"},
    )
    def add_to_sale(
        self, session: Session, context: CoreContext, codigo: str, cantidad: int
    ) -> ServiceResponse:
        """Adds a product to the current pending sale."""
        res = stock_service.get_product(session, context, code=codigo)
        if res.success:
            return ServiceResponse.success_res(
                data={"product": res.data, "quantity": cantidad},
                message="Product available and ready to be added to sale.",
            )
        return res

    @command(
        name="venta.cobrar",
        description="Processes the final payment, deducts stock, and updates the cash box.",
        params_model=SaleCobrarModel,
        example={
            "cliente": "Juan Perez",
            "items": [
                {"product_code": "P001", "quantity": 2},
                {"product_code": "P005", "quantity": 1},
            ],
            "metodo_pago": "Efectivo",
            "paga_con": 500.0,
            "alias": None,
        },
    )
    def process_sale(
        self,
        session: Session,
        context: CoreContext,
        cliente: str,
        items: List[Dict[str, Any]],
        payment_method: str,
        paga_con: float = 0.0,
        alias: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Atomic sale process: Validates stock, checks alias limits, creates records, deducts inventory, and updates cash box.
        """
        try:
            total_amount = 0.0
            processed_items = []

            # 1. Validation and Total Calculation
            for item in items:
                product_code = item["product_code"]
                qty = item["quantity"]
                product_res = stock_service.get_product(
                    session, context, code=product_code
                )

                if not product_res.success:
                    return ServiceResponse.error_res(
                        f"Product {product_code} not found", "PRODUCT_NOT_FOUND"
                    )

                product = product_res.data
                if product["quantity"] < qty:
                    return ServiceResponse.error_res(
                        f"Insufficient stock for {product['name']}",
                        "STOCK_INSUFFICIENT",
                    )

                subtotal = float(product["price"]) * qty
                total_amount += subtotal
                processed_items.append(
                    {
                        "product_code": product_code,
                        "qty": qty,
                        "price": float(product["price"]),
                        "subtotal": subtotal,
                    }
                )

            # 2. Alias Limit Validation (Transfers)
            if payment_method == "Transferencia" and alias:
                alias_query = text(
                    "SELECT acumulado, limite FROM aliases WHERE nombre = :nombre"
                )
                alias_data = (
                    session.execute(alias_query, {"nombre": alias}).mappings().first()
                )
                if not alias_data:
                    return ServiceResponse.error_res(
                        "Alias not registered.", "ALIAS_NOT_FOUND"
                    )
                if (float(alias_data["acumulado"] or 0)) + total_amount > float(
                    alias_data["limite"]
                ):
                    return ServiceResponse.error_res(
                        f"Limit exceeded for alias {alias}.", "ALIAS_LIMIT_EXCEEDED"
                    )

            # 3. Cash Payment Validation
            vuelto = 0.0
            if payment_method == "Efectivo":
                if paga_con < total_amount:
                    return ServiceResponse.error_res(
                        "Insufficient cash amount.", "CASH_INSUFFICIENT"
                    )
                vuelto = paga_con - total_amount

            # 4. Atomic Persistence
            sale_query = text(
                """
                INSERT INTO sales (client_name, total_amount, status, payment_method, paga_con, vuelto) 
                VALUES (:name, :total, 'COMPLETED', :method, :paga_con, :vuelto) 
                RETURNING id
            """
            )
            sale_id = session.execute(
                sale_query,
                {
                    "name": cliente,
                    "total": total_amount,
                    "method": payment_method,
                    "paga_con": paga_con,
                    "vuelto": vuelto,
                },
            ).scalar()

            for pi in processed_items:
                item_query = text(
                    """
                    INSERT INTO sale_items (sale_id, product_code, quantity, unit_price, subtotal) 
                    VALUES (:sale_id, :code, :qty, :price, :sub)
                """
                )
                session.execute(
                    item_query,
                    {
                        "sale_id": sale_id,
                        "code": pi["product_code"],
                        "qty": pi["qty"],
                        "price": pi["price"],
                        "sub": pi["subtotal"],
                    },
                )

            # 5. Update Cash Box
            col = (
                "ventas_efectivo" if payment_method == "Efectivo" else "ventas_digital"
            )
            cash_query = text(
                f"UPDATE cash_box SET {col} = {col} + :total WHERE id = 1"
            )
            session.execute(cash_query, {"total": total_amount})

            # 6. Update Alias Accumulator
            if payment_method == "Transferencia" and alias:
                alias_update = text(
                    "UPDATE aliases SET acumulado = acumulado + :total WHERE nombre = :nombre"
                )
                session.execute(alias_update, {"total": total_amount, "nombre": alias})

            # 7. Deduct Stock (Ledger)
            for pi in processed_items:
                stock_service.update_stock(
                    session,
                    context,
                    code=pi["product_code"],
                    quantity=-pi["qty"],
                    reason=f"SALE_{sale_id}",
                )

            return ServiceResponse.success_res(
                data={"sale_id": sale_id, "total": total_amount, "vuelto": vuelto},
                message="Sale processed and stock deducted successfully.",
            )
        except Exception as e:
            logger.error(f"Critical error processing sale: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SALES_PROCESS_ERROR"
            )

    @command(
        name="venta.cancelar",
        description="Cancels a pending sale and restores stock if already deducted.",
        params_model={"sale_id": "int"},
    )
    def cancel_sale(
        self, session: Session, context: CoreContext, sale_id: int
    ) -> ServiceResponse:
        """Cancels a sale."""
        try:
            sale = (
                session.execute(
                    text("SELECT status FROM sales WHERE id = :id"), {"id": sale_id}
                )
                .mappings()
                .first()
            )
            if not sale or sale["status"] == "COMPLETED":
                return ServiceResponse.error_res(
                    "Sale cannot be cancelled.", "SALE_INVALID"
                )

            session.execute(
                text("UPDATE sales SET status = 'CANCELLED' WHERE id = :id"),
                {"id": sale_id},
            )
            return ServiceResponse.success_res(message="Sale cancelled successfully.")
        except Exception as e:
            logger.error(f"Error cancelling sale {sale_id}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SALE_CANCEL_ERROR"
            )

    @command(
        name="venta.create_link",
        description="Creates a pending sale and generates a MercadoPago payment link.",
        params_model={"codigo": "string", "cantidad": "int", "cliente": "string"},
    )
    def create_payment_link(
        self,
        session: Session,
        context: CoreContext,
        codigo: str,
        cantidad: int,
        cliente: str,
    ) -> ServiceResponse:
        """Creates a pending sale and generates a payment link."""
        from src.domains.sales.mp_service import mp_service

        try:
            # 1. Create pending sale

            product_res = stock_service.get_product(session, context, code=codigo)
            if not product_res.success:
                return product_res

            total = float(product_res.data["price"]) * cantidad

            sale_query = text(
                "INSERT INTO sales (client_name, total_amount, status, payment_method) VALUES (:name, :total, 'PENDING', 'MercadoPago') RETURNING id"
            )
            sale_id = session.execute(
                sale_query, {"name": cliente, "total": total}
            ).scalar()

            session.execute(
                text(
                    "INSERT INTO sale_items (sale_id, product_code, quantity, unit_price, subtotal) VALUES (:sid, :code, :qty, :price, :sub)"
                ),
                {
                    "sid": sale_id,
                    "code": codigo,
                    "qty": cantidad,
                    "price": product_res.data["price"],
                    "sub": total,
                },
            )

            # 2. Generate MP Link
            from src.core.system_service import system_service

            token_res = system_service.get_setting(
                session=session, context=context, key="mp_access_token"
            )
            if not token_res.success:
                return token_res

            mp_token = token_res.data.get("value")

            if not mp_token:
                return ServiceResponse.error_res(
                    "MP Token not configured in system settings.", "CONFIG_MISSING"
                )

            from typing import cast

            mp_res = mp_service.create_payment(
                context=context,
                amount=total,
                description=f"Pago de producto {cast(dict, product_res.data)['name']}",
                external_reference=str(sale_id),
                access_token=mp_token,
            )

            if mp_res.success:
                data_mp = cast(dict, mp_res.data)
                return ServiceResponse.success_res(
                    data={"payment_url": data_mp["init_point"], "sale_id": sale_id},
                    message="Payment link generated successfully.",
                )
            return mp_res
        except Exception as e:
            logger.error(f"Error creating payment link: {e}")
            return ServiceResponse.error_res(
                f"Internal la error: {str(e)}", "MP_LINK_ERROR"
            )

    # --- Alias Management ---

    @command(
        name="alias.add",
        description="Creates a new alias with a specific credit/recollection limit.",
        params_model={"nombre": "string", "limite": "float"},
    )
    def add_alias(
        self, session: Session, context: CoreContext, nombre: str, limite: float
    ) -> ServiceResponse:
        """Creates a new alias."""
        try:
            import uuid

            alias_id = str(uuid.uuid4())[:8]
            session.execute(
                text(
                    "INSERT INTO aliases (id, nombre, limite, acumulado) VALUES (:id, :nombre, :limite, 0)"
                ),
                {"id": alias_id, "nombre": nombre, "limite": limite},
            )
            return ServiceResponse.success_res(
                message=f"Alias {nombre} created successfully."
            )
        except Exception as e:
            logger.error(f"Error adding alias: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "ALIAS_ADD_ERROR"
            )

    @command(
        name="alias.list",
        description="Lists all aliases and their current accumulations.",
        params_model={},
    )
    def list_aliases(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Lists all aliases."""
        try:
            result = session.execute(text("SELECT * FROM aliases")).mappings().all()
            return ServiceResponse.success_res(
                data=[dict(a) for a in result], message="Aliases listed successfully."
            )
        except Exception as e:
            logger.error(f"Error listing aliases: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "ALIAS_LIST_ERROR"
            )

    @command(
        name="alias.delete",
        description="Deletes an alias from the system.",
        params_model={"alias_id": "string"},
    )
    def delete_alias(
        self, session: Session, context: CoreContext, alias_id: str
    ) -> ServiceResponse:
        """Deletes an alias."""
        try:
            session.execute(
                text("DELETE FROM aliases WHERE id = :id"), {"id": alias_id}
            )
            return ServiceResponse.success_res(
                message=f"Alias {alias_id} deleted successfully."
            )
        except Exception as e:
            logger.error(f"Error deleting alias: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "ALIAS_DELETE_ERROR"
            )


# Singleton
sales_service = SalesService()
