import logging
from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import asyncio
import time
from contextlib import asynccontextmanager
from core.dispatcher.exceptions import InfrastructureException

logger = logging.getLogger("OmniCore.DbPool")

class DynamicDbManager:
    """
    Dynamic Database Manager for OmniCore-AI.
    
    Implements a Circuit Breaker pattern and Global Concurrency Control
    to prevent cascading failures and DB saturation.
    """
    def __init__(self):
        self._engines: Dict[str, Any] = {}
        self._session_factories: Dict[str, Any] = {}
        self._last_accessed: Dict[str, float] = {}
        
        # Circuit Breaker State
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.FAILURE_THRESHOLD = 3
        self.RECOVERY_TIMEOUT = 60 

        # Global Concurrency Control (SRE Layer)
        self.GLOBAL_MAX_CONCURRENCY = 100 
        self._semaphore = asyncio.Semaphore(self.GLOBAL_MAX_CONCURRENCY)

    def _create_engine(self, db_config: Dict[str, Any], pool_size: int = 5, max_overflow: int = 10):
        url = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        
        # Log the connection string (masking password for security)
        masked_url = url.replace(db_config['password'], "********")
        logger.info(f"🔧 Creating DB Engine: {masked_url}")
        
        return create_engine(
            url, 
            poolclass=QueuePool, 
            pool_size=pool_size, 
            max_overflow=max_overflow,
            pool_recycle=3600
        )

    def report_failure(self, app_id: str):
        if app_id not in self._circuit_breakers:
            self._circuit_breakers[app_id] = {"failures": 0, "last_failure": 0, "status": "CLOSED"}
        
        state = self._circuit_breakers[app_id]
        state["failures"] += 1
        state["last_failure"] = time.time()
        
        if state["failures"] >= self.FAILURE_THRESHOLD:
            logger.error(f"🚨 Circuit OPENED for App {app_id} due to repeated failures.")
            state["status"] = "OPEN"

    def _check_circuit(self, app_id: str):
        if app_id not in self._circuit_breakers:
            return

        state = self._circuit_breakers[app_id]
        if state["status"] == "OPEN":
            if time.time() - state["last_failure"] > self.RECOVERY_TIMEOUT:
                logger.info(f"🌓 Circuit HALF-OPEN for App {app_id}. Testing connection...")
                return
            
            raise InfrastructureException(
                message=f"Connection to business database is temporarily suspended. Please try again in a few minutes.",
                error_code="CIRCUIT_OPEN"
            )

    @asynccontextmanager
    async def get_session(self, app_id: str, db_config: Dict[str, Any], tier: str = "FREE") -> AsyncGenerator[Session, None]:
        """
        Injects a database session with Global Concurrency Control and Circuit Breaker protection.
        """
        async with self._semaphore:
            self._check_circuit(app_id)

            # Dynamic Pool Sizing based on Tier
            pool_settings = {
                "FREE": {"size": 5, "overflow": 10},
                "PRO": {"size": 15, "overflow": 20},
                "ENTERPRISE": {"size": 30, "overflow": 50}
            }.get(tier.upper(), {"size": 5, "overflow": 10})

            if app_id not in self._engines:
                try:
                    logger.info(f"Initializing new DB pool for App {app_id} [Tier: {tier}]")
                    self._engines[app_id] = self._create_engine(
                        db_config, 
                        pool_size=pool_settings["size"], 
                        max_overflow=pool_settings["overflow"]
                    )
                    self._session_factories[app_id] = sessionmaker(bind=self._engines[app_id])
                except Exception as e:
                    self.report_failure(app_id)
                    raise InfrastructureException(f"Could not initialize DB pool: {str(e)}", "DB_INIT_FAILED")

            self._last_accessed[app_id] = time.time()
            
            session = self._session_factories[app_id]()
            try:
                yield session
                if app_id in self._circuit_breakers and self._circuit_breakers[app_id]["status"] != "CLOSED":
                    logger.info(f"✅ Circuit CLOSED for App {app_id}. Connection restored.")
                    self._circuit_breakers[app_id] = {"failures": 0, "last_failure": 0, "status": "CLOSED"}
            except Exception as e:
                self.report_failure(app_id)
                raise e
            finally:
                session.close()

    def evict_idle_pools(self, max_idle_seconds: int = 1800):
        now = time.time()
        to_evict = [
            app_id for app_id, last_time in self._last_accessed.items() 
            if now - last_time > max_idle_seconds
        ]

        for app_id in to_evict:
            logger.info(f"Evicting idle DB pool for App: {app_id}")
            if app_id in self._engines:
                self._engines[app_id].dispose()
                del self._engines[app_id]
            if app_id in self._session_factories:
                del self._session_factories[app_id]
            del self._last_accessed[app_id]
            
        if to_evict:
            logger.info(f"Pool Eviction Complete. Removed {len(to_evict)} idle pools.")

    def close_all_pools(self):
        for engine in self._engines.values():
            engine.dispose()
        self._engines.clear()
        self._session_factories.clear()
        self._last_accessed.clear()

# Singleton for global access
db_manager = DynamicDbManager()
