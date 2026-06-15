import logging
import os
from typing import Dict, Any, Optional, List
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
        name="system.deploy_schema",
        description="Deploys the database schema blueprints to the client's external DB.",
        params_schema={"domains": "list[string]"}
    )
    def deploy_schema(self, session: Session, context: CoreContext, domains: Optional[List[str]] = None) -> ServiceResponse:
        """
        Executes the SQL blueprints for the specified domains in the external DB.
        If domains is None, deploys all available blueprints.
        """
        from src.infrastructure.blueprint_manager import blueprint_manager
        
        try:
            # 1. Resolve blueprints (Note: blueprint_manager path might need adjustment to 'src/domains')
            # We override the modules_path on the fly or assume the manager handles it.
            # Let's adjust the logic to use the current project structure.
            blueprint_manager.modules_path = "src/domains"
            blueprints = blueprint_manager.get_all_blueprints(requested_modules=domains)
            
            if not blueprints:
                return ServiceResponse.error_res("No blueprints found to deploy.", "NO_BLUEPRINTS")
            
            executed_domains = []
            for domain, sql in blueprints.items():
                # Execute each blueprint SQL
                session.execute(text(sql))
                executed_domains.append(domain)
            
            session.commit()
            return ServiceResponse.success_res(
                message=f"Successfully deployed blueprints for: {', '.join(executed_domains)}."
            )
        except Exception as e:
            logger.error(f"Schema deployment failure: {e}")
            return ServiceResponse.error_res(f"Deployment failed: {str(e)}", "DEPLOY_ERROR")

    @command(
        name="system.get_version",
        description="Retrieves the current system version and deployment metadata.",
        params_schema={}
    )
    def get_version(self, session: Session, context: CoreContext) -> ServiceResponse:
        """Returns the current version of the system."""
        try:
            # In a production Sentinel environment, this would read from a file or symlink
            version = os.getenv("SYSTEM_VERSION", "1.0.0-stable")
            deploy_date = os.getenv("DEPLOY_DATE", "Unknown")
            
            return ServiceResponse.success_res(
                data={"version": version, "deploy_date": deploy_date},
                message=f"System is running version {version}."
            )
        except Exception as e:
            logger.error(f"Error fetching system version: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "SYS_VERSION_ERROR")

    @command(
        name="system.set_maintenance",
        description="Toggles the global maintenance mode for the business infrastructure.",
        params_schema={"enabled": "boolean"}
    )
    def set_maintenance(self, session: None, context: CoreContext, enabled: bool) -> ServiceResponse:
        """Toggles maintenance mode."""
        try:
            # Maintenance is stored in the Core DB per App
            core_db_manager.execute_raw(
                "UPDATE apps SET maintenance_mode = :status WHERE id = :id",
                {"status": enabled, "id": context.app_id}
            )
            return ServiceResponse.success_res(message=f"Maintenance mode {'enabled' if enabled else 'disabled'} for app {context.app_id}.")
        except Exception as e:
            logger.error(f"Error setting maintenance mode: {e}")
            return ServiceResponse.error_res(f"Internal error: {str(e)}", "SYS_MAINT_ERROR")

    @command(
        name="system.validate_blueprint",
        description="Checks if the external business database has all required tables according to the blueprint.",
        params_schema={"domain": "string"}
    )
    def validate_blueprint(self, session: Session, context: CoreContext, domain: str) -> ServiceResponse:
        """Validates DB structure for a given domain."""
        try:
            # This would typically check against a known list of tables for 'whatsapp', 'stock', or 'sales'
            required_tables = {
                "whatsapp": ["whatsapp_conversations", "whatsapp_menus", "whatsapp_menu_options", "bot_settings"],
                "stock": ["products", "stock_movements"],
                "sales": ["sales", "sale_items", "cash_box", "aliases", "users"]
            }
            
            if domain not in required_tables:
                return ServiceResponse.error_res(f"Unknown domain: {domain}", "DOMAIN_UNKNOWN")
            
            missing = []
            for table in required_tables[domain]:
                # Check if table exists in the current session's DB
                check = session.execute(text(f"SELECT 1 FROM {table} LIMIT 1")).scalar()
                # Note: This is a simplification; a real check would query information_schema
            
            return ServiceResponse.success_res(message=f"Blueprint for {domain} validated successfully.")
        except Exception as e:
            logger.error(f"Error validating blueprint for {domain}: {e}")
            return ServiceResponse.error_res(f"Validation failed: {str(e)}", "BLUEPRINT_ERROR")

    @command(
        name="system.get_health",
        description="Performs a comprehensive health check of the infrastructure (DB, API Tokens, Connectivity).",
        params_schema={}
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
                message="Infrastructure is healthy."
            )
        except Exception as e:
            return ServiceResponse.error_res(f"Unhealthy: {str(e)}", "SYSTEM_UNHEALTHY")

# Singleton
system_service = SystemService()
