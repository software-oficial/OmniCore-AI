import logging
import time
import asyncio
from typing import Any, Dict, Optional, Callable
from fastapi import HTTPException, Request
from core.dispatcher.core_types import CoreContext, ServiceResponse
from core.auth.token_manager import token_manager
from core.registry.infrastructure_registry import infrastructure_registry
from core.governance.governance_service import governance_service
from infra.cache.redis_manager import cache_manager
from infra.db.db_manager import db_manager

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

    def register_command(self, command_name: str, handler: Callable, description: str = "No description provided", params_schema: Optional[Dict[str, Any]] = None):
        """Registers a command handler with semantic metadata for AI discovery."""
        self.loader._command_registry[command_name] = {
            "handler": handler,
            "description": description,
            "params_schema": params_schema or {},
            "registered_at": time.time()
        }
        logger.info(f"✅ Command Registered: {command_name} | Desc: {description}")

    async def execute(self, command_name: str, token: str, params: Dict[str, Any], request: Request):
        start_time = time.perf_counter()
        logger.info(f"📩 Incoming Request: command={command_name} | token_prefix={token[:10]}...")
        
        # 1. Token Validation
        is_valid, mode, agent_id = token_manager.validate_token(token)
        if not is_valid:
            logger.warning(f"⚠️ Auth Failed: Invalid token used for {command_name}")
            res = ServiceResponse.error_res("Invalid or expired token", "AUTH_TOKEN_INVALID")
            duration_ms = (time.perf_counter() - start_time) * 1000
            res.latency_ms = duration_ms
            from core.telemetry.telemetry_service import telemetry_service
            telemetry_service.track_request("unknown", "unknown", command_name, duration_ms / 1000, False)
            return res

        # 2. Context Retrieval
        app_context = infrastructure_registry.get_app_context(agent_id)
        if not app_context:
            logger.warning(f"⚠️ Infrastructure not found for agent: {agent_id}")
            res = ServiceResponse.error_res("No associated business infrastructure found.", "INFRA_NOT_FOUND")
            duration_ms = (time.perf_counter() - start_time) * 1000
            res.latency_ms = duration_ms
            from core.telemetry.telemetry_service import telemetry_service
            telemetry_service.track_request(agent_id, "unknown", command_name, duration_ms / 1000, False)
            return res
        
        ctx = CoreContext(
            agent_id=agent_id, 
            app_id=app_context["app_id"], 
            mode=mode, 
            db_config=app_context["db_config"], 
            tier=app_context["tier"]
        )

        # 3. Mode-Based Execution (Now fully async)
        if mode == "LEARNING":
            result = await self._handle_learning_mode(command_name, ctx, params)
        else:
            result = await self._handle_production_mode(command_name, ctx, params)
        
        duration_ms = (time.perf_counter() - start_time) * 1000
        result.latency_ms = duration_ms
        
        from core.telemetry.telemetry_service import telemetry_service
        telemetry_service.track_request(agent_id, ctx.app_id, command_name, duration_ms / 1000, result.success)

        # System Audit Log
        try:
            from infra.db.core_db_manager import core_db_manager
            audit_query = "INSERT INTO system_audit_log (agent_id, app_id, command, status, message) VALUES (:agent_id, :app_id, :command, :status, :message)"
            core_db_manager.execute_raw(audit_query, {
                "agent_id": agent_id, "app_id": ctx.app_id, "command": command_name,
                "status": "SUCCESS" if result.success else "FAILED", "message": result.message[:255]
            })
        except Exception as e:
            logger.error(f"Audit log failure: {e}")

        if not result.success:
            error_logger.error(f"❌ Command Failure: {command_name} | Agent={agent_id} | Code={result.error_code}")
            
        return result

    async def _handle_learning_mode(self, command_name: str, ctx: CoreContext, params: Dict[str, Any]):
        from core.governance.error_analytics_service import error_analytics_service
        import inspect

        # 1. Strict Parameter Validation (Fixing the 'Learning Black Hole')
        cmd_metadata = self.loader.get_metadata(command_name)
        handler = self.loader.get_handler(command_name)
        
        # Use schema if available, otherwise infer from function signature
        expected_params = cmd_metadata.get('params_schema', {})
        if not expected_params and handler:
            try:
                sig = inspect.signature(handler)
                # Identify parameters that are not 'session', 'context', 'self' and have no default value
                expected_params = {
                    name: "required" 
                    for name, param in sig.parameters.items() 
                    if name not in ('session', 'context', 'self') and param.default == inspect.Parameter.empty
                }
            except Exception as e:
                logger.warning(f"Could not infer signature for {command_name}: {e}")

        if expected_params:
            missing_params = [p for p in expected_params if p not in params]
            if missing_params:
                return ServiceResponse.error_res(
                    message=f"💡 LEARNING ERROR: Missing parameters: {', '.join(missing_params)}. Check the API guide or function signature for the correct schema.",
                    error_code="LEARNING_VALIDATION_ERROR",
                    guide={"expected_params": list(expected_params.keys()), "received_params": list(params.keys())}
                )

        # 2. Mentorship and Learning Corrections
        guided = error_analytics_service.get_guided_solution(command_name, "COMMON_ERROR")
        if guided:
            return ServiceResponse.error_res(message=f"💡 MENTORSHIP: {guided}", error_code="LEARNING_PATTERN_FOUND")

        correction = cache_manager.get_learning_correction(ctx.agent_id, command_name, str(params))
        if correction:
            return ServiceResponse.error_res(message=f"Learning Suggestion: {correction}", error_code="LEARNING_PATTERN_FOUND")
        
        return ServiceResponse.success_res(data={"mock": "Simulated"}, message=f"Simulation of {command_name} successful.")

    async def _handle_production_mode(self, command_name: str, ctx: CoreContext, params: Dict[str, Any]):
        handler = self.loader.get_handler(command_name)
        if not handler:
            return ServiceResponse.error_res(f"Command {command_name} not found", "COMMAND_NOT_FOUND")
        
        cmd_metadata = self.loader.get_metadata(command_name)
        is_system = cmd_metadata.get('is_system', False)

        if is_system:
            try:
                # System commands operate on the Core DB and do not require a business session
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: handler(session=None, context=ctx, **params))
                return result if isinstance(result, ServiceResponse) else ServiceResponse.success_res(data=result)
            except Exception as e:
                from core.dispatcher.exceptions import handle_omnicore_exception
                return handle_omnicore_exception(e)

        try:
            async with db_manager.get_session(ctx.app_id, ctx.db_config, ctx.tier) as session:
                # Dynamic Schema Validation based on Command Metadata
                module_name = command_name.split('.')[0]
                cmd_metadata = self.loader.get_metadata(command_name)
                required_tables = cmd_metadata.get('required_tables', [])
                
                from infra.validation.schema_validator import schema_validator
                is_valid, schema_err = schema_validator.validate_module_schema(session, module_name, required_tables)
                if not is_valid:
                    from core.governance.error_analytics_service import error_analytics_service
                    error_analytics_service.track_error(ctx.agent_id, command_name, "SCHEMA_OUTDATED", schema_err.message)
                    return schema_err
                
                is_allowed, error_res = governance_service.validate_access(command_name, ctx, session)
                if not is_allowed:
                    from core.governance.error_analytics_service import error_analytics_service
                    error_analytics_service.track_error(ctx.agent_id, command_name, error_res.error_code, error_res.message)
                    return error_res
                
                # The handler is usually synchronous; we run it in a thread to avoid blocking the loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: handler(session=session, context=ctx, **params))
                return result if isinstance(result, ServiceResponse) else ServiceResponse.success_res(data=result)
        except Exception as e:
            from core.dispatcher.exceptions import handle_omnicore_exception
            from core.governance.error_analytics_service import error_analytics_service
            res = handle_omnicore_exception(e)
            error_analytics_service.track_error(ctx.agent_id, command_name, res.error_code, res.message)
            return res

ai_gateway = AIGateway()
