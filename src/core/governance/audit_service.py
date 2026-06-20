import logging
from typing import Any, Dict, Optional

from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.AuditService")


class AuditService:
    """
    Application Layer: Handles persistent audit logging of all critical system actions.
    Ensures that every command execution is recorded for security and compliance.
    """

    def __init__(self):
        pass

    def log_event(
        self,
        agent_id: str,
        app_id: str,
        command: str,
        status: str,
        message: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Records a command execution event in the core audit table.
        """
        try:
            # Using core_db_manager for internal registry persistence
            audit_query = """
                INSERT INTO system_audit_log 
                (agent_id, app_id, command, status, message, params, timestamp) 
                VALUES (:agent_id, :app_id, :command, :status, :message, :params, CURRENT_TIMESTAMP)
            """
            import json

            core_db_manager.execute_raw(
                audit_query,
                {
                    "agent_id": agent_id,
                    "app_id": app_id,
                    "command": command,
                    "status": status,
                    "message": message[:500],
                    "params": json.dumps(params) if params else None,
                },
            )
        except Exception as e:
            # We log the failure to the file system but don't crash the main request
            logger.error(f"Critical Audit Log failure: {e}")


# Singleton
audit_service = AuditService()
