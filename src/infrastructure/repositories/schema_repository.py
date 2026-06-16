import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("OmniCore.SchemaRepository")


class SchemaRepository:
    """
    Infrastructure Layer: Direct access to the database for schema operations.
    Follows the Repository Pattern to isolate SQL execution from business logic.
    """

    def __init__(self, session: Session):
        self.session = session

    def execute_blueprint(self, sql: str) -> None:
        """Executes a raw SQL blueprint on the provided session."""
        try:
            self.session.execute(text(sql))
        except Exception as e:
            logger.error(f"SQL Execution Error during blueprint deployment: {e}")
            raise e

    def validate_table_exists(self, table_name: str) -> bool:
        """Checks if a specific table exists in the current database."""
        try:
            self.session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
            return True
        except Exception:
            return False
