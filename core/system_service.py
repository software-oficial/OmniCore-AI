import logging
from typing import Dict, Any
from sqlalchemy import text
from core.dispatcher.core_types import CoreContext, ServiceResponse
from infra.db.db_manager import db_manager
from infra.blueprint_manager import blueprint_manager

logger = logging.getLogger("OmniCore.SystemService")

class SystemService:
    """
    Handles system-level operations, including infrastructure deployment 
    and schema synchronization for external databases.
    """
    
    async def deploy_schema(self, session, context: CoreContext, **params) -> ServiceResponse:
        """
        Deploys the necessary database schema (Blueprints) to the client's external DB.
        """
        app_id = context.app_id
        logger.info(f"🚀 Starting schema deployment for App: {app_id}")
        
        try:
            # 1. Get all available blueprints
            blueprints = blueprint_manager.get_all_blueprints()
            if not blueprints:
                return ServiceResponse.error_res("No blueprints found to deploy", "NO_BLUEPRINTS")
            
            deployed_modules = []
            
            # 2. Execute each blueprint in the client's DB session
            for module, sql in blueprints.items():
                logger.info(f"📦 Deploying blueprint for module: {module}")
                # Blueprints can contain multiple statements; execute them sequentially
                for statement in sql.strip().split(';'):
                    if statement.strip():
                        session.execute(text(statement))
                deployed_modules.append(module)
            
            session.commit()
            
            return ServiceResponse.success_res(
                data={"deployed_modules": deployed_modules},
                message=f"Successfully deployed schemas for: {', '.join(deployed_modules)}"
            )
            
        except Exception as e:
            logger.error(f"❌ Schema deployment failed for {app_id}: {e}")
            return ServiceResponse.error_res(f"Deployment failed: {str(e)}", "DEPLOYMENT_ERROR")

# Singleton
system_service = SystemService()
