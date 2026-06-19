import json
import logging
import uuid
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

    # --- Internal Helpers (Used by Dispatcher) ---

    def has_provider_configured(
        self, session: Session, user_id: str, provider: str
    ) -> bool:
        """Checks if the user has at least one active credential for the given provider."""
        try:
            query = text(
                "SELECT 1 FROM user_credentials WHERE user_id = :uid AND provider = :provider LIMIT 1"
            )
            result = session.execute(
                query, {"uid": user_id, "provider": provider}
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking provider configuration for {user_id}: {e}")
            return False

    def get_credential(
        self,
        session: Session,
        user_id: str,
        provider: str,
        account_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific credential or the default one for the provider.
        """
        try:
            if account_id:
                query = text(
                    "SELECT * FROM user_credentials WHERE id = :cid AND user_id = :uid"
                )
                params = {"cid": account_id, "uid": user_id}
            else:
                # Try to find the default one first
                query = text(
                    "SELECT * FROM user_credentials WHERE user_id = :uid AND provider = :provider AND is_default = 1 LIMIT 1"
                )
                params = {"uid": user_id, "provider": provider}

                # Fallback to any credential for that provider if no default is set
                result = session.execute(query, params).mappings().fetchone()
                if not result:
                    query = text(
                        "SELECT * FROM user_credentials WHERE user_id = :uid AND provider = :provider LIMIT 1"
                    )
                    result = session.execute(query, params).mappings().fetchone()

                return dict(result) if result else None

            result = session.execute(query, params).mappings().fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error retrieving credential for {user_id} [{provider}]: {e}")
            return None

    # --- API Commands ---

    @command(
        name="system.credentials.list",
        description="Lists all service credentials for the current user/business.",
        params_model={"provider": "string"},
    )
    def list_credentials(
        self, session: Session, context: CoreContext, provider: Optional[str] = None
    ) -> ServiceResponse:
        """Retrieves active credentials, optionally filtered by provider."""
        try:
            query = "SELECT id, user_id, provider, account_name, is_default, created_at FROM user_credentials WHERE user_id = :uid"
            params = {"uid": context.user_id}

            if provider:
                query += " AND provider = :provider"
                params["provider"] = provider

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
            "account_name": "string",
            "provider": "string",
            "api_key": "string",
            "secret": "string",
            "metadata": "json",
            "is_default": "boolean",
        },
    )
    def create_credential(
        self,
        session: Session,
        context: CoreContext,
        account_name: str,
        provider: str,
        api_key: str,
        secret: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_default: bool = False,
    ) -> ServiceResponse:
        """Creates a new credential entry."""
        try:
            credential_id = str(uuid.uuid4())[:12]

            # If this is set as default, unset others for the same provider
            if is_default:
                session.execute(
                    text(
                        "UPDATE user_credentials SET is_default = 0 WHERE user_id = :uid AND provider = :provider"
                    ),
                    {"uid": context.user_id, "provider": provider},
                )

            query = text(
                """
                INSERT INTO user_credentials (id, user_id, provider, account_name, api_key, secret, metadata, is_default) 
                VALUES (:id, :uid, :provider, :account_name, :api_key, :secret, :metadata, :is_default)
                """
            )
            session.execute(
                query,
                {
                    "id": credential_id,
                    "uid": context.user_id,
                    "provider": provider,
                    "account_name": account_name,
                    "api_key": api_key,
                    "secret": secret,
                    "metadata": json.dumps(metadata) if metadata else None,
                    "is_default": is_default,
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
        name="system.credentials.delete",
        description="Deletes a specific credential.",
        params_model={"credential_id": "string"},
    )
    def delete_credential(
        self,
        session: Session,
        context: CoreContext,
        credential_id: str,
    ) -> ServiceResponse:
        """Deletes a credential if owned by the user."""
        try:
            query = text(
                "DELETE FROM user_credentials WHERE id = :cid AND user_id = :uid"
            )
            result = session.execute(
                query, {"cid": credential_id, "uid": context.user_id}
            )

            if result.rowcount == 0:
                return ServiceResponse.error_res(
                    "Credential not found or access denied", "CRED_NOT_FOUND"
                )

            return ServiceResponse.success_res(message="Credential deleted.")
        except Exception as e:
            logger.error(
                f"Error deleting credential {credential_id} for {context.user_id}: {e}"
            )
            return ServiceResponse.error_res(
                f"Failed to delete credential: {str(e)}", "CRED_DELETE_ERROR"
            )


# Singleton
credential_service = CredentialService()
