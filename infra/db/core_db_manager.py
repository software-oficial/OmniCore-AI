import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()
logger = logging.getLogger("OmniCore.CoreDbManager")

class CoreDbManager:
    """
    Manages the internal database for OmniCore-AI.
    Uses SQLite by default for the registry to ensure zero-config setup.
    """
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialize_engine()
        # Auto-Doctor: Ensure schema is present on startup
        self.init_schema()

    def _initialize_engine(self):
        db_url = os.getenv("OMNICORE_INTERNAL_DB_URL")
        if not db_url:
            logger.info("Using local SQLite for internal registry.")
            db_url = "sqlite:///omnicore_registry.db"
        
        try:
            self.engine = create_engine(db_url, pool_pre_ping=True)
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info(f"Internal Core DB initialized at: {db_url}")
        except Exception as e:
            logger.critical(f"Failed to initialize internal Core DB: {e}")
            raise ConnectionError(f"Core DB connection failed: {e}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provides a session for interacting with the internal registry."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def execute_raw(self, query: str, params: dict = None):
        """Executes a raw SQL query on the internal DB."""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result

    def init_schema(self):
        """
        Initializes the core registry schema by loading the base SQL migration file.
        This ensures consistency across environments.
        """
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "infra/db/migrations/001_initial_schema.sql")
        try:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            
            # Execute statements sequentially for compatibility
            for statement in schema_sql.strip().split(';'):
                if statement.strip():
                    self.execute_raw(statement)
            
            logger.info(f"Internal Core DB schema initialized from {schema_path}.")
        except FileNotFoundError:
            logger.critical(f"SCHEMA ERROR: Migration file not found at {schema_path}. Core DB cannot initialize.")
            raise RuntimeError(f"Missing critical migration file: {schema_path}")
        except Exception as e:
            logger.error(f"Error initializing Core DB schema: {e}")
            raise e

# Singleton for global access
core_db_manager = CoreDbManager()
