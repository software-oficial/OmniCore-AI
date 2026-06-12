import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized system configuration."""
    # API Settings
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")
    VERSION = "2.0.0-Enterprise"
    
    # Internal Registry DB
    INTERNAL_DB_URL = os.getenv("OMNICORE_INTERNAL_DB_URL", "sqlite:///omnicore_registry.db")
    
    # Redis Cache
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    
    # System Limits
    POOL_CLEANUP_INTERVAL = 900 # 15 minutes
    ERROR_PROMOTION_THRESHOLD = 5

config = Config()
