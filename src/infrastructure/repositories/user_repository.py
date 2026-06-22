import logging
from typing import Any, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.repositories.base_repository import BaseRepository

logger = logging.getLogger("OmniCore.UserRepository")


class UserRepository(BaseRepository):
    """
    Infrastructure Layer: Encapsulates all SQL operations for User and Permission management.
    Ensures that the application layer remains agnostic of the database schema.
    """

    def __init__(self, session: Session, business_id: str):
        super().__init__(session, business_id)

    def create_user(
        self,
        email: str,
        password_hash: str,
        role: str = "owner",
    ) -> str:
        result = self.session.execute(
            text(
                "INSERT INTO users (id, email, password_hash, app_id, role) VALUES (gen_random_uuid(), :email, :password_hash, :app_id, :role) RETURNING id"
            ),
            {
                "email": email,
                "password_hash": password_hash,
                "app_id": self.app_id,
                "role": role,
            },
        )
        return str(result.scalar())

    def update_user_role(self, email: str, role: str) -> int:
        result = self.session.execute(
            text(
                "UPDATE users SET role = :role WHERE email = :email AND app_id = :app_id"
            ),
            {"role": role, "email": email, "app_id": self.app_id},
        )
        return int(result.rowcount)

    def get_user_by_username(self, email: str) -> dict[str, Any] | None:
        row = (
            self.session.execute(
                text(
                    "SELECT id, email, role FROM users WHERE email = :email AND app_id = :app_id"
                ),
                {"email": email, "app_id": self.app_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def grant_permission(self, user_id: str, permission_key: str) -> None:
        # Note: user_id is likely UUID string based on gen_random_uuid()
        self.session.execute(
            text(
                "INSERT INTO user_permissions (user_id, permission_key) VALUES (:uid, :perm) ON CONFLICT DO NOTHING"
            ),
            {"uid": user_id, "perm": permission_key},
        )

    def revoke_permission(self, user_id: str, permission_key: str) -> None:
        self.session.execute(
            text(
                "DELETE FROM user_permissions WHERE user_id = :uid AND permission_key = :perm"
            ),
            {"uid": user_id, "perm": permission_key},
        )

    def list_users(self) -> list[dict[str, Any]]:
        """
        Retrieves all users with their current roles.
        """
        return [
            dict(row)
            for row in self.session.execute(
                text("SELECT id, email, role FROM users WHERE app_id = :app_id"),
                {"app_id": self.app_id},
            ).mappings()
        ]

    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Retrieves all permission keys assigned to a user.
        """
        # This assumes user_permissions is tied to user_id, no explicit app_id check needed if user_id is unique
        results = self.session.execute(
            text("SELECT permission_key FROM user_permissions WHERE user_id = :uid"),
            {"uid": user_id},
        )
        return [row[0] for row in results]
