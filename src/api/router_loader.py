import importlib
import inspect
import logging
import pkgutil
from typing import List

from fastapi import APIRouter

logger = logging.getLogger("OmniCore.RouterLoader")


def load_routers(package_name: str = "src.api.routes") -> List[APIRouter]:
    """
    Dynamically scans the package and registers all FastAPI Routers found in modules.
    """
    routers = []
    package = importlib.import_module(package_name)

    for _, name, is_pkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        if is_pkg:
            continue

        try:
            module = importlib.import_module(name)
            for _, obj in inspect.getmembers(module):
                if isinstance(obj, APIRouter):
                    routers.append(obj)
                    logger.info(f"✅ Auto-registered router from: {name}")
        except Exception as e:
            logger.error(f"❌ Failed to load router from {name}: {e}")

    return routers
