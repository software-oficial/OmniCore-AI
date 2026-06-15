from typing import List, Optional

from fastapi import APIRouter, Query

from src.infrastructure.blueprint_manager import blueprint_manager

router = APIRouter(prefix="/api/infra", tags=["Infrastructure"])


@router.get("/setup")
async def get_setup_blueprints(modules: Optional[List[str]] = Query(None)):
    """
    Delivers the SQL blueprints needed to initialize the developer's external database.
    """
    blueprints = blueprint_manager.get_all_blueprints(requested_modules=modules)
    return {
        "success": True,
        "message": "Database blueprints retrieved successfully.",
        "blueprints": blueprints,
    }
