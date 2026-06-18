import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("OmniCore.UserRepository")


class UserRepository:
    """
    Infrastructure Layer: Encapsulates all SQL operations for User and Permission management.
    Ensures that the application layer remains agnostic of the database schema.
    """

    def __init__(self, session: Session):
        self.session = session

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

    def list_users(self) -> List[Dict[str, Any]]:
        """
        Retrieves all users with their current roles.
        """
        return (
            self.session.execute(text("SELECT id, username, role FROM users"))
            .mappings()
            .all()
        )

    def get_user_permissions(self, user_id: int) -> List[str]:
        """
        Retrieves all permission keys assigned to a user.
        """
        results = self.session.execute(
            text("SELECT permission_key FROM user_permissions WHERE user_id = :uid"),
            {"uid": user_id},
        )
        return [row[0] for row in results]
