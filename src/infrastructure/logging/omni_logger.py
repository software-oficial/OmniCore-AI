import logging
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.LoggerSystem")

class OmniLogger:
    """
    Asynchronous Structured Logging System for OmniCore-AI.
    Buffers logs in an internal queue to prevent database latency from blocking the API.
    """
    
    CATEGORIES = {
        "SECURITY": "LOG_SECURITY",
        "INFRA": "LOG_INFRA",
        "BUSINESS": "LOG_BUSINESS",
        "LEARNING": "LOG_AI_LEARNING",
        "SYSTEM": "LOG_SYSTEM"
    }

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
        # Internal buffer for asynchronous processing
        self.queue = asyncio.Queue()

    def _format_log(self, level: str, category: str, message: str, 
                    app_id: Optional[str] = None, agent_id: Optional[str] = None, 
                    trace_id: Optional[str] = None, payload: Optional[Dict] = None) -> Dict:
        """Formats the log entry as a dictionary."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "category": category,
            "logger": self.name,
            "message": message,
            "context": {
                "app_id": app_id,
                "agent_id": agent_id,
                "trace_id": trace_id
            },
            "payload": payload or {}
        }

    def _emit(self, level: str, category: str, message: str, **kwargs):
        """Pushes the log to the async queue instead of writing to DB synchronously."""
        log_entry = self._format_log(level, category, message, **kwargs)
        
        # 1. Immediate Standard Output (for container logs)
        formatted_msg = json.dumps(log_entry)
        if level == "INFO": self.logger.info(formatted_msg)
        elif level == "WARNING": self.logger.warning(formatted_msg)
        elif level == "ERROR": self.logger.error(formatted_msg)
        elif level == "CRITICAL": self.logger.critical(formatted_msg)
        else: self.logger.debug(formatted_msg)

        # 2. Buffer for DB persistence
        try:
            # Use a thread-safe way to put into asyncio queue if called from sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self.queue.put_nowait, log_entry)
        except Exception as e:
            print(f"CRITICAL: Failed to queue log: {e}")

    async def process_logs(self):
        """Background worker that persists queued logs to the Core DB."""
        logger.info("🚀 Async Log Worker started. Processing logs in background...")
        while True:
            try:
                log_entry = await self.queue.get()
                
                # Persist to Hot Store (Core DB)
                core_db_manager.execute_raw(
                    "INSERT INTO system_logs (level, category, message, app_id, agent_id, payload) VALUES (:level, :cat, :msg, :app, :agent, :pay)",
                    {
                        "level": log_entry["level"],
                        "cat": log_entry["category"],
                        "msg": log_entry["message"],
                        "app": log_entry["context"].get("app_id"),
                        "agent": log_entry["context"].get("agent_id"),
                        "pay": json.dumps(log_entry["payload"])
                    }
                )
                self.queue.task_done()
            except Exception as e:
                print(f"CRITICAL: Async log persistence failed: {e}")
                await asyncio.sleep(1) # Avoid tight loop on DB failure

    def info(self, category: str, message: str, **kwargs):
        self._emit("INFO", category, message, **kwargs)

    def warning(self, category: str, message: str, **kwargs):
        self._emit("WARNING", category, message, **kwargs)

    def error(self, category: str, message: str, **kwargs):
        self._emit("ERROR", category, message, **kwargs)

    def critical(self, category: str, message: str, **kwargs):
        self._emit("CRITICAL", category, message, **kwargs)

    def debug(self, category: str, message: str, **kwargs):
        self._emit("DEBUG", category, message, **kwargs)

# Helper to create loggers easily
def get_logger(name: str) -> OmniLogger:
    return OmniLogger(name)
