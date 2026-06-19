import logging
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command

logger = logging.getLogger("OmniCore.CredentialService")


class CredentialService:
    """
    Domain Layer: Manages the lifecycle of service credentials.
    Enables Multi-Instance architecture by allowing multiple provider accounts per user.
    """

    @command(
        name="system.credentials.list",
        description="Lists all service credentials for the current user/business.",
        params_model={"service_type": "string"},
    )
    def list_credentials(
        self, session: Session, context: CoreContext, service_type: Optional[str] = None
    ) -> ServiceResponse:
        """Retrieves active credentials, optionally filtered by type."""
        try:
            query = "SELECT id, user_id, service_type, provider_id, config, label, is_active FROM service_credentials WHERE user_id = :uid"
            params = {"uid": context.user_id}

            if service_type:
                query += " AND service_type = :stype"
                params["stype"] = service_type

            result = session.execute(text(query), params).mappings().all()
            return ServiceResponse.success_res(
                data=[dict(row) for row in result], message="Credentials retrieved."
            )
        except Exception as e:
            logger.error(f"Error listing credentials for {context.user_id}: {e}")
            return ServiceResponse.error_res(
                f"Failed to retrieve credentials: {str(e)}", "CRED_LIST_ERROR"
            )

    @command(
        name="system.credentials.create",
        description="Creates a new service credential for the user.",
        params_model={
            "label": "string",
            "service_type": "string",
            "provider_id": "string",
            "config": "json",
        },
    )
    def create_credential(
        self,
        session: Session,
        context: CoreContext,
        label: str,
        service_type: str,
        provider_id: str,
        config: Dict[str, Any],
    ) -> ServiceResponse:
        """Creates a new credential entry."""
        try:
            import uuid

            credential_id = str(uuid.uuid4())[:12]

            query = text(
                """
                INSERT INTO service_credentials (id, user_id, service_type, provider_id, config, label) 
                VALUES (:id, :uid, :stype, :pid, :config, :label)
                """
            )
            session.execute(
                query,
                {
                    "id": credential_id,
                    "uid": context.user_id,
                    "stype": service_type,
                    "pid": provider_id,
                    "config": config,
                    "label": label,
                },
            )
            return ServiceResponse.success_res(
                data={"id": credential_id}, message="Service credential created."
            )
        except Exception as e:
            logger.error(f"Error creating credential for {context.user_id}: {e}")
            return ServiceResponse.error_res(
                f"Failed to create credential: {str(e)}", "CRED_CREATE_ERROR"
            )

    @command(
        name="system.credentials.update_status",
        description="Updates the active status of a specific credential.",
        params_model={"credential_id": "string", "is_active": "boolean"},
    )
    def update_credential_status(
        self,
        session: Session,
        context: CoreContext,
        credential_id: str,
        is_active: bool,
    ) -> ServiceResponse:
        """Toggles the is_active flag for a credential."""
        try:
            # Verify ownership before updating
            query = text(
                "UPDATE service_credentials SET is_active = :active WHERE id = :cid AND user_id = :uid"
            )
            result = session.execute(
                query,
                {"active": is_active, "cid": credential_id, "uid": context.user_id},
            )

            if result.rowcount == 0:
                return ServiceResponse.error_res(
                    "Credential not found or access denied", "CRED_NOT_FOUND"
                )

            return ServiceResponse.success_res(message="Credential status updated.")
        except Exception as e:
            logger.error(f"Error updating status for {credential_id}: {e}")
            return ServiceResponse.error_res(
                f"Failed to update status: {str(e)}", "CRED_STATUS_ERROR"
            )


# Singleton
credential_service = CredentialService()
