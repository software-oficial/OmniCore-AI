import logging
import time
from typing import Any, Dict

from src.infrastructure.cache.redis_manager import cache_manager

logger = logging.getLogger("OmniCore.Telemetry")


class TelemetryService:
    """
    High-performance telemetry engine.
    Tracks real-time metrics, concurrency, and system health using Redis.
    """

    def __init__(self):
        self.METRIC_PREFIX = "telemetry:"
        self.WINDOW_SIZE = 3600  # 1 hour window for rolling metrics

    def track_request(
        self, agent_id: str, app_id: str, command: str, duration: float, success: bool
    ):
        """
        Logs a request event. Updates total counts, concurrency, and latency.
        """
        try:
            pipe = cache_manager.client.pipeline()

            # 1. Total Command Execution
            pipe.incr(f"{self.METRIC_PREFIX}total_requests")
            pipe.incr(f"{self.METRIC_PREFIX}commands:{command}")

            # 2. Success/Failure Rate
            status = "success" if success else "failure"
            pipe.incr(f"{self.METRIC_PREFIX}status:{status}")

            # 3. Latency Tracking (Using a Sorted Set for rolling window)
            timestamp = time.time()
            pipe.zadd(
                f"{self.METRIC_PREFIX}latency:{command}",
                {f"{timestamp}:{duration}": duration},
            )

            # 4. Real-time Agent Activity
            # Set agent as active for the next 60 seconds
            pipe.setex(f"{self.METRIC_PREFIX}active_agent:{agent_id}", 60, "active")
            pipe.setex(f"{self.METRIC_PREFIX}active_app:{app_id}", 60, "active")

            pipe.execute()
        except Exception as e:
            logger.warning(f"Telemetry tracking failed: {e}")

    def get_realtime_metrics(self) -> Dict[str, Any]:
        """
        Aggregates all current metrics for the Administrative Panel.
        """
        try:
            if not cache_manager.is_available():
                return {"error": "Telemetry unavailable (Redis offline)"}

            # Get active counts
            active_agents = len(
                cache_manager.client.keys(f"{self.METRIC_PREFIX}active_agent:*")
            )
            active_apps = len(
                cache_manager.client.keys(f"{self.METRIC_PREFIX}active_app:*")
            )

            # Get total requests
            total = int(
                cache_manager.client.get(f"{self.METRIC_PREFIX}total_requests") or 0
            )

            # Get command distribution
            command_keys = cache_manager.client.keys(f"{self.METRIC_PREFIX}commands:*")
            command_stats = {}
            for key in command_keys:
                cmd_name = key.split(":")[-1]
                command_stats[cmd_name] = int(cache_manager.client.get(key) or 0)

            return {
                "global": {
                    "total_requests": total,
                    "active_agents": active_agents,
                    "active_apps": active_apps,
                },
                "commands": command_stats,
                "status": {
                    "success": int(
                        cache_manager.client.get(f"{self.METRIC_PREFIX}status:success")
                        or 0
                    ),
                    "failure": int(
                        cache_manager.client.get(f"{self.METRIC_PREFIX}status:failure")
                        or 0
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error aggregating telemetry: {e}")
            return {"error": str(e)}


# Singleton
telemetry_service = TelemetryService()
