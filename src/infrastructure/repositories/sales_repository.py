import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("OmniCore.SalesRepository")


class SalesRepository:
    """
    Infrastructure Layer: Encapsulates all SQL operations for the Sales domain.
    Ensures that the application layer remains agnostic of the database schema.
    """

    def __init__(self, session: Session):
        self.session = session

    # --- User & Permission Management ---
    def create_user(self, username: str, password: str) -> None:
        self.session.execute(
            text("INSERT INTO users (username, password) VALUES (:user, :pass)"),
            {"user": username, "pass": password},
        )

    def update_user_role(self, username: str, role: str) -> int:
        result = self.session.execute(
            text("UPDATE users SET role = :role WHERE username = :user"),
            {"role": role, "user": username},
        )
        return result.rowcount

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(
                text("SELECT id, username, role FROM users WHERE username = :u"),
                {"u": username},
            )
            .mappings()
            .first()
        )

    def grant_permission(self, user_id: int, permission_key: str) -> None:
        self.session.execute(
            text(
                "INSERT INTO user_permissions (user_id, permission_key) VALUES (:uid, :perm) ON CONFLICT DO NOTHING"
            ),
            {"uid": user_id, "perm": permission_key},
        )

    def revoke_permission(self, user_id: int, permission_key: str) -> None:
        self.session.execute(
            text(
                "DELETE FROM user_permissions WHERE user_id = :uid AND permission_key = :perm"
            ),
            {"uid": user_id, "perm": permission_key},
        )

    # --- Cash Box Management ---
    def open_cash_box(self, monto_inicial: float) -> int:
        result = self.session.execute(
            text(
                """
                UPDATE cash_box 
                SET abierta = true, efectivo_inicial = :monto, ventas_efectivo = 0, ventas_digital = 0, hora_apertura = CURRENT_TIMESTAMP 
                WHERE id = 1
            """
            ),
            {"monto": monto_inicial},
        )
        return result.rowcount

    def get_cash_box(self) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(text("SELECT * FROM cash_box WHERE id = 1"))
            .mappings()
            .first()
        )

    def close_cash_box(self, monto_real: float) -> None:
        self.session.execute(
            text(
                """
                UPDATE cash_box 
                SET abierta = false, hora_cierre = CURRENT_TIMESTAMP, monto_cierre_real = :real 
                WHERE id = 1
            """
            ),
            {"real": monto_real},
        )

    def update_cash_box_totals(self, amount: float, is_digital: bool) -> None:
        column = "ventas_digital" if is_digital else "ventas_efectivo"
        self.session.execute(
            text(f"UPDATE cash_box SET {column} = {column} + :total WHERE id = 1"),
            {"total": amount},
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
                INSERT INTO sales (client_name, total_amount, status, payment_method, paga_con, vuelto) 
                VALUES (:name, :total, :status, :method, :paga_con, :vuelto) 
                RETURNING id
            """
            ),
            {
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
                INSERT INTO sale_items (sale_id, product_code, quantity, unit_price, subtotal) 
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
                text("SELECT * FROM sales WHERE id = :id"), {"id": sale_id}
            )
            .mappings()
            .first()
        )

    def update_sale_status(self, sale_id: int, status: str) -> None:
        self.session.execute(
            text("UPDATE sales SET status = :status WHERE id = :id"),
            {"status": status, "id": sale_id},
        )

    def get_sale_items(self, sale_id: int) -> List[Dict[str, Any]]:
        return (
            self.session.execute(
                text(
                    "SELECT product_code, quantity FROM sale_items WHERE sale_id = :id"
                ),
                {"id": sale_id},
            )
            .mappings()
            .all()
        )

    # --- Alias Management ---
    def add_alias(self, alias_id: str, nombre: str, limite: float) -> None:
        self.session.execute(
            text(
                "INSERT INTO aliases (id, nombre, limite, acumulado) VALUES (:id, :nombre, :limite, 0)"
            ),
            {"id": alias_id, "nombre": nombre, "limite": limite},
        )

    def get_alias_by_name(self, nombre: str) -> Optional[Dict[str, Any]]:
        return (
            self.session.execute(
                text("SELECT * FROM aliases WHERE nombre = :nombre"), {"nombre": nombre}
            )
            .mappings()
            .first()
        )

    def update_alias_accumulation(self, nombre: str, amount: float) -> None:
        self.session.execute(
            text(
                "UPDATE aliases SET acumulado = acumulado + :total WHERE nombre = :nombre"
            ),
            {"total": amount, "nombre": nombre},
        )

    def list_all_aliases(self) -> List[Dict[str, Any]]:
        return self.session.execute(text("SELECT * FROM aliases")).mappings().all()

    def delete_alias(self, alias_id: str) -> None:
        self.session.execute(
            text("DELETE FROM aliases WHERE id = :id"), {"id": alias_id}
        )

    # --- Reports ---
    def get_daily_totals(self, date: str) -> float:
        res = self.session.execute(
            text(
                "SELECT SUM(total_amount) as total FROM sales WHERE DATE(created_at) = :date"
            ),
            {"date": date},
        ).scalar()
        return float(res or 0)

    def get_daily_breakdown(self, date: str) -> List[Dict[str, Any]]:
        return (
            self.session.execute(
                text(
                    "SELECT payment_method, SUM(total_amount) as sum FROM sales WHERE DATE(created_at) = :date GROUP BY payment_method"
                ),
                {"date": date},
            )
            .mappings()
            .all()
        )
