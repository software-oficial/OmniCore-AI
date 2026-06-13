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
        """Initializes the core registry schema with PostgreSQL compatibility."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            api_key VARCHAR(255) UNIQUE NOT NULL,
            owner_user_id TEXT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS api_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT REFERENCES users(id),
            agent_id TEXT,
            token_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS apps (
            id TEXT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            owner_id TEXT REFERENCES agents(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS app_infrastructure (
            app_id TEXT PRIMARY KEY REFERENCES apps(id),
            db_host VARCHAR(255) NOT NULL,
            db_port INTEGER NOT NULL,
            db_user VARCHAR(255) NOT NULL,
            db_password TEXT NOT NULL,
            db_name VARCHAR(255) NOT NULL,
            tier VARCHAR(50) DEFAULT 'FREE'
        );

        CREATE TABLE IF NOT EXISTS agent_app_mapping (
            agent_id TEXT REFERENCES agents(id),
            app_id TEXT REFERENCES apps(id),
            PRIMARY KEY (agent_id, app_id)
        );

        CREATE TABLE IF NOT EXISTS governance_tiers (
            tier_name TEXT PRIMARY KEY,
            level INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS governance_commands (
            command_name TEXT PRIMARY KEY,
            permission_key TEXT,
            min_tier TEXT REFERENCES governance_tiers(tier_name)
        );

        CREATE TABLE IF NOT EXISTS system_audit_log (
            id SERIAL PRIMARY KEY,
            agent_id TEXT,
            app_id TEXT,
            command TEXT,
            status TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS common_errors_kb (
            id SERIAL PRIMARY KEY,
            error_pattern TEXT UNIQUE,
            solution_guide TEXT,
            occurrence_count INTEGER DEFAULT 1,
            impact_level TEXT DEFAULT 'LOW',
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            level TEXT,
            category TEXT,
            message TEXT,
            app_id TEXT,
            agent_id TEXT,
            payload TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            # PostgreSQL allows executing multiple statements in one call via some drivers, 
            # but we keep the split for safety and SQLite compatibility.
            for statement in schema_sql.strip().split(';'):
                if statement.strip():
                    self.execute_raw(statement)
            logger.info("Internal Core DB schema initialized successfully (PostgreSQL).")
        except Exception as e:
            logger.error(f"Error initializing Core DB schema: {e}")
            raise e

# Singleton for global access
core_db_manager = CoreDbManager()
