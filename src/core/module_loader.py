import importlib
import logging
import sys
import time
from typing import Any, Callable, Dict, Optional

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
        Dynamically loads all sub-modules within a domain package.
        Uses pkgutil to discover and import all modules in the domain.
        """
        import pkgutil

        domain_package_path = f"{self.modules_dir}.{module_name}"
        try:
            # Import the domain package first
            domain_pkg = importlib.import_module(domain_package_path)
            package_path = (
                domain_pkg.__path__ if hasattr(domain_pkg, "__path__") else None
            )

            if not package_path:
                logger.error(
                    f"❌ {domain_package_path} is not a package or has no path."
                )
                return False

            commands_found = 0
            # Walk through all sub-modules in the package
            for loader, name, is_pkg in pkgutil.walk_packages(
                package_path, domain_package_path + "."
            ):
                module_path = name
                try:
                    if module_path in sys.modules:
                        module = importlib.reload(sys.modules[module_path])
                    else:
                        module = importlib.import_module(module_path)

                    self._loaded_modules[module_path] = module

                    # Scan the module for commands
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # 1. Module-level functions
                        if callable(attr) and getattr(
                            attr, "_is_omnicore_command", False
                        ):
                            # Ensure it's not an unbound method of a class
                            if (
                                not hasattr(attr, "__qualname__")
                                or "." not in attr.__qualname__
                            ):
                                self._register_command(attr)
                                commands_found += 1

                        # 2. Instance methods (singletons)
                        elif hasattr(attr, "__dict__") or hasattr(attr, "__slots__"):
                            # We only care about objects that are actually instances of a class
                            # to find bound methods.
                            for member_name in dir(attr):
                                if member_name.startswith("__"):
                                    continue
                                member = getattr(attr, member_name)
                                if callable(member) and getattr(
                                    member, "_is_omnicore_command", False
                                ):
                                    # Check if it's a bound method (has __self__)
                                    if hasattr(member, "__self__"):
                                        self._register_command(member)
                                        commands_found += 1

                    logger.info(
                        f"✅ Loaded {module_path}. Found {commands_found} commands."
                    )
                except Exception as e:
                    logger.error(f"❌ Failed to load sub-module {module_path}: {e}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to load domain package {domain_package_path}: {e}")
            return False

    def _register_command(self, handler: Callable):
        """Helper to register a handler in the master registry."""
        cmd_name = getattr(handler, "_command_name")
        self._command_registry[cmd_name] = {
            "handler": handler,
            "description": getattr(handler, "_command_description"),
            "params_model": getattr(handler, "_command_params_model"),
            "registered_at": time.time(),
            "is_system": getattr(handler, "_command_is_system"),
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
            return entry.get("handler")

        return entry if callable(entry) else None

    def get_metadata(self, command_name: str) -> Dict[str, Any]:
        """Retrieves metadata (like required tables) for a specific command."""
        entry = self._command_registry.get(command_name)
        return entry if entry else {}


# Singleton
module_loader = ModuleLoader()
