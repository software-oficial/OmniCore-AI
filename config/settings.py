import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class Config:
    """Centralized system configuration."""
    # API Settings
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")
    VERSION = "2.0.0-Enterprise"
    
    # Internal Registry DB
    INTERNAL_DB_URL = os.getenv("OMNICORE_INTERNAL_DB_URL", "sqlite:///omnicore_registry.db")
    
    # Parse DB URL for easy access to components
    try:
        parsed = urlparse(INTERNAL_DB_URL)
        DB_HOST = parsed.hostname or "localhost"
        DB_PORT = parsed.port or (5432 if "postgresql" in INTERNAL_DB_URL else 0)
        DB_USER = parsed.username or "postgres"
        DB_PASSWORD = parsed.password or ""
        DB_NAME = parsed.path.lstrip('/') or "omnicore_registry"
    except Exception:
        DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME = "localhost", 5432, "postgres", "", "omnicore_registry"
    
    # Redis Cache
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_HOST = os.getenv("REDIS_HOST") or os.getenv("REDISHOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT") or os.getenv("REDISPORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or os.getenv("REDISPASSWORD")
    
    # System Limits
    POOL_CLEANUP_INTERVAL = 900 # 15 minutes
    ERROR_PROMOTION_THRESHOLD = 5
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-prod")


config = Config()
