import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("OmniCore.BlueprintManager")


class BlueprintManager:
    """
    Manages the delivery of SQL blueprints for external database setup.
    Enables 'Zero-Touch' infrastructure deployment for developers.
    """

    def __init__(self, modules_path: str = "modules"):
        self.modules_path = modules_path

    def get_module_blueprint(self, module_name: str) -> Optional[str]:
        """Reads the blueprint.sql file for a specific module."""
        file_path = os.path.join(self.modules_path, module_name, "blueprint.sql")

        if not os.path.exists(file_path):
            logger.warning(f"Blueprint not found for module: {module_name}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading blueprint for {module_name}: {e}")
            return None

    def get_all_blueprints(
        self, requested_modules: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Returns a map of module names to their SQL content.
        If requested_modules is None, returns all available blueprints.
        """
        blueprints = {}

        # Determine which modules to process
        if requested_modules:
            modules_to_process = requested_modules
        else:
            # Scan modules directory for folders containing blueprint.sql
            modules_to_process = [
                d
                for d in os.listdir(self.modules_path)
                if os.path.isdir(os.path.join(self.modules_path, d))
                and os.path.exists(os.path.join(self.modules_path, d, "blueprint.sql"))
            ]

        for module in modules_to_process:
            content = self.get_module_blueprint(module)
            if content:
                blueprints[module] = content

        return blueprints


# Singleton
blueprint_manager = BlueprintManager()
