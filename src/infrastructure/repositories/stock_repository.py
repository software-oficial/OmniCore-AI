import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.repositories.base_repository import BaseRepository

logger = logging.getLogger("OmniCore.StockRepository")


class StockRepository(BaseRepository):
    """
    Infrastructure Layer: Encapsulates all SQL operations for the Stock domain.
    Ensures that the application layer remains agnostic of the database schema.
    """

    def __init__(self, session: Session):
        super().__init__(session)

    def get_sync_delta(self, since: str) -> List[Dict[str, Any]]:
        """Retrieves products updated after the specified timestamp."""
        return (
            self.session.execute(
                text("SELECT * FROM products WHERE updated_at > :since"),
                {"since": since},
            )
            .mappings()
            .all()
        )

    def upsert_product(
        self,
        code: str,
        name: str,
        price: float,
        quantity: int,
        category: Optional[str] = None,
        is_weight: bool = False,
    ) -> int:
        """Inserts a product or updates it if the code already exists. Returns the product ID."""
        query = text(
            """
            INSERT INTO products (app_id, code, name, price, quantity, category, is_weight) 
            VALUES (:app_id, :code, :name, :price, :quantity, :category, :is_weight) 
            ON CONFLICT(code) DO UPDATE SET 
                name=excluded.name, price=excluded.price, quantity=excluded.quantity, 
                category=excluded.category, is_weight=excluded.is_weight, updated_at=CURRENT_TIMESTAMP
            RETURNING id
            """
        )
        result = self.session.execute(
            query,
            {
                "app_id": self.app_id,
                "code": code,
                "name": name,
                "price": price,
                "quantity": quantity,
                "category": category,
                "is_weight": is_weight,
            },
        )
        return result.scalar()

    def get_product_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single product by its unique code."""
        return (
            self.session.execute(
                text("SELECT * FROM products WHERE code = :code"), {"code": code}
            )
            .mappings()
            .first()
        )

    def get_product_quantity_for_update(self, code: str) -> Optional[int]:
        """Locks the product row and returns the current quantity to prevent race conditions."""
        return self.session.execute(
            text("SELECT quantity FROM products WHERE code = :code FOR UPDATE"),
            {"code": code},
        ).scalar()

    def update_product_quantity(self, code: str, new_qty: int) -> None:
        """Updates the product quantity and timestamp."""
        self.session.execute(
            text(
                "UPDATE products SET quantity = :new_qty, updated_at = CURRENT_TIMESTAMP WHERE code = :code"
            ),
            {"new_qty": new_qty, "code": code},
        )

    def record_movement(
        self, code: str, amount: int, reason: str, user_id: str
    ) -> None:
        """Records a stock movement in the ledger."""
        self.session.execute(
            text(
                "INSERT INTO stock_movements (product_code, amount, reason, user_id) VALUES (:code, :amount, :reason, :user_id)"
            ),
            {
                "code": code,
                "amount": amount,
                "reason": reason,
                "user_id": user_id,
            },
        )

    def list_products(
        self, category: Optional[str] = None, filter_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lists products with optional filtering."""
        query_str = "SELECT * FROM products WHERE 1=1"
        params = {}

        if category:
            query_str += " AND category = :category"
            params["category"] = category

        if filter_text:
            query_str += " AND (name LIKE :filter OR code LIKE :filter)"
            params["filter"] = f"%{filter_text}%"

        return self.session.execute(text(query_str), params).mappings().all()

    def get_movement_history(self, code: str) -> List[Dict[str, Any]]:
        """Retrieves movement history for a specific product."""
        return (
            self.session.execute(
                text(
                    "SELECT * FROM stock_movements WHERE product_code = :code ORDER BY created_at DESC"
                ),
                {"code": code},
            )
            .mappings()
            .all()
        )

    def get_low_stock(self, threshold: float) -> List[Dict[str, Any]]:
        """Retrieves products below the critical threshold."""
        return (
            self.session.execute(
                text(
                    "SELECT * FROM products WHERE quantity < :threshold ORDER by quantity ASC"
                ),
                {"threshold": threshold},
            )
            .mappings()
            .all()
        )

    def delete_product(self, code: str) -> int:
        """Deletes a product. Returns the number of rows affected."""
        result = self.session.execute(
            text("DELETE FROM products WHERE code = :code"), {"code": code}
        )
        return result.rowcount
