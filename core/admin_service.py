import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
from core.dispatcher.core_types import ServiceResponse
from core.registry.infrastructure_registry import infrastructure_registry
from core.auth.auth_service import auth_service
from infra.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.AdminService")

class AdminService:
    """
    Service layer for System Administration.
    Provides the logic to manage clients, plans, and tokens.
    Designed to be wrapped as AIGateway commands for the Developer Agent.
    """

    def get_system_metrics(self, session=None, context=None, **params) -> ServiceResponse:
        try:
            from core.telemetry.telemetry_service import telemetry_service
            from infra.db.db_manager import db_manager
            metrics = telemetry_service.get_realtime_metrics()
            infra_status = {
                "active_db_pools": len(db_manager._engines),
                "system_status": "HEALTHY" if len(db_manager._engines) < 100 else "HIGH_LOAD"
            }
            return ServiceResponse.success_res(data={"telemetry": metrics, "infrastructure": infra_status})
        except Exception as e:
            return ServiceResponse.error_res(f"Failed to fetch metrics: {str(e)}", "METRICS_ERROR")

    def onboard_client(self, session=None, context=None, **params) -> ServiceResponse:
        try:
            app_id = infrastructure_registry.register_app(
                agent_id=params['agent_id'],
                app_name=params['app_name'],
                db_config=params['db_config'],
                tier=params.get('tier', 'FREE')
            )
            return ServiceResponse.success_res(data={"app_id": app_id}, message=f"Client {params['app_name']} onboarded.")
        except Exception as e:
            return ServiceResponse.error_res(f"Onboarding failed: {str(e)}", "ONBOARD_ERROR")

    def update_client_tier(self, session=None, context=None, **params) -> ServiceResponse:
        app_id = params.get('app_id')
        tier = params.get('tier')
        if not app_id or not tier:
            return ServiceResponse.error_res("Missing app_id or tier", "MISSING_PARAMS")
        
        success = infrastructure_registry.update_app_tier(app_id, tier)
        if not success:
            return ServiceResponse.error_res("Failed to update tier", "TIER_UPDATE_ERROR")
        return ServiceResponse.success_res(message=f"Client {app_id} updated to {tier}.")

    def get_app_details(self, session=None, context=None, **params) -> ServiceResponse:
        app_id = params.get('app_id')
        if not app_id:
            return ServiceResponse.error_res("Missing app_id", "MISSING_PARAMS")
        
        app = infrastructure_registry.get_app_by_id(app_id)
        if not app:
            return ServiceResponse.error_res("Application not found", "APP_NOT_FOUND")
        return ServiceResponse.success_res(data=app)

    def list_apps(self, session=None, context=None, **params) -> ServiceResponse:
        try:
            apps = core_db_manager.execute_raw("SELECT id, name, owner_id FROM apps").mappings().all()
            return ServiceResponse.success_res(data=[dict(a) for a in apps])
        except Exception as e:
            return ServiceResponse.error_res(f"Failed to list apps: {str(e)}", "LIST_APPS_ERROR")

    def generate_client_token(self, session=None, context=None, **params) -> ServiceResponse:
        app_id = params.get('app_id')
        token_name = params.get('token_name')
        user_id = params.get('user_id')
        if not all([app_id, token_name, user_id]):
            return ServiceResponse.error_res("Missing app_id, token_name, or user_id", "MISSING_PARAMS")

        p = params if params is not None else {}
        app_id = p.get('app_id')
        token_name = p.get('token_name')
        user_id = p.get('user_id')
        if not all([app_id, token_name, user_id]):
            return ServiceResponse.error_res("Missing app_id, token_name, or user_id", "MISSING_PARAMS")


        app_id = params.get('app_id')
        token_name = params.get('token_name')
        user_id = params.get('user_id')
        if not all([app_id, token_name, user_id]):
            return ServiceResponse.error_res("Missing app_id, token_name, or user_id", "MISSING_PARAMS")
            
        res = core_db_manager.execute_raw("SELECT agent_id FROM agent_app_mapping WHERE app_id = :aid", {"aid": app_id}).fetchone()
        if not res:
            return ServiceResponse.error_res("No agent mapped to this app", "AGENT_NOT_FOUND")
        
        agent_id = res[0]
        return auth_service.create_api_token(user_id=user_id, agent_id=agent_id, token_name=token_name)

    def create_custom_plan(self, params: Dict[str, Any]) -> ServiceResponse:
        try:
            core_db_manager.execute_raw(
                "INSERT INTO governance_tiers (tier_name, level) VALUES (:name, :level)",
                {"name": params['tier_name'].upper(), "level": params['level']}
            )
            from core.governance.governance_service import governance_service
            governance_service.clear_tier_cache()
            return ServiceResponse.success_res(message=f"Plan {params['tier_name']} created.")
        except Exception as e:
            return ServiceResponse.error_res(f"Plan creation failed: {str(e)}", "PLAN_ERROR")

    def map_command_to_plan(self, session=None, context=None, **params) -> ServiceResponse:
        try:
            core_db_manager.execute_raw(
                """
                INSERT INTO governance_commands (command_name, min_tier) 
                VALUES (:cmd, :tier) 
                ON CONFLICT(command_name) DO UPDATE SET min_tier = :tier
                """,
                {"cmd": params['command_name'], "tier": params['min_tier'].upper()}
            )
            return ServiceResponse.success_res(message=f"Command {params['command_name']} mapped to {params['min_tier']}.")
        except Exception as e:
            return ServiceResponse.error_res(f"Mapping failed: {str(e)}", "MAP_ERROR")


# Singleton
admin_service = AdminService()
