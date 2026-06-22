import logging
from typing import Any, Dict, cast

from src.core.auth.auth_service import auth_service
from src.core.dispatcher.core_types import ServiceResponse
from src.core.registry.infrastructure_registry import business_registry
from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.AdminService")


class AdminService:
    """
    Service layer for System Administration.
    Provides the logic to manage clients, plans, and tokens.
    Designed to be wrapped as AIGateway commands for the Developer Agent.
    """

    def get_system_metrics(
        self, session=None, context=None, **params
    ) -> ServiceResponse:
        try:
            from src.core.telemetry.telemetry_service import telemetry_service
            from src.infrastructure.db.db_manager import db_manager

            metrics = telemetry_service.get_realtime_metrics()
            infra_status = {
                "active_db_pools": len(db_manager._engines),
                "system_status": (
                    "HEALTHY" if len(db_manager._engines) < 100 else "HIGH_LOAD"
                ),
            }
            return ServiceResponse.success_res(
                data={"telemetry": metrics, "infrastructure": infra_status}
            )
        except Exception as e:
            return ServiceResponse.error_res(
                f"Failed to fetch metrics: {str(e)}", "METRICS_ERROR"
            )

    def onboard_client(self, session=None, context=None, **params) -> ServiceResponse:
        try:
            business_id = business_registry.register_business(
                owner_id=params["owner_id"],
                business_name=params["app_name"],
                plan=params.get("tier", "FREE"),
            )
            return ServiceResponse.success_res(
                data={"business_id": business_id},
                message=f"Business {params['app_name']} onboarded.",
            )
        except Exception as e:
            return ServiceResponse.error_res(
                f"Onboarding failed: {str(e)}", "ONBOARD_ERROR"
            )

    def update_client_tier(
        self, session=None, context=None, **params
    ) -> ServiceResponse:
        business_id = params.get("business_id")
        tier = params.get("tier")
        if not business_id or not tier:
            return ServiceResponse.error_res(
                "Missing business_id or tier", "MISSING_PARAMS"
            )

        success = business_registry.update_app_tier(business_id, tier)
        if not success:
            return ServiceResponse.error_res(
                "Failed to update tier", "TIER_UPDATE_ERROR"
            )
        return ServiceResponse.success_res(
            message=f"Client {business_id} updated to {tier}."
        )

    def get_app_details(self, session=None, context=None, **params) -> ServiceResponse:
        business_id = params.get("business_id")
        if not business_id:
            return ServiceResponse.error_res("Missing business_id", "MISSING_PARAMS")

        app = business_registry.get_app_by_id(business_id)
        if not app:
            return ServiceResponse.error_res("Business not found", "APP_NOT_FOUND")
        return ServiceResponse.success_res(data=app)

    def list_apps(self, session=None, context=None, **params) -> ServiceResponse:
        try:
            apps = (
                core_db_manager.execute_raw("SELECT id, name, owner_id FROM apps")
                .mappings()
                .all()
            )
            return ServiceResponse.success_res(data=[dict(a) for a in apps])
        except Exception as e:
            return ServiceResponse.error_res(
                f"Failed to list apps: {str(e)}", "LIST_APPS_ERROR"
            )

    def generate_client_token(
        self, session=None, context=None, **params
    ) -> ServiceResponse:
        # Simplification: Agents removed, use owner_id directly
        business_id = params.get("business_id")
        token_name = params.get("token_name")
        user_id = params.get("user_id")

        if not all([business_id, token_name, user_id]):
            return ServiceResponse.error_res(
                "Missing business_id, token_name, or user_id", "MISSING_PARAMS"
            )

        return auth_service.create_api_token(
            session=session,
            user_id=cast(str, user_id),
            agent_id=cast(str, business_id),  # Reusing agent_id field as business_id
            token_name=cast(str, token_name),
        )

    def create_custom_plan(self, params: Dict[str, Any]) -> ServiceResponse:
        try:
            core_db_manager.execute_raw(
                "INSERT INTO governance_tiers (tier_name, level) VALUES (:name, :level)",
                {"name": params["tier_name"].upper(), "level": params["level"]},
            )
            from src.core.governance.governance_service import governance_service

            governance_service.clear_tier_cache()
            return ServiceResponse.success_res(
                message=f"Plan {params['tier_name']} created."
            )
        except Exception as e:
            return ServiceResponse.error_res(
                f"Plan creation failed: {str(e)}", "PLAN_ERROR"
            )

    def map_command_to_plan(
        self, session=None, context=None, **params
    ) -> ServiceResponse:
        try:
            core_db_manager.execute_raw(
                """
                INSERT INTO governance_commands (command_name, min_tier) 
                VALUES (:cmd, :tier) 
                ON CONFLICT(command_name) DO UPDATE SET min_tier = :tier
                """,
                {"cmd": params["command_name"], "tier": params["min_tier"].upper()},
            )
            return ServiceResponse.success_res(
                message=f"Command {params['command_name']} mapped to {params['min_tier']}."
            )
        except Exception as e:
            return ServiceResponse.error_res(f"Mapping failed: {str(e)}", "MAP_ERROR")


# Singleton
admin_service = AdminService()
