import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional
from infra.db.core_db_manager import core_db_manager

class OmniLogger:
    """
    Structured Logging System for OmniCore-AI.
    Produces JSON logs categorized by flow, facilitating migration to 
    centralized log servers (ELK, MongoDB, etc.).
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

    def _format_log(self, level: str, category: str, message: str, 
                    app_id: Optional[str] = None, agent_id: Optional[str] = None, 
                    trace_id: Optional[str] = None, payload: Optional[Dict] = None) -> str:
        """Formats the log entry as a JSON string."""
        log_entry = {
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
        return json.dumps(log_entry)

    def _emit(self, level: str, category: str, message: str, **kwargs):
        """Emits the log to the standard logger and persists to the Hot Store (Core DB)."""
        formatted_msg = self._format_log(level, category, message, **kwargs)
        
        # 1. Standard Output (for Railway/Docker logs)
        if level == "INFO": self.logger.info(formatted_msg)
        elif level == "WARNING": self.logger.warning(formatted_msg)
        elif level == "ERROR": self.logger.error(formatted_msg)
        elif level == "CRITICAL": self.logger.critical(formatted_msg)
        else: self.logger.debug(formatted_msg)

        # 2. Hot Storage (Core DB) - Persist system logs
        try:
            core_db_manager.execute_raw(
                "INSERT INTO system_logs (level, category, message, app_id, agent_id, payload) VALUES (:level, :cat, :msg, :app, :agent, :pay)",
                {
                    "level": level,
                    "cat": category,
                    "msg": message,
                    "app": kwargs.get("app_id"),
                    "agent": kwargs.get("agent_id"),
                    "pay": json.dumps(kwargs.get("payload")) if kwargs.get("payload") else None
                }
            )
        except Exception as e:
            # Avoid infinite recursion if DB logging fails
            print(f"CRITICAL: Logging to Core DB failed: {e}")

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
