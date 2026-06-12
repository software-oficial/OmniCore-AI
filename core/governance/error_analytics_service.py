import logging
from typing import Dict, Any, Optional
from infra.db.core_db_manager import core_db_manager
from infra.cache.redis_manager import cache_manager
from sqlalchemy import text

logger = logging.getLogger("OmniCore.ErrorAnalytics")

class ErrorAnalyticsService:
    """
    Analyzes failures across all agents to identify common patterns.
    Implements the AI Intelligence Loop: Error $ightarrow$ Pattern $ightarrow$ KB $ightarrow$ Learning.
    """
    
    def __init__(self):
        self.error_threshold = 5 # Number of occurrences before promoting to KB

    def track_error(self, agent_id: str, command: str, error_code: str, message: str):
        """
        Tracks an error occurrence in Redis to detect patterns.
        If the error reaches the threshold, it is promoted to the CommonErrorKB.
        """
        # Use a Redis key to track frequency of this specific error pattern
        # pattern: cmd:error_code:message_snippet
        pattern_key = f"err_pattern:{command}:{error_code}:{message[:50]}"
        
        try:
            count = cache_manager.client.incr(pattern_key)
            cache_manager.client.expire(pattern_key, 604800) # 1 week window
            
            if count >= self.error_threshold:
                self._promote_to_kb(command, error_code, message)
                # Reset Redis counter after promotion to avoid spamming the KB
                cache_manager.client.delete(pattern_key)
        except Exception as e:
            logger.error(f"Error tracking failure pattern: {e}")

    def _promote_to_kb(self, command: str, error_code: str, message: str):
        """
        Promotes a frequent error to the CommonErrorKB for human review and AI guidance.
        """
        error_pattern = f"{command}|{error_code}"
        
        try:
            # Upsert into the common_errors_kb table
            query = text("""
                INSERT INTO common_errors_kb (error_pattern, solution_guide, occurrence_count, impact_level)
                VALUES (:pattern, 'PENDING_REVIEW: Please provide a guided solution for this common error.', :count, 'MEDIUM')
                ON CONFLICT(error_pattern) DO UPDATE SET 
                    occurrence_count = occurrence_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """)
            core_db_manager.execute_raw(query, {
                "pattern": error_pattern,
                "count": 1
            })
            logger.info(f"🚀 Pattern Promoted to KB: {error_pattern} (Triggered by high frequency)")
        except Exception as e:
            logger.error(f"Error promoting pattern to KB: {e}")

    def get_guided_solution(self, command: str, error_code: str) -> Optional[str]:
        """
        Retrieves a professional solution guide for a known common error.
        """
        error_pattern = f"{command}|{error_code}"
        try:
            result = core_db_manager.execute_raw(
                "SELECT solution_guide FROM common_errors_kb WHERE error_pattern = :pattern AND status = 'FIXED'", 
                {"pattern": error_pattern}
            ).scalar()
            return result
        except Exception as e:
            logger.error(f"Error retrieving guided solution: {e}")
            return None

# Singleton
error_analytics_service = ErrorAnalyticsService()
