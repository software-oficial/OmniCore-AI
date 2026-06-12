import importlib
import logging
import os
import sys
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
        """
        module_path = f"modules.{module_name}"
        try:
            if module_path in sys.modules:
                # Hot-Swap: Reload the module if it's already loaded
                logger.info(f"♻️ Hot-Swapping module: {module_name}")
                module = importlib.reload(sys.modules[module_path])
            else:
                # Fresh load
                logger.info(f"📦 Loading module: {module_name}")
                module = importlib.import_module(module_path)
            
            self._loaded_modules[module_name] = module
            
            # After loading, we must re-register commands from the module
            # We assume each module has a 'register_commands' function
            if hasattr(module, 'register_commands'):
                module.register_commands(self._command_registry)
                logger.info(f"✅ Module {module_name} commands registered.")
            
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
