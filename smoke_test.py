import logging
import sys

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SmokeTest")

def test_initialization():
    logger.info("🚀 Starting Smoke Test: System Initialization...")
    try:
        # Test 1: Core DB Manager
        logger.info("Testing CoreDbManager...")
        from infra.db.core_db_manager import core_db_manager
        logger.info("✅ CoreDbManager imported and initialized.")

        # Test 2: Redis Manager
        logger.info("Testing RedisManager...")
        from infra.cache.redis_manager import cache_manager
        logger.info("✅ RedisManager imported and initialized.")

        # Test 3: API Main
        logger.info("Testing API Main import...")
        import api.main
        logger.info("✅ API Main imported successfully.")

        logger.info("🎉 ALL SMOKE TESTS PASSED!")
        return True
    except Exception as e:
        logger.error(f"❌ SMOKE TEST FAILED: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_initialization()
    sys.exit(0 if success else 1)
