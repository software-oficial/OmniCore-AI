import logging
from typing import Any, Dict, List, Optional, cast

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
        return int(cast(Any, result).rowcount)

    def get_cash_box(self) -> Optional[Dict[str, Any]]:
        row = (
            self.session.execute(
                text("SELECT * FROM cash_box WHERE app_id = :app_id"),
                {"app_id": self.app_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

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
        return int(result.scalar())

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
        row = (
            self.session.execute(
                text("SELECT * FROM sales WHERE id = :id AND app_id = :app_id"),
                {"id": sale_id, "app_id": self.app_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def update_sale_status(self, sale_id: int, status: str) -> None:
        self.session.execute(
            text(
                "UPDATE sales SET status = :status WHERE id = :id AND app_id = :app_id"
            ),
            {"status": status, "id": sale_id, "app_id": self.app_id},
        )

    def get_sale_items(self, sale_id: int) -> List[Dict[str, Any]]:
        return [
            dict(row)
            for row in self.session.execute(
                text("SELECT sku, quantity FROM sale_items WHERE sale_id = :id"),
                {"id": sale_id},
            ).mappings()
        ]

    # --- Alias Management ---
    def add_alias(self, alias_id: str, nombre: str, limite: float) -> None:
        self.session.execute(
            text(
                "INSERT INTO aliases (id, app_id, nombre, limite, acumulado) VALUES (:id, :app_id, :nombre, :limite, 0)"
            ),
            {"id": alias_id, "app_id": self.app_id, "nombre": nombre, "limite": limite},
        )

    def get_alias_by_name(self, nombre: str) -> Optional[Dict[str, Any]]:
        row = (
            self.session.execute(
                text(
                    "SELECT * FROM aliases WHERE nombre = :nombre AND app_id = :app_id"
                ),
                {"nombre": nombre, "app_id": self.app_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def update_alias_accumulation(self, nombre: str, amount: float) -> None:
        self.session.execute(
            text(
                "UPDATE aliases SET acumulado = acumulado + :total WHERE nombre = :nombre AND app_id = :app_id"
            ),
            {"total": amount, "nombre": nombre, "app_id": self.app_id},
        )

    def list_all_aliases(self) -> List[Dict[str, Any]]:
        return [
            dict(row)
            for row in self.session.execute(
                text("SELECT * FROM aliases WHERE app_id = :app_id"),
                {"app_id": self.app_id},
            ).mappings()
        ]

    def delete_alias(self, alias_id: str) -> None:
        self.session.execute(
            text("DELETE FROM aliases WHERE id = :id AND app_id = :app_id"),
            {"id": alias_id, "app_id": self.app_id},
        )

    # --- Reports ---
    def get_daily_totals(self, date: str) -> float:
        res = self.session.execute(
            text(
                "SELECT SUM(total_amount) as total FROM sales WHERE DATE(created_at) = :date AND app_id = :app_id"
            ),
            {"date": date, "app_id": self.app_id},
        ).scalar()
        return float(res or 0)

    def get_daily_breakdown(self, date: str) -> List[Dict[str, Any]]:
        return [
            dict(row)
            for row in self.session.execute(
                text(
                    "SELECT payment_method, SUM(total_amount) as sum FROM sales WHERE DATE(created_at) = :date AND app_id = :app_id GROUP BY payment_method"
                ),
                {"date": date, "app_id": self.app_id},
            ).mappings()
        ]
