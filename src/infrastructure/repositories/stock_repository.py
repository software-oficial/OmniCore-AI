import logging
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.repositories.base_repository import BaseRepository

logger = logging.getLogger("OmniCore.StockRepository")


class StockRepository(BaseRepository):
    """
    Infrastructure Layer: Encapsulates all SQL operations for the Stock domain.
    Ensures that the application layer remains agnostic of the database schema.
    """

    def __init__(self, session: Session, business_id: str):
        super().__init__(session, business_id)

    def get_sync_delta(self, since: str) -> list[dict[str, Any]]:
        """Retrieves products updated after the specified timestamp."""
        return [
            dict(row)
            for row in self.session.execute(
                text(
                    "SELECT * FROM products WHERE updated_at > :since AND app_id = :app_id"
                ),
                {"since": since, "app_id": self.app_id},
            ).mappings()
        ]

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
            ON CONFLICT(app_id, code) DO UPDATE SET 
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
        return int(result.scalar())

    def get_product_by_code(self, code: str) -> dict[str, Any] | None:
        """Retrieves a single product by its unique code."""
        row = (
            self.session.execute(
                text("SELECT * FROM products WHERE code = :code AND app_id = :app_id"),
                {"code": code, "app_id": self.app_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def get_product_quantity_for_update(self, code: str) -> Optional[int]:
        """Locks the product row and returns the current quantity to prevent race conditions."""
        res = self.session.execute(
            text(
                "SELECT quantity FROM products WHERE code = :code AND app_id = :app_id FOR UPDATE"
            ),
            {"code": code, "app_id": self.app_id},
        ).scalar()
        return int(res) if res is not None else None

    def update_product_quantity(self, code: str, new_qty: int) -> None:
        """Updates the product quantity and timestamp."""
        self.session.execute(
            text(
                "UPDATE products SET quantity = :new_qty, updated_at = CURRENT_TIMESTAMP WHERE code = :code AND app_id = :app_id"
            ),
            {"new_qty": new_qty, "code": code, "app_id": self.app_id},
        )

    def record_movement(
        self, code: str, amount: int, reason: str, user_id: str
    ) -> None:
        """Records a stock movement in the ledger."""
        self.session.execute(
            text(
                "INSERT INTO stock_movements (app_id, product_code, amount, reason, user_id) VALUES (:app_id, :code, :amount, :reason, :user_id)"
            ),
            {
                "app_id": self.app_id,
                "code": code,
                "amount": amount,
                "reason": reason,
                "user_id": user_id,
            },
        )

    def list_products(
        self, category: Optional[str] = None, filter_text: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Lists products with optional filtering."""
        query_str = "SELECT * FROM products WHERE app_id = :app_id"
        params = {"app_id": self.app_id}

        if category:
            query_str += " AND category = :category"
            params["category"] = category

        if filter_text:
            query_str += " AND (name LIKE :filter OR code LIKE :filter)"
            params["filter"] = f"%{filter_text}%"

        return [
            dict(row)
            for row in self.session.execute(text(query_str), params).mappings()
        ]

    def get_movement_history(self, code: str) -> list[dict[str, Any]]:
        """Retrieves movement history for a specific product."""
        # Assuming stock_movements also has app_id, if not it should be added.
        # Based on the prompt UUS schema requirement, it should be added.
        return [
            dict(row)
            for row in self.session.execute(
                text(
                    "SELECT * FROM stock_movements WHERE product_code = :code AND app_id = :app_id ORDER BY created_at DESC"
                ),
                {"code": code, "app_id": self.app_id},
            ).mappings()
        ]

    def get_low_stock(self, threshold: float) -> list[dict[str, Any]]:
        """Retrieves products below the critical threshold."""
        return [
            dict(row)
            for row in self.session.execute(
                text(
                    "SELECT * FROM products WHERE quantity < :threshold AND app_id = :app_id ORDER by quantity ASC"
                ),
                {"threshold": threshold, "app_id": self.app_id},
            ).mappings()
        ]

    def delete_product(self, code: str) -> int:
        """Deletes a product. Returns the number of rows affected."""
        result = self.session.execute(
            text("DELETE FROM products WHERE code = :code AND app_id = :app_id"),
            {"code": code, "app_id": self.app_id},
        )
        return int(result.rowcount)
