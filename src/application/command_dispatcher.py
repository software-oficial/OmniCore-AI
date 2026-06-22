import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, cast

from src.core.auth.token_manager import token_manager
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.exceptions import handle_omnicore_exception
from src.core.dispatcher.normalizer import CommandNormalizer
from src.core.dispatcher.validator import RequestValidator
from src.core.governance.governance_service import governance_service
from src.core.module_loader import module_loader
from src.core.registry.infrastructure_registry import business_registry
from src.infrastructure.db.core_db_manager import core_db_manager
from src.infrastructure.validation.sanitizer import sanitizer

logger = logging.getLogger("OmniCore.Dispatcher")


class CommandDispatcher:
    """
    The Orchestrator of the Enterprise Core (UUS).
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
                "No business linked to this user.",
                "BUSINESS_NOT_FOUND",
            )

        # Build Enterprise CoreContext (UUS)
        ctx = ctx_override or CoreContext(
            user_id=user_id,
            business_id=app_context["business_id"],
            role=app_context["role"],
            tier=jwt_tier or app_context.get("tier", "FREE"),
            entity="DISPATCHER",
            mode="PRODUCTION",
        )

        try:
            # 4. Governance (PBAC)
            # PBAC is still handled via governance service, which we'll need to adapt
            is_allowed, gov_error = governance_service.validate_access(
                effective_command, ctx, None
            )
            if not is_allowed:
                return cast(ServiceResponse, gov_error)

            # 5. Execution (Always using Core DB)
            handler = self.loader.get_handler(effective_command)
            if not handler:
                return ServiceResponse.error_res("Handler missing", "HANDLER_MISSING")

            # In UUS, we always provide the core session
            with core_db_manager.get_session() as session:
                # Load settings from business.settings (JSON)
                business_data = (
                    core_db_manager.execute_raw(
                        "SELECT settings FROM businesses WHERE id = :bid",
                        {"bid": ctx.business_id},
                    )
                    .mappings()
                    .first()
                )

                try:
                    ctx.settings = json.loads(business_data["settings"] or "{}")
                except (json.JSONDecodeError, TypeError, KeyError):
                    ctx.settings = {}

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
            audit_query = "INSERT INTO system_audit_log (user_id, business_id, command, status, message) VALUES (:uid, :bid, :cmd, :status, :msg)"
            core_db_manager.execute_raw(
                audit_query,
                {
                    "uid": ctx.user_id,
                    "bid": ctx.business_id,
                    "cmd": command,
                    "status": "SUCCESS" if result.success else "FAILED",
                    "msg": result.message[:255],
                },
            )
        except Exception as e:
            logger.error(f"Audit log failure: {e}")


# Singleton for the entire system
command_dispatcher = CommandDispatcher()
