import asyncio
import logging
import time
from typing import Any, Dict, Optional, cast

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.normalizer import CommandNormalizer
from src.core.dispatcher.validator import RequestValidator
from src.core.governance.governance_service import governance_service
from src.core.module_loader import module_loader
from src.core.registry.infrastructure_registry import business_registry
from src.core.settings_service import settings_service
from src.infrastructure.db.db_manager import db_manager
from src.infrastructure.validation.sanitizer import sanitizer

logger = logging.getLogger("OmniCore.Dispatcher")


class CommandDispatcher:
    """
    The Orchestrator of the Enterprise Core.
    Implements the Dispatcher Pattern to decouple interfaces from execution.
    """

    def __init__(self):
        self.loader = module_loader
        self.executor = asyncio.get_event_loop().run_in_executor

    async def dispatch(
        self,
        command_name: str,
        token: str,
        params: Dict[str, Any],
        ctx_override: Optional[CoreContext] = None,
    ) -> ServiceResponse:
        start_time = time.perf_counter()

        # 1. Normalization
        effective_command, was_aliased = CommandNormalizer.normalize(command_name)

        # 2. Metadata & Validation
        cmd_metadata = self.loader.get_metadata(effective_command)
        if not cmd_metadata:
            return ServiceResponse.error_res(
                f"Command {effective_command} not found", "COMMAND_NOT_FOUND"
            )

        model = cmd_metadata.get("params_model", {})
        is_valid, error_res, filtered_params = RequestValidator.validate(
            effective_command, params, model
        )
        if not is_valid:
            return cast(ServiceResponse, error_res)

        # Anti-XSS
        filtered_params = sanitizer.sanitize_params(filtered_params)

        # 3. Identity & Context Resolution
        from src.core.auth.token_manager import token_manager

        is_valid_token, payload, jwt_tier = token_manager.validate_token(token)
        if not is_valid_token or not payload:
            return ServiceResponse.error_res(
                "Invalid token or missing user identity", "AUTH_TOKEN_INVALID"
            )

        user_id = payload.get("user_id") or payload.get("agent_id")
        if not user_id:
            return ServiceResponse.error_res(
                "Invalid token or missing user identity", "AUTH_TOKEN_INVALID"
            )

        app_context = business_registry.get_business_context(user_id)
        if not app_context:
            return ServiceResponse.error_res(
                "No business database linked to this user.",
                "INFRA_NOT_FOUND",
            )

        # Build Enterprise CoreContext
        ctx = ctx_override or CoreContext(
            agent_id=user_id,
            app_id=app_context["business_id"],
            dev_id="SYSTEM",
            mode="PRODUCTION",
            db_config=app_context["db_config"],
            tier=jwt_tier or app_context.get("tier", "FREE"),
            entity="DISPATCHER",
            execution_strategy="DIRECT",
        )

        try:
            # 4. Governance (PBAC)
            is_allowed, gov_error = governance_service.validate_access(
                effective_command, ctx, None
            )
            if not is_allowed:
                return cast(ServiceResponse, gov_error)

            # 4b. API Credential Validation
            api_provider = cmd_metadata.get("api_provider")
            if api_provider:
                from src.domains.system.credential_service import credential_service
                from src.infrastructure.db.core_db_manager import core_db_manager

                with core_db_manager.get_session() as session:
                    if not credential_service.has_provider_configured(
                        session, ctx.user_id, api_provider
                    ):
                        return ServiceResponse.error_res(
                            f"Falta configurar API de {api_provider}.",
                            "API_NOT_CONFIGURED",
                        )

                    cred = credential_service.get_credential(
                        session, ctx.user_id, api_provider
                    )
                    if cred:
                        ctx.active_credentials = ctx.active_credentials or {}
                        ctx.active_credentials[api_provider] = cred

            # 5. Execution
            handler = self.loader.get_handler(effective_command)
            if not handler:
                return ServiceResponse.error_res("Handler missing", "HANDLER_MISSING")

            # Handle both async and sync handlers
            if cmd_metadata.get("is_system", False):
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(session=None, context=ctx, **filtered_params)
                else:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: handler(session=None, context=ctx, **filtered_params),
                    )
            else:
                if ctx.db_config is None:
                    return ServiceResponse.error_res(
                        "Database configuration is missing.",
                        "INFRA_CONFIG_MISSING",
                    )

                async with db_manager.get_session(
                    ctx.app_id, ctx.db_config, ctx.tier
                ) as session:
                    ctx.settings = settings_service.get_all_settings(
                        session, ctx.app_id
                    )

                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(
                            session=session, context=ctx, **filtered_params
                        )
                    else:
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(
                            None,
                            lambda: handler(
                                session=session, context=ctx, **filtered_params
                            ),
                        )

            if not isinstance(result, ServiceResponse):
                result = ServiceResponse.success_res(data=result)

        except Exception as e:
            from src.core.dispatcher.exceptions import handle_omnicore_exception

            result = handle_omnicore_exception(e)

        finally:
            # 6. Audit Trail
            self._log_audit(ctx, effective_command, result)

        duration_ms = (time.perf_counter() - start_time) * 1000
        result.latency_ms = duration_ms
        return result

    def _log_audit(self, ctx: CoreContext, command: str, result: ServiceResponse):
        """Persistent audit log in the core database."""
        try:
            from src.infrastructure.db.core_db_manager import core_db_manager

            logger.info(
                f"Logging audit for command: {command}, status: {result.success}, app_id: {ctx.app_id}"
            )

            audit_query = "INSERT INTO system_audit_log (agent_id, app_id, command, status, message) VALUES (:agent_id, :app_id, :command, :status, :message)"
            core_db_manager.execute_raw(
                audit_query,
                {
                    "agent_id": ctx.agent_id,
                    "app_id": ctx.app_id,
                    "command": command,
                    "status": "SUCCESS" if result.success else "FAILED",
                    "message": result.message[:255],
                },
            )
            logger.info("Audit log successfully inserted.")
        except Exception as e:
            logger.error(f"Audit log failure: {e}", exc_info=True)


# Singleton for the entire system
command_dispatcher = CommandDispatcher()
