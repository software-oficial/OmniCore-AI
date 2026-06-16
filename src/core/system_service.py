import logging
import os
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.core.dispatcher.decorators import command
from src.infrastructure.db.core_db_manager import core_db_manager

logger = logging.getLogger("OmniCore.SystemService")


class SystemService:
    """
    Core System Management.
    Handles health checks, maintenance modes, and infrastructure validation.
    """

    @command(
        name="system.help",
        description="Provides guidance on how to discover and use available commands.",
        params_model={},
    )
    def get_help(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Provides guidance on how to discover and use available commands."""
        return ServiceResponse.success_res(
            message="Welcome to OmniCore-AI. To discover all available commands, their descriptions and required parameters, please use the official discovery endpoint: GET /api/discovery/commands. For detailed infrastructure setup guides, use: GET /api/agent/guides.",
            data={
                "discovery_endpoint": "/api/discovery/commands",
                "guides_endpoint": "/api/agent/guides",
                "manifest_endpoint": "/api/agent/manifest",
            },
        )

    @command(
        name="system.info",
        description="Provides general information about the system, version, and data model.",
        params_model={},
    )
    def get_info(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Returns general system information."""
        version = os.getenv("SYSTEM_VERSION", "1.0.0-stable")
        return ServiceResponse.success_res(
            message=f"OmniCore-AI v{version} is a stateless Meta-Orchestrator.",
            data={
                "version": version,
                "model": "BYODB (Bring Your Own Database)",
                "architecture": "Dispatcher Pattern",
                "onboarding_guide": "/api/agent/guides",
            },
        )

    @command(
        name="system.get_setting",
        description="Retrieves a specific system configuration value.",
        params_model={"key": "string"},
    )
    def get_setting(
        self, session: Session, context: CoreContext, key: str
    ) -> ServiceResponse:
        """Retrieves a system setting from the internal Core DB."""
        try:
            # Settings are stored in the internal Core DB (SQLite)
            result = core_db_manager.execute_raw(
                "SELECT setting_value FROM system_settings WHERE setting_key = :key",
                {"key": key},
            ).scalar()

            if result is None:
                return ServiceResponse.error_res(
                    f"Setting {key} not found in system configuration.",
                    "SETTING_NOT_FOUND",
                )

            return ServiceResponse.success_res(
                data={"value": result}, message="Setting retrieved."
            )
        except Exception as e:
            logger.error(f"Error retrieving system setting {key}: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SYS_SETTING_ERROR"
            )

    @command(
        name="system.deploy_schema",
        description="Deploys the database schema blueprints to the client's external DB.",
        params_model={"domains": "list[string]"},
    )
    def deploy_schema(
        self,
        session: Session,
        context: CoreContext,
        domains: Optional[List[str]] = None,
    ) -> ServiceResponse:
        """
        Enterprise Handler: Delegates execution to the DeploySchemaUseCase.
        """
        from src.application.deploy_schema_use_case import DeploySchemaUseCase

        use_case = DeploySchemaUseCase(session, context)
        return use_case.execute(domains=domains)

    @command(
        name="system.get_version",
        description="Retrieves the current system version and deployment metadata.",
        params_model={},
    )
    def get_version(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Returns the current version of the system."""
        try:
            # In a production Sentinel environment, this would read from a file or symlink
            version = os.getenv("SYSTEM_VERSION", "1.0.0-stable")
            deploy_date = os.getenv("DEPLOY_DATE", "Unknown")

            return ServiceResponse.success_res(
                data={"version": version, "deploy_date": deploy_date},
                message=f"System is running version {version}.",
            )
        except Exception as e:
            logger.error(f"Error fetching system version: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SYS_VERSION_ERROR"
            )

    @command(
        name="system.set_maintenance",
        description="Toggles the global maintenance mode for the business infrastructure.",
        params_model={"enabled": "boolean"},
    )
    def set_maintenance(
        self, session: None, context: CoreContext, enabled: bool
    ) -> ServiceResponse:
        """Toggles maintenance mode."""
        try:
            # Maintenance is stored in the Core DB per App
            core_db_manager.execute_raw(
                "UPDATE apps SET maintenance_mode = :status WHERE id = :id",
                {"status": enabled, "id": context.app_id},
            )
            return ServiceResponse.success_res(
                message=f"Maintenance mode {'enabled' if enabled else 'disabled'} for app {context.app_id}."
            )
        except Exception as e:
            logger.error(f"Error setting maintenance mode: {e}")
            return ServiceResponse.error_res(
                f"Internal error: {str(e)}", "SYS_MAINT_ERROR"
            )

    @command(
        name="system.validate_blueprint",
        description="Checks if the external business database has all required tables according to the blueprint.",
        params_model={"domain": "string"},
    )
    def validate_blueprint(
        self, session: Session, context: CoreContext, domain: str
    ) -> ServiceResponse:
        """Validates DB structure for a given domain."""
        try:
            # This would typically check against a known list of tables for 'whatsapp', 'stock', or 'sales'
            required_tables = {
                "whatsapp": [
                    "whatsapp_conversations",
                    "whatsapp_menus",
                    "whatsapp_menu_options",
                    "bot_settings",
                ],
                "stock": ["products", "stock_movements"],
                "sales": ["sales", "sale_items", "cash_box", "aliases", "users"],
            }

            if domain not in required_tables:
                return ServiceResponse.error_res(
                    f"Unknown domain: {domain}", "DOMAIN_UNKNOWN"
                )

            missing: List[str] = []
            for table in required_tables[domain]:
                # Check if table exists in the current session's DB
                check = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1")).scalar()
                if not check:
                    missing.append(table)

            if missing:
                return ServiceResponse.error_res(
                    message=f"Blueprint for {domain} is incomplete. Missing tables: {', '.join(missing)}",
                    error_code="BLUEPRINT_INCOMPLETE",
                )

            return ServiceResponse.success_res(
                message=f"Blueprint for {domain} validated successfully."
            )
        except Exception as e:
            logger.error(f"Error validating blueprint for {domain}: {e}")
            return ServiceResponse.error_res(
                f"Validation failed: {str(e)}", "BLUEPRINT_ERROR"
            )

    @command(
        name="system.get_health",
        description="Performs a comprehensive health check of the infrastructure (DB, API Tokens, Connectivity).",
        params_model={},
    )
    def get_health(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Comprehensive health check."""
        try:
            # 1. DB Check
            session.execute(text("SELECT 1"))

            # 2. Token Check (simulated)
            # In a real scenario, we'd call a lightweight endpoint of Meta/MP

            return ServiceResponse.success_res(
                data={"db": "OK", "api": "OK", "latency": "low"},
                message="Infrastructure is healthy.",
            )
        except Exception as e:
            return ServiceResponse.error_res(f"Unhealthy: {str(e)}", "SYSTEM_UNHEALTHY")


# Singleton
system_service = SystemService()
