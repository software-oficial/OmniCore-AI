import logging
import time
import asyncio
import difflib
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Callable, List
from fastapi import Request
from core.dispatcher.core_types import CoreContext, ServiceResponse
from core.dispatcher.normalizer import CommandNormalizer
from core.dispatcher.validator import RequestValidator
from core.auth.token_manager import token_manager
from core.registry.infrastructure_registry import infrastructure_registry
from core.governance.governance_service import governance_service
from infra.cache.redis_manager import cache_manager
from infra.db.db_manager import db_manager
from infra.validation.sanitizer import sanitizer
from infra.validation.type_checker import type_checker

logger = logging.getLogger("OmniCore.Gateway")
error_logger = logging.getLogger("OmniCore.Errors")

class AIGateway:
    """
    The Entry Point for all AI Agent requests.
    Implements the 3-layer security check and dynamic DB injection.
    """

    def __init__(self):
        from core.module_loader import module_loader
        self.loader = module_loader
        # Dedicated pool for blocking I/O bound business logic
        self.executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="GatewayWorker")

    def register_command(self, command_name: str, handler: Callable, description: str = "No description provided", params_schema: Optional[Dict[str, Any]] = None, is_system: bool = False):
        """Registers a command handler with semantic metadata for AI discovery."""
        self.loader._command_registry[command_name] = {
            "handler": handler,
            "description": description,
            "params_schema": params_schema or {},
            "registered_at": time.time(),
            "is_system": is_system
        }
        logger.info(f"✅ Command Registered: {command_name} | Desc: {description} | System: {is_system}")

    async def execute(self, command_name: Optional[str], token: str, params: Optional[Dict[str, Any]], request: Request, flow: Optional[List[Dict[str, Any]]] = None, requested_mode: Optional[str] = None):
        start_time = time.perf_counter()
        traces = {}
        
        # 0. Command Normalization (Delegated)
        effective_command, was_aliased = CommandNormalizer.normalize(command_name)

        # 1. Validation (Delegated)
        cmd_metadata = self.loader.get_metadata(effective_command)
        schema = cmd_metadata.get('params_schema', {})
        
        is_valid, error_res, filtered_params = RequestValidator.validate(effective_command, params, schema)
        if not is_valid:
            return error_res

        # 2. Token Validation
        t_auth_start = time.perf_counter()

        is_valid, agent_id, jwt_tier = token_manager.validate_token(token)
        traces['auth_ms'] = (time.perf_counter() - t_auth_start) * 1000
        
        if not is_valid:
            logger.warning(f"⚠️ Auth Failed: Invalid token used")
            res = ServiceResponse.error_res("Invalid or expired token", "AUTH_TOKEN_INVALID")
            duration_ms = (time.perf_counter() - start_time) * 1000
            res.latency_ms = duration_ms
            from core.telemetry.telemetry_service import telemetry_service
            telemetry_service.track_request("unknown", "unknown", "gateway.execute", duration_ms / 1000, False)
            return res

        # 3. Context Retrieval
        t_infra_start = time.perf_counter()
        app_context = infrastructure_registry.get_app_context(agent_id)
        traces['infra_ms'] = (time.perf_counter() - t_infra_start) * 1000
        
        if not app_context:
            logger.warning(f"⚠️ Infrastructure not found for agent: {agent_id}")
            res = ServiceResponse.error_res("No associated business infrastructure found.", "INFRA_NOT_FOUND")
            duration_ms = (time.perf_counter() - start_time) * 1000
            res.latency_ms = duration_ms
            from core.telemetry.telemetry_service import telemetry_service
            telemetry_service.track_request(agent_id, "unknown", "gateway.execute", duration_ms / 1000, False)
            return res
        
        # Resolve Mode: Header -> Default PRODUCTION
        mode = requested_mode.upper() if requested_mode else "PRODUCTION"
        if mode not in ["LEARNING", "PRODUCTION"]:
            mode = "PRODUCTION"

        # Use JWT tier if available, otherwise fallback to registry
        effective_tier = jwt_tier or app_context.get("tier", "FREE")
        
        ctx = CoreContext(
            agent_id=agent_id, 
            app_id=app_context["app_id"], 
            mode=mode, 
            db_config=app_context["db_config"], 
            tier=effective_tier
        )

        logger.info(f"🔍 DB CONFIG RESOLVED: App={ctx.app_id} | Mode={ctx.mode} | Tier={ctx.tier} | Host={ctx.db_config.get('host')} | Port={ctx.db_config.get('port')}")

        # 4. Execution Path
        t_exec_start = time.perf_counter()

        if flow:
            # BATCH EXECUTION MODE
            result = await self._handle_batch_execution(flow, ctx)
            cmd_for_telemetry = "gateway.batch"
        elif mode == "LEARNING":
            # SINGLE COMMAND - LEARNING
            result = await self._handle_learning_mode(effective_command, ctx, filtered_params)
            cmd_for_telemetry = effective_command
        else:
            # SINGLE COMMAND - PRODUCTION
            result = await self._handle_production_mode(effective_command, ctx, filtered_params)
            cmd_for_telemetry = effective_command
        traces['exec_ms'] = (time.perf_counter() - t_exec_start) * 1000
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        result.latency_ms = duration_ms
        
        from core.telemetry.telemetry_service import telemetry_service
        telemetry_service.track_request(agent_id, ctx.app_id, cmd_for_telemetry, duration_ms / 1000, result.success)

        # Pedagogical Hint for Aliases
        if was_aliased and result.success:
            result.message = f"💡 TIP: Command executed successfully, but you used an alias. The official name is `{effective_command}`. Use it for better compatibility.\n\n{result.message}"

        # 5. System Audit Log
        t_audit_start = time.perf_counter()
        try:
            from infra.db.core_db_manager import core_db_manager
            audit_query = "INSERT INTO system_audit_log (agent_id, app_id, command, status, message) VALUES (:agent_id, :app_id, :command, :status, :message)"
            core_db_manager.execute_raw(audit_query, {
                "agent_id": agent_id, "app_id": ctx.app_id, "command": cmd_for_telemetry,
                "status": "SUCCESS" if result.success else "FAILED", "message": result.message[:255]
            })
        except Exception as e:
            logger.error(f"Audit log failure: {e}")
        traces['audit_ms'] = (time.perf_counter() - t_audit_start) * 1000

        # Log detailed latency breakdown for debugging
        logger.info(f"⏱️ Latency Trace [{cmd_for_telemetry}]: Auth={traces['auth_ms']:.2f}ms | Infra={traces['infra_ms']:.2f}ms | Exec={traces['exec_ms']:.2f}ms | Audit={traces['audit_ms']:.2f}ms | Total={duration_ms:.2f}ms")

        if not result.success:
            error_logger.error(f"❌ Command/Flow Failure: {cmd_for_telemetry} | Agent={agent_id} | Code={result.error_code}")
            
        return result

    async def _handle_batch_execution(self, flow: List[Dict[str, Any]], ctx: CoreContext) -> ServiceResponse:

        """
        Executes a sequence of commands within a SINGLE database session.
        Ensures total atomicity: if one command fails, the entire flow is rolled back.
        """
        if not flow:
            return ServiceResponse.error_res("Empty flow provided", "EMPTY_FLOW")

        logger.info(f"🚀 Starting Batch Execution: {len(flow)} commands | Agent={ctx.agent_id}")
        
        try:
            async with db_manager.get_session(ctx.app_id, ctx.db_config, ctx.tier) as session:
                results = []
                
                for idx, step in enumerate(flow):
                    cmd_name = step.get('command')
                    params = step.get('params', {})
                    
                    if not cmd_name:
                        return ServiceResponse.error_res(f"Step {idx} missing 'command' name", "FLOW_INVALID_STEP")

                    handler = self.loader.get_handler(cmd_name)
                    if not handler:
                        return ServiceResponse.error_res(f"Command {cmd_name} (Step {idx}) not found", "COMMAND_NOT_FOUND")
                    
                    # Governance check for every step in the flow
                    is_allowed, error_res = governance_service.validate_access(cmd_name, ctx, session)
                    if not is_allowed:
                        session.rollback()
                        return ServiceResponse.error_res(
                            message=f"Governance failure at step {idx} ({cmd_name}): {error_res.message}",
                            error_code=error_res.error_code
                        )
                    
                    # Execution of the step
                    result = await asyncio.get_event_loop().run_in_executor(self.executor, lambda: handler(session=session, context=ctx, **params))
                    
                    if not isinstance(result, ServiceResponse) or not result.success:
                        session.rollback()
                        msg = result.message if isinstance(result, ServiceResponse) else "Unexpected handler return"
                        code = result.error_code if isinstance(result, ServiceResponse) else "HANDLER_ERROR"
                        return ServiceResponse.error_res(
                            message=f"Flow failed at step {idx} ({cmd_name}): {msg}",
                            error_code=code
                        )
                    
                    results.append(result)

                # ALL steps succeeded -> Final Commit
                session.commit()
                return ServiceResponse.success_res(
                    data={"results": [r.to_dict() if isinstance(r, ServiceResponse) else r for r in results]},
                    message=f"Flow executed successfully. {len(flow)} steps committed."
                )

        except Exception as e:
            logger.error(f"Batch execution critical failure: {e}")
            return ServiceResponse.error_res(f"Critical flow failure: {str(e)}", "FLOW_CRITICAL_ERROR")

    async def _handle_learning_mode(self, command_name: str, ctx: CoreContext, params: Dict[str, Any]):
        from core.governance.error_analytics_service import error_analytics_service

        if not command_name:
            return ServiceResponse.error_res("No command specified", "COMMAND_MISSING")

        # 1. Existence Check with Intelligent Suggestions
        handler = self.loader.get_handler(command_name)
        if not handler:
            all_commands = list(self.loader._command_registry.keys())
            closest_matches = difflib.get_close_matches(command_name, all_commands, n=1, cutoff=0.5)
            suggestion = f"\\n\\n👉 Did you mean: `{closest_matches[0]}`?" if closest_matches else ""
            
            return ServiceResponse.error_res(
                message=f"💡 LEARNING ERROR: Command '{command_name}' does not exist."
                        f"{suggestion}",
                error_code="COMMAND_NOT_FOUND"
            )

        # 2. Pedagogical Type and Parameter Validation
        cmd_metadata = self.loader.get_metadata(command_name)
        schema = cmd_metadata.get('params_schema', {})
        
        if isinstance(schema, dict):
            from infra.validation.type_checker import type_checker
            is_valid, type_err = type_checker.validate_types(params, schema)
            if not is_valid:
                return ServiceResponse.error_res(
                    message=f"💡 LEARNING ERROR: {type_err.message}",
                    error_code="LEARNING_TYPE_ERROR"
                )

        # 3. Mentorship and Learning Corrections
        guided = error_analytics_service.get_guided_solution(command_name, "COMMON_ERROR")
        if guided:
            return ServiceResponse.error_res(message=f"💡 MENTORSHIP: {guided}", error_code="LEARNING_PATTERN_FOUND")

        # 4. Pedagogical Success
        return ServiceResponse.success_res(
            data={"mock": "Simulated", "params": params}, 
            message=f"💡 SUCCESS: Simulation of {command_name} successful."
        )

    async def _handle_production_mode(self, command_name: str, ctx: CoreContext, params: Dict[str, Any]):
        handler = self.loader.get_handler(command_name)
        if not handler:
            return ServiceResponse.error_res(f"Command {command_name} not found", "COMMAND_NOT_FOUND")
        
        cmd_metadata = self.loader.get_metadata(command_name)
        is_system = cmd_metadata.get('is_system', False)

        if is_system:
            try:
                result = await asyncio.get_event_loop().run_in_executor(self.executor, lambda: handler(session=None, context=ctx, **params))
                return result if isinstance(result, ServiceResponse) else ServiceResponse.success_res(data=result)
            except Exception as e:
                from core.dispatcher.exceptions import handle_omnicore_exception
                return handle_omnicore_exception(e)

        try:
            async with db_manager.get_session(ctx.app_id, ctx.db_config, ctx.tier) as session:
                # Security Check
                is_allowed, error_res = governance_service.validate_access(command_name, ctx, session)
                if not is_allowed:
                    return error_res
                
                # Execute in Worker Pool to not block Event Loop
                result = await asyncio.get_event_loop().run_in_executor(self.executor, lambda: handler(session=session, context=ctx, **params))
                return result if isinstance(result, ServiceResponse) else ServiceResponse.success_res(data=result)
        except Exception as e:
            from core.dispatcher.exceptions import handle_omnicore_exception
            return handle_omnicore_exception(e)

ai_gateway = AIGateway()
