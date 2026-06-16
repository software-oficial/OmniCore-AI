import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.core.dispatcher.core_types import CoreContext, ServiceResponse
from src.infrastructure.blueprint_manager import blueprint_manager
from src.infrastructure.repositories.schema_repository import SchemaRepository

logger = logging.getLogger("OmniCore.DeploySchemaUseCase")


class DeploySchemaUseCase:
    """
    Application Layer: Orquestrates the deployment of database blueprints.
    Decoupled from the API and Framework.
    """

    def __init__(self, session: Session, context: CoreContext):
        self.session = session
        self.context = context
        self.repo = SchemaRepository(session)

    def execute(self, domains: Optional[List[str]] = None) -> ServiceResponse:
        """
        Business Logic: Resolves blueprints and applies them via the repository.
        """
        try:
            # Ensure blueprint manager points to the correct domain directory
            blueprint_manager.modules_path = "src/domains"
            blueprints = blueprint_manager.get_all_blueprints(requested_modules=domains)

            if not blueprints:
                return ServiceResponse.error_res(
                    "No blueprints found to deploy for the requested domains.",
                    "NO_BLUEPRINTS",
                )

            executed_domains = []
            for domain, sql in blueprints.items():
                self.repo.execute_blueprint(sql)
                executed_domains.append(domain)

            # Transactional integrity is handled by the Dispatcher/Session Manager
            # But we commit here if we are managing the session manually
            self.session.commit()

            return ServiceResponse.success_res(
                message=f"Successfully deployed blueprints for: {', '.join(executed_domains)}."
            )
        except Exception as e:
            logger.error(f"DeploySchemaUseCase critical failure: {e}")
            return ServiceResponse.error_res(
                f"Deployment failed: {str(e)}", "DEPLOY_ERROR"
            )
