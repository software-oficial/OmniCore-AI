import asyncio
import difflib
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

from fastapi import Request
from pydantic import BaseModel

from src.core.auth.token_manager import token_manager
from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.normalizer import CommandNormalizer
from src.core.dispatcher.validator import RequestValidator
from src.core.governance.governance_service import governance_service
from src.core.registry.infrastructure_registry import infrastructure_registry
from src.infrastructure.db.db_manager import db_manager
from src.infrastructure.validation.sanitizer import sanitizer

logger = logging.getLogger("OmniCore.Gateway")
error_logger = logging.getLogger("OmniCore.Errors")


class AIGateway:
    """
    The Entry Point for all AI Agent requests.
    Implements the 3-layer security check and dynamic DB injection.
    """

    def __init__(self):
        from src.core.module_loader import module_loader

        self.loader = module_loader
        # Dedicated pool for blocking I/O bound business logic
        self.executor = ThreadPoolExecutor(
            max_workers=20, thread_name_prefix="GatewayWorker"
        )

    def register_command(
        self,
        command_name: str,
        handler: Callable,
        description: str = "No description provided",
        params_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
        example: Optional[Dict[str, Any]] = None,
        is_system: bool = False,
    ):
        """Registers a command handler with semantic metadata for AI discovery."""
        # If it's a Pydantic model, extract the schema for the discovery registry
        final_schema = params_schema or {}
        if isinstance(params_schema, type) and issubclass(params_schema, BaseModel):
            final_schema = params_schema.model_json_schema()

        self.loader._command_registry[command_name] = {
            "handler": handler,
            "description": description,
            "params_schema": final_schema,
            "example": example,
            "registered_at": time.time(),
            "is_system": is_system,
        }
        logger.info(
            f"✅ Command Registered: {command_name} | Desc: {description} | System: {is_system}"
        )

    async def execute(
        self,
        command_name: Optional[str],
        token: str,
        params: Optional[Dict[str, Any]],
        request: Request,
        flow: Optional[List[Dict[str, Any]]] = None,
        requested_mode: Optional[str] = None,
    ):
        start_time = time.perf_counter()
        traces = {}

        # 0. Command Normalization (Delegated)
        effective_command, was_aliased = CommandNormalizer.normalize(command_name or "")

        # 1. Validation (Delegated)
        cmd_metadata = self.loader.get_metadata(effective_command)
        schema = cmd_metadata.get("params_schema", {})

        is_valid, error_res, filtered_params = RequestValidator.validate(
            effective_command, params or {}, schema
        )
        if not is_valid:
            return error_res

        # Anti-XSS: Sanitize filtered parameters before execution
        filtered_params = sanitizer.sanitize_params(filtered_params)

        # 2. Token Validation
        t_auth_start = time.perf_counter()

        is_valid, agent_id, jwt_tier = token_manager.validate_token(token)
        traces["auth_ms"] = (time.perf_counter() - t_auth_start) * 1000

        if not is_valid:
            logger.warning("⚠️ Auth Failed: Invalid token used")
            res = ServiceResponse.error_res(
                "Invalid or expired token", "AUTH_TOKEN_INVALID"
            )
            duration_ms = (time.perf_counter() - start_time) * 1000
            res.latency_ms = duration_ms
            from src.core.telemetry.telemetry_service import telemetry_service

            telemetry_service.track_request(
                "unknown", "unknown", "gateway.execute", duration_ms / 1000, False
            )
            return res

        # Mypy: agent_id is now str
        assert agent_id is not None

        # 3. Context Retrieval
        t_infra_start = time.perf_counter()
        app_context = infrastructure_registry.get_app_context(agent_id)
        traces["infra_ms"] = (time.perf_counter() - t_infra_start) * 1000

        if not app_context:
            logger.warning(f"⚠️ Infrastructure not found for agent: {agent_id}")
            res = ServiceResponse.error_res(
                "No associated business infrastructure found.", "INFRA_NOT_FOUND"
            )
            duration_ms = (time.perf_counter() - start_time) * 1000
            res.latency_ms = duration_ms
            from src.core.telemetry.telemetry_service import telemetry_service

            telemetry_service.track_request(
                agent_id, "unknown", "gateway.execute", duration_ms / 1000, False
            )
            return res

        # Mypy: app_context is now dict
        assert app_context is not None

        # Resolve Mode: Header -> Default PRODUCTION
        mode = requested_mode.upper() if requested_mode else "PRODUCTION"
        if mode not in ["LEARNING", "PRODUCTION"]:
            mode = "PRODUCTION"

        # Determine Execution Strategy: DELEGATED if host is local
        db_host = (app_context or {}).get("db_config", {}).get("host")
        execution_strategy = "DIRECT"
        if db_host in ["localhost", "127.0.0.1"]:
            execution_strategy = "DELEGATED"

        # FORCE DIRECT for system commands to avoid delegation of cloud-state queries
        if cmd_metadata.get("is_system", False):
            execution_strategy = "DIRECT"

        # Use JWT tier if available, fallback to registry
        effective_tier = jwt_tier or app_context.get("tier", "FREE")

        ctx = CoreContext(
            agent_id=agent_id,
            app_id=app_context["app_id"],
            mode=mode,
            db_config=app_context["db_config"],
            tier=effective_tier,
            entity="API",
            execution_strategy=execution_strategy,
        )

        logger.info(
            f"🔍 DB CONFIG RESOLVED: App={ctx.app_id} | Mode={ctx.mode} | Tier={ctx.tier} | Strategy={ctx.execution_strategy} | Host={(ctx.db_config or {}).get('host')}"
        )

        # 4. Execution Path
        t_exec_start = time.perf_counter()

        if ctx.execution_strategy == "DELEGATED":
            # DELEGATED MODE: The Cloud API only validates and authorizes.
            return ServiceResponse.success_res(
                data={
                    "action": "EXECUTE_LOCALLY",
                    "command": effective_command,
                    "params": filtered_params,
                    "context": {
                        "app_id": ctx.app_id,
                        "tier": ctx.tier,
                        "mode": ctx.mode,
                    },
                },
                message="Execution authorized. Please execute this command on your local infrastructure.",
            )

        if flow:
            # BATCH EXECUTION MODE
            result = await self._handle_batch_execution(flow, ctx)
            cmd_for_telemetry = "gateway.batch"
        elif mode == "LEARNING":
            # SINGLE COMMAND - LEARNING
            result = await self._handle_learning_mode(
                effective_command, ctx, filtered_params
            )
            cmd_for_telemetry = effective_command
        else:
            # SINGLE COMMAND - PRODUCTION
            result = await self._handle_production_mode(
                effective_command, ctx, filtered_params
            )
            cmd_for_telemetry = effective_command
        traces["exec_ms"] = (time.perf_counter() - t_exec_start) * 1000

        duration_ms = (time.perf_counter() - start_time) * 1000

        # FORCE ENVELOPE PATTERN: Ensure result is ALWAYS a ServiceResponse
        # This prevents the SDK from crashing when handlers return raw lists or dicts
        if not isinstance(result, ServiceResponse):
            result = ServiceResponse.success_res(data=result)

        result.latency_ms = duration_ms

        from src.core.telemetry.telemetry_service import telemetry_service

        telemetry_service.track_request(
            agent_id, ctx.app_id, cmd_for_telemetry, duration_ms / 1000, result.success
        )

        # Pedagogical Hint for Aliases
        if was_aliased and result.success:
            result.message = f"💡 TIP: Command executed successfully, but you used an alias. The official name is `{effective_command}`. Use it for better compatibility.\n\n{result.message}"

        # 5. System Audit Log
        t_audit_start = time.perf_counter()
        try:
            from src.infrastructure.db.core_db_manager import core_db_manager

            audit_query = "INSERT INTO system_audit_log (agent_id, app_id, command, status, message) VALUES (:agent_id, :app_id, :command, :status, :message)"
            core_db_manager.execute_raw(
                audit_query,
                {
                    "agent_id": agent_id,
                    "app_id": ctx.app_id,
                    "command": cmd_for_telemetry,
                    "status": "SUCCESS" if result.success else "FAILED",
                    "message": result.message[:255],
                },
            )
        except Exception as e:
            logger.error(f"Audit log failure: {e}")
        traces["audit_ms"] = (time.perf_counter() - t_audit_start) * 1000

        # Log detailed latency breakdown for debugging
        logger.info(
            f"⏱️ Latency Trace [{cmd_for_telemetry}]: Auth={traces['auth_ms']:.2f}ms | Infra={traces['infra_ms']:.2f}ms | Exec={traces['exec_ms']:.2f}ms | Audit={traces['audit_ms']:.2f}ms | Total={duration_ms:.2f}ms"
        )

        if not result.success:
            error_logger.error(
                f"❌ Command/Flow Failure: {cmd_for_telemetry} | Agent={agent_id} | Code={result.error_code}"
            )

        return result

    async def _handle_batch_execution(
        self, flow: List[Dict[str, Any]], ctx: CoreContext
    ) -> ServiceResponse:
        """
        Executes a sequence of commands within a SINGLE database session.
        Ensures total atomicity: if one command fails, the entire flow is rolled back.
        """
        if not flow:
            return ServiceResponse.error_res("Empty flow provided", "EMPTY_FLOW")

        logger.info(
            f"🚀 Starting Batch Execution: {len(flow)} commands | Agent={ctx.agent_id}"
        )

        try:
            async with db_manager.get_session(
                ctx.app_id, ctx.db_config or {}, ctx.tier
            ) as session:
                results = []

                for idx, step in enumerate(flow):
                    cmd_name = step.get("command")
                    params = step.get("params", {})

                    if not cmd_name:
                        return ServiceResponse.error_res(
                            f"Step {idx} missing 'command' name", "FLOW_INVALID_STEP"
                        )

                    handler = self.loader.get_handler(cmd_name)
                    if not handler:
                        return ServiceResponse.error_res(
                            f"Command {cmd_name} (Step {idx}) not found",
                            "COMMAND_NOT_FOUND",
                        )

                    # Governance check for every step in the flow
                    is_allowed, error_res = governance_service.validate_access(
                        cmd_name, ctx, session
                    )
                    if not is_allowed:
                        session.rollback()
                        err = cast(ServiceResponse, error_res)
                        msg = err.message if err else "Access denied"
                        code = err.error_code if err else "GOVERNANCE_ERROR"
                        return ServiceResponse.error_res(
                            message=f"Governance failure at step {idx} ({cmd_name}): {msg}",
                            error_code=code if code else "GOVERNANCE_ERROR",
                        )

                    # Execution of the step
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(session=session, context=ctx, **params)
                    else:
                        result = await asyncio.get_event_loop().run_in_executor(
                            self.executor,
                            lambda: handler(session=session, context=ctx, **params),
                        )

                    if (
                        result is None
                        or not isinstance(result, ServiceResponse)
                        or not result.success
                    ):
                        session.rollback()
                        res_obj = (
                            cast(ServiceResponse, result)
                            if isinstance(result, ServiceResponse)
                            else None
                        )
                        msg = (
                            res_obj.message if res_obj else "Unexpected handler return"
                        )
                        code = res_obj.error_code if res_obj else "HANDLER_ERROR"
                        return ServiceResponse.error_res(
                            message=f"Flow failed at step {idx} ({cmd_name}): {msg}",
                            error_code=code if code else "HANDLER_ERROR",
                        )

                    results.append(result)

                # ALL steps succeeded -> Final Commit
                session.commit()
                return ServiceResponse.success_res(
                    data={
                        "results": [
                            r.to_dict() if isinstance(r, ServiceResponse) else r
                            for r in results
                        ]
                    },
                    message=f"Flow executed successfully. {len(flow)} steps committed.",
                )

        except Exception as e:
            logger.error(f"Batch execution critical failure: {e}")
            return ServiceResponse.error_res(
                f"Critical flow failure: {str(e)}", "FLOW_CRITICAL_ERROR"
            )

    async def _handle_learning_mode(
        self, command_name: str, ctx: CoreContext, params: Dict[str, Any]
    ):
        from src.core.governance.error_analytics_service import error_analytics_service

        if not command_name:
            return ServiceResponse.error_res("No command specified", "COMMAND_MISSING")

        # 1. Existence Check with Intelligent Suggestions
        handler = self.loader.get_handler(command_name)
        if not handler:
            all_commands = list(self.loader._command_registry.keys())
            closest_matches = difflib.get_close_matches(
                command_name, all_commands, n=1, cutoff=0.5
            )
            suggestion = (
                f"\\n\\n👉 Did you mean: `{closest_matches[0]}`?"
                if closest_matches
                else ""
            )

            return ServiceResponse.error_res(
                message=f"💡 LEARNING ERROR: Command '{command_name}' does not exist."
                f"{suggestion}",
                error_code="COMMAND_NOT_FOUND",
            )

        # 2. Pedagogical Type and Parameter Validation
        cmd_metadata = self.loader.get_metadata(command_name)
        schema = cmd_metadata.get("params_schema", {})

        if isinstance(schema, dict):
            from src.infrastructure.validation.type_checker import type_checker

            is_valid, type_err = type_checker.validate_types(params, schema)
            if not is_valid:
                err = cast(ServiceResponse, type_err)
                return ServiceResponse.error_res(
                    message=f"💡 LEARNING ERROR: {err.message if err else 'Invalid type'}",
                    error_code="LEARNING_TYPE_ERROR",
                )

        # 3. Mentorship and Learning Corrections
        guided = error_analytics_service.get_guided_solution(
            command_name, "COMMON_ERROR"
        )
        if guided:
            return ServiceResponse.error_res(
                message=f"💡 MENTORSHIP: {guided}", error_code="LEARNING_PATTERN_FOUND"
            )

        # 4. Pedagogical Success
        return ServiceResponse.success_res(
            data={"mock": "Simulated", "params": params},
            message=f"💡 SUCCESS: Simulation of {command_name} successful.",
        )

    async def _handle_production_mode(
        self, command_name: str, ctx: CoreContext, params: Dict[str, Any]
    ):
        handler = self.loader.get_handler(command_name)
        if not handler:
            return ServiceResponse.error_res(
                message=f"Command '{command_name}' not found. To discover all available commands, use 'GET /api/discovery/commands'. For setup guides, use 'GET /api/agent/guides'.",
                error_code="COMMAND_NOT_FOUND",
            )

        cmd_metadata = self.loader.get_metadata(command_name)
        is_system = cmd_metadata.get("is_system", False)

        if is_system:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor, lambda: handler(session=None, context=ctx, **params)
                )
                return (
                    result
                    if isinstance(result, ServiceResponse)
                    else ServiceResponse.success_res(data=result)
                )
            except Exception as e:
                from src.core.dispatcher.exceptions import handle_omnicore_exception

                return handle_omnicore_exception(e)

        try:
            async with db_manager.get_session(
                ctx.app_id, ctx.db_config or {}, ctx.tier
            ) as session:
                # Security Check
                is_allowed, error_res = governance_service.validate_access(
                    command_name, ctx, session
                )
                if not is_allowed:
                    err = cast(ServiceResponse, error_res)
                    return (
                        err
                        if err
                        else ServiceResponse.error_res(
                            "Access denied", "GOVERNANCE_ERROR"
                        )
                    )

                # Execute in Worker Pool to not block Event Loop
                result = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: handler(session=session, context=ctx, **params),
                )
                return (
                    result
                    if isinstance(result, ServiceResponse)
                    else ServiceResponse.success_res(data=result)
                )
        except Exception as e:
            # ODDS Pilar 3: Smart Error Feedback for DB errors
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                import re

                match = re.search(
                    r'column "([^"]+)" of relation "([^"]+)" does not exist', str(e)
                )
                if match:
                    wrong_col, table_name = match.groups()

                    # Introspect schema for suggestions
                    try:
                        query = f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
                        with db_manager.get_session_sync(
                            ctx.app_id, ctx.db_config or {}, ctx.tier
                        ) as session:
                            columns = [row[0] for row in session.execute(query).all()]

                        closest = difflib.get_close_matches(
                            wrong_col, columns, n=1, cutoff=0.5
                        )
                        if closest:
                            suggestion = f" Column '{wrong_col}' does not exist in table '{table_name}'. Did you mean '{closest[0]} '?"
                            return ServiceResponse.error_res(
                                message=f"💡 SEMANTIC ERROR: {str(e)}{suggestion}",
                                error_code="SCHEMA_MISMATCH",
                            )
                    except Exception as inner_e:
                        logger.error(
                            f"Failed to generate semantic suggestion: {inner_e}"
                        )

            from src.core.dispatcher.exceptions import handle_omnicore_exception

            return handle_omnicore_exception(e)


ai_gateway = AIGateway()
