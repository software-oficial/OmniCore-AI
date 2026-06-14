import importlib
import logging
import os
import sys
import time
from typing import Dict, Any, Callable, Optional
from config.settings import config

logger = logging.getLogger("OmniCore.ModuleLoader")

class ModuleLoader:
    """
    Implements Dynamic Module Loading and Hot-Swapping.
    Allows updating business logic in /modules without restarting the API.
    """
    def __init__(self, modules_dir: str = "modules"):
        self.modules_dir = modules_dir
        self._loaded_modules: Dict[str, Any] = {}
        self._command_registry: Dict[str, Dict[str, Any]] = {}

    def load_module(self, module_name: str):
        """
        Dynamically loads or reloads a module from the filesystem.
        Automatically discovers commands decorated with @command.
        """
        module_path = f"modules.{module_name}"
        try:
            if module_path in sys.modules:
                logger.info(f"♻️ Hot-Swapping module: {module_name}")
                module = importlib.reload(sys.modules[module_path])
            else:
                logger.info(f"📦 Loading module: {module_name}")
                module = importlib.import_module(module_path)

            self._loaded_modules[module_name] = module

            # --- AUTO-DISCOVERY LOGIC ---
            # Scan the module for functions decorated with @command
            commands_found = 0
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and getattr(attr, "_is_omnicore_command", False):
                    cmd_name = getattr(attr, "_command_name")

                    # Register the function in the master registry
                    self._command_registry[cmd_name] = {
                        "handler": attr,
                        "description": getattr(attr, "_command_description"),
                        "params_schema": getattr(attr, "_command_params_schema"),
                        "registered_at": time.time(),
                        "is_system": getattr(attr, "_command_is_system")
                    }
                    commands_found += 1

            logger.info(f"✅ Module {module_name} loaded. {commands_found} commands auto-discovered.")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load module {module_name}: {e}")
            return False

    def reload_all(self):
        """Reloads all currently tracked modules."""
        for module_name in list(self._loaded_modules.keys()):
            self.load_module(module_name)
        logger.info("♻️ All modules have been hot-swapped.")

    def get_handler(self, command_name: str) -> Optional[Callable]:
        """Retrieves the handler for a specific command, handling both legacy and metadata formats."""
        entry = self._command_registry.get(command_name)
        if not entry:
            return None
        
        if isinstance(entry, dict):
            return entry.get('handler')
        
        return entry if callable(entry) else None

    def get_metadata(self, command_name: str) -> Dict[str, Any]:
        """Retrieves metadata (like required tables) for a specific command."""
        entry = self._command_registry.get(command_name)
        return entry if entry else {}

# Singleton
module_loader = ModuleLoader()
