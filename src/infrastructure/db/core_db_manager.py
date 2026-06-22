import logging
import os
from contextlib import contextmanager
from typing import Any, Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

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

    def execute_raw(self, query: Any, params: Optional[dict] = None):
        """Executes a query on the internal DB. Accepts string or SQLAlchemy text object."""
        with self.get_session() as session:
            if isinstance(query, str):
                query = text(query)
            result = session.execute(query, params or {})
            return result

    SCHEMA_SQL = """
        -- 1. Empresas / Negocios
        CREATE TABLE IF NOT EXISTS businesses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_id TEXT, 
            plan TEXT DEFAULT 'FREE',
            settings TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 2. Usuarios y Personal
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            business_id TEXT REFERENCES businesses(id),
            role TEXT DEFAULT 'EMPLOYEE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 3. Stock Flexible (Universal Schema)
        CREATE TABLE IF NOT EXISTS stock (
            id SERIAL PRIMARY KEY,
            business_id TEXT REFERENCES businesses(id),
            sku TEXT NOT NULL,
            data TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(business_id, sku)
        );

        -- 4. Credenciales Dinámicas (APIs Externas)
        CREATE TABLE IF NOT EXISTS credentials (
            id SERIAL PRIMARY KEY,
            business_id TEXT REFERENCES businesses(id),
            provider TEXT NOT NULL,
            data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 5. Registro de Ventas Unificado
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            business_id TEXT REFERENCES businesses(id),
            client_name TEXT,
            total_amount REAL,
            data TEXT DEFAULT '{}', -- Detalles de items y pagos en JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 5.5 Caja
        CREATE TABLE IF NOT EXISTS cash_box (
            id SERIAL PRIMARY KEY,
            app_id TEXT REFERENCES businesses(id),
            abierta BOOLEAN DEFAULT false,
            efectivo_inicial REAL DEFAULT 0,
            ventas_efectivo REAL DEFAULT 0,
            ventas_digital REAL DEFAULT 0,
            hora_apertura TIMESTAMP,
            hora_cierre TIMESTAMP
        );


        -- 6. Gobernanza y Auditoría
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
            user_id TEXT,
            business_id TEXT,
            command TEXT,
            status TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    def init_schema(self):
        """
        Initializes the core registry schema using the embedded SQL.
        This guarantees availability regardless of deployment path.
        """
        try:
            # Execute statements sequentially for compatibility
            for statement in self.SCHEMA_SQL.strip().split(";"):
                if statement.strip():
                    self.execute_raw(statement)

            logger.info("Internal Core DB schema initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Core DB schema: {e}")
            raise e


# Singleton for global access
core_db_manager = CoreDbManager()
