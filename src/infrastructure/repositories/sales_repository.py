import logging
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.repositories.base_repository import BaseRepository

logger = logging.getLogger("OmniCore.SalesRepository")


class SalesRepository(BaseRepository):
    """
    Infrastructure Layer: Encapsulates all SQL operations for the Sales domain.
    Ensures that the application layer remains agnostic of the database schema.
    """

    def __init__(self, session: Session, business_id: str):
        super().__init__(session, business_id)

    # --- Cash Box Management ---
    def open_cash_box(self, monto_inicial: float) -> int:
        result = self.session.execute(
            text(
                """
                UPDATE cash_box 
                SET abierta = true, efectivo_inicial = :monto, ventas_efectivo = 0, ventas_digital = 0, hora_apertura = CURRENT_TIMESTAMP 
                WHERE app_id = :app_id
            """
            ),
            {"monto": monto_inicial, "app_id": self.app_id},
        )
        return result.rowcount

    def get_cash_box(self) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(
                text("SELECT * FROM cash_box WHERE app_id = :app_id"),
                {"app_id": self.app_id},
            )
            .mappings()
            .first()
        )

    def close_cash_box(self, monto_real: float) -> None:
        self.session.execute(
            text(
                """
                UPDATE cash_box 
                SET abierta = false, hora_cierre = CURRENT_TIMESTAMP, monto_cierre_real = :real 
                WHERE app_id = :app_id
            """
            ),
            {"real": monto_real, "app_id": self.app_id},
        )

    def update_cash_box_totals(self, amount: float, is_digital: bool) -> None:
        column = "ventas_digital" if is_digital else "ventas_efectivo"
        self.session.execute(
            text(
                f"UPDATE cash_box SET {column} = {column} + :total WHERE app_id = :app_id"
            ),
            {"total": amount, "app_id": self.app_id},
        )

    # --- Sales Processing ---
    def create_sale(
        self,
        client_name: str,
        total: float,
        method: str,
        paga_con: float,
        vuelto: float,
        status: str = "COMPLETED",
    ) -> int:
        result = self.session.execute(
            text(
                """
                INSERT INTO sales (app_id, client_name, total_amount, status, payment_method, paga_con, vuelto) 
                VALUES (:app_id, :name, :total, :status, :method, :paga_con, :vuelto) 
                RETURNING id
            """
            ),
            {
                "app_id": self.app_id,
                "name": client_name,
                "total": total,
                "status": status,
                "method": method,
                "paga_con": paga_con,
                "vuelto": vuelto,
            },
        )
        return result.scalar()

    def add_sale_item(
        self,
        sale_id: int,
        product_code: str,
        quantity: int,
        price: float,
        subtotal: float,
    ) -> None:
        self.session.execute(
            text(
                """
                INSERT INTO sale_items (sale_id, sku, quantity, unit_price, subtotal) 
                VALUES (:sale_id, :code, :qty, :price, :sub)
            """
            ),
            {
                "sale_id": sale_id,
                "code": product_code,
                "qty": quantity,
                "price": price,
                "sub": subtotal,
            },
        )

    def get_sale_by_id(self, sale_id: int) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(
                text("SELECT * FROM sales WHERE id = :id AND app_id = :app_id"),
                {"id": sale_id, "app_id": self.app_id},
            )
            .mappings()
            .first()
        )

    # ... alias and report methods also need app_id ...
    # (Simplified for brevity, assuming similar pattern for all SQL)
