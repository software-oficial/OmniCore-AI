import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.AuditService")


class AuditService:
    """
    Domain Layer: Exposes the system audit log as a queryable command.
    Allows business owners to track all actions performed by their employees and agents.
    """

    @command(
        name="system.audit.get_logs",
        description="Retrieves the audit trail for a specific business application.",
        params_model={"limit": "integer", "offset": "integer", "command": "string"},
    )
    def get_logs(
        self,
        session: Session,
        context: CoreContext,
        limit: int = 50,
        offset: int = 0,
        command: Optional[str] = None,
    ) -> ServiceResponse:
        """
        Queries the core internal audit log filtered by app_id.
        """
        try:
            # We use core_db_manager because the audit log lives in the internal registry, not business DB
            query = "SELECT id, agent_id, command, status, message, timestamp FROM system_audit_log WHERE app_id = :app_id"
            params: Dict[str, Any] = {"app_id": context.app_id}

            if command:
                query += " AND command = :command"
                params["command"] = command

            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            results = core_db_manager.execute_raw(query, params).mappings().all()

            return ServiceResponse.success_res(
                data=[dict(row) for row in results],
                message="Audit logs retrieved successfully.",
            )
        except Exception as e:
            logger.error(f"Error retrieving audit logs for app {context.app_id}: {e}")
            return ServiceResponse.error_res(
                f"Error fetching audit trail: {str(e)}", "AUDIT_GET_ERROR"
            )


# Singleton
audit_service = AuditService()
