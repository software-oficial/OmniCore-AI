
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from src.core.registry.infrastructure_registry import business_registry
from src.infrastructure.logging.omni_logger import get_logger

router = APIRouter(prefix="/api/business", tags=["Business"])
engine_logger = get_logger("OmniCore.AgentRoute")


class RegisterRequest(BaseModel):
    name: str = Field(..., description="Business name")


@router.post("/register")
async def register_business(
    request: RegisterRequest, authorization: str = Header(None)
):
    """
    Registers a new business directly for the authenticated user.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = authorization.replace("Bearer ", "")

    try:
        from config.settings import config

        db_config = {
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "dbname": config.DB_NAME,
        }

        # Registrar negocio directamente mediante BusinessRegistry
        business_id = business_registry.register_business(
            owner_id=user_id, name=request.name, db_config=db_config
        )

        return {
            "success": True,
            "business_id": business_id,
            "message": "Negocio creado exitosamente.",
        }

    except Exception:
        engine_logger.error("Project creation error", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create project.")
