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
    def __init__(self, modules_dir: str = "src.domains"):
        self.modules_dir = modules_dir
        self._loaded_modules: Dict[str, Any] = {}
        self._command_registry: Dict[str, Dict[str, Any]] = {}

    def load_module(self, module_name: str):
        """
        Dynamically loads modules from a domain directory.
        Searches for all .py files in the domain folder and registers commands.
        """
        # Convert domain name (e.g., 'stock') to a path (e.g., 'src/domains/stock')
        domain_path = f"src/domains/{module_name}"
        try:
            import os
            if not os.path.exists(domain_path):
                logger.error(f"❌ Domain directory not found: {domain_path}")
                return False

            # Find all .py files in the domain directory (excluding __init__.py)
            files = [f for f in os.listdir(domain_path) if f.endswith('.py') and f != '__init__.py']
            
            for file in files:
                # Convert filename to module path (e.g., 'stock_service.py' -> 'src.domains.stock.stock_service')
                module_short_name = file[:-3]
                module_path = f"{self.modules_dir}.{module_name}.{module_short_name}"
                
                try:
                    if module_path in sys.modules:
                        logger.info(f"♻️ Hot-Swapping module: {module_path}")
                        module = importlib.reload(sys.modules[module_path])
                    else:
                        logger.info(f"📦 Loading module: {module_path}")
                        module = importlib.import_module(module_path)

                    self._loaded_modules[module_path] = module

                    # --- ENHANCED AUTO-DISCOVERY LOGIC ---
                    commands_found = 0
                    # 1. Scan module attributes for callables (functions or objects)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # Handle module-level functions
                        if callable(attr) and getattr(attr, "_is_omnicore_command", False):
                            self._register_command(attr)
                            commands_found += 1
                        
                        # Handle object methods (singletons)
                        elif hasattr(attr, "__dict__") or hasattr(attr, "__slots__"):
                            # Scan the object's methods
                            for member_name in dir(attr):
                                member = getattr(attr, member_name)
                                if callable(member) and getattr(member, "_is_omnicore_command", False):
                                    self._register_command(member)
                                    commands_found += 1

                    logger.info(f"✅ Module {module_path} loaded. {commands_found} commands discovered.")
                except Exception as e:
                    logger.error(f"❌ Failed to load sub-module {module_path}: {e}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to load domain {module_name}: {e}")
            return False

    def _register_command(self, handler: Callable):
        """Helper to register a handler in the master registry."""
        cmd_name = getattr(handler, "_command_name")
        self._command_registry[cmd_name] = {
            "handler": handler,
            "description": getattr(handler, "_command_description"),
            "params_schema": getattr(handler, "_command_params_schema"),
            "registered_at": time.time(),
            "is_system": getattr(handler, "_command_is_system")
        }

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
