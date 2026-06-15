import logging
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import ServiceResponse

logger = logging.getLogger("OmniCore.SchemaValidator")


class SchemaValidator:
    """
    Ensures the external business database has the required tables
    before a module execution. This prevents raw SQL errors and
    guides the AI to run the necessary blueprints.
    """

    @staticmethod
    def validate_module_schema(
        session: Session, module_name: str, required_tables: List[str]
    ) -> Tuple[bool, Optional[ServiceResponse]]:
        """
        Checks if all required tables for a module exist in the current session's DB.
        """
        try:
            # Query the information_schema to check for table existence (Postgres compatible)
            # Note: If using SQLite for local tests, this query would change.
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = :table
            """)

            for table in required_tables:
                result = session.execute(query, {"table": table}).scalar()
                if not result:
                    logger.warning(
                        f"Missing required table {table} for module {module_name}"
                    )
                    return False, ServiceResponse.error_res(
                        message=f"The required table '{table}' is missing in your database. Please run the blueprint for module '{module_name}'.",
                        error_code="SCHEMA_OUTDATED",
                    )

            return True, None
        except Exception as e:
            logger.error(f"Error validating schema for {module_name}: {e}")
            # We return True here to avoid blocking execution on a validator failure,
            # but in a strict mode, this would be False.
            return True, None


# Singleton
schema_validator = SchemaValidator()
