from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from src.core.auth.auth_service import auth_service
from src.core.registry.infrastructure_registry import infrastructure_registry
from src.infrastructure.db.core_db_manager import core_db_manager

router = APIRouter(prefix="/api/dev", tags=["Developer Control Plane"])


# --- Request Models ---
class DBConfig(BaseModel):
    host: str = Field(..., json_schema_extra={"example": "localhost"})
    port: int = Field(..., json_schema_extra={"example": 5432})
    user: str = Field(..., json_schema_extra={"example": "postgres"})
    password: str = Field(..., json_schema_extra={"example": "password"})
    dbname: str = Field(..., json_schema_extra={"example": "omnicore_biz"})


class OnboardClientRequest(BaseModel):
    agent_id: str = Field(..., description="Unique ID for the AI Agent")
    app_name: str = Field(
        ..., description="Human-readable name of the client application"
    )
    db_config: DBConfig = Field(
        ..., description="Database connection details for the external business DB"
    )
    tier: str = Field(
        "FREE", description="Initial subscription tier (e.g., FREE, GOLD, PLATINUM)"
    )


class CreatePlanRequest(BaseModel):
    tier_name: str = Field(
        ...,
        json_schema_extra={"example": "Plan Oro"},
        description="Name of the subscription plan",
    )
    level: int = Field(
        ...,
        json_schema_extra={"example": 5},
        description="Hierarchy level of the plan (higher = more privileges)",
    )


class MapCommandPlanRequest(BaseModel):
    command_name: str = Field(
        ...,
        json_schema_extra={"example": "stock.import.commit"},
        description="The registered command name",
    )
    min_tier: str = Field(
        ...,
        json_schema_extra={"example": "PLAN_ORO"},
        description="The minimum tier required to execute this command",
    )


class GenerateClientTokenRequest(BaseModel):
    token_name: str = Field(
        ...,
        json_schema_extra={"example": "Production-Token-1"},
        description="Name for the generated token",
    )
    user_id: str = Field(..., description="ID of the user who owns this token")


# --- Dependencies ---
async def verify_dev_access(authorization: str = Header(None)):
    """
    Validates the Master Developer Key.
    """
    import os

    master_key = os.getenv("OMNICORE_MASTER_KEY", "admin-secret-key")
    if authorization != master_key and authorization != f"Bearer {master_key}":
        raise HTTPException(
            status_code=403, detail="Forbidden: Master Developer Key required."
        )
    return True


# --- Endpoints ---


@router.post("/clients/onboard", dependencies=[Depends(verify_dev_access)])
async def onboard_client(payload: OnboardClientRequest):
    """
    Onboards a new supermarket/client for the developer.
    """
    try:
        app_id = infrastructure_registry.register_app(
            agent_id=payload.agent_id,
            app_name=payload.app_name,
            db_config=payload.db_config.model_dump(),
            tier=payload.tier,
        )
        return {
            "success": True,
            "app_id": app_id,
            "message": f"Client {payload.app_name} onboarded.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/clients/{app_id}/deploy", dependencies=[Depends(verify_dev_access)])
async def deploy_client_schema(app_id: str):
    """
    Triggers the deployment of blueprints to the client's DB.
    """
    from src.core.dispatcher.core_types import CoreContext
    from src.infrastructure.db.db_manager import db_manager

    app_info = infrastructure_registry.get_app_by_id(app_id)
    if not app_info:
        raise HTTPException(status_code=404, detail="App not found")

    ctx = CoreContext(
        agent_id="dev_admin",
        app_id=app_id,
        dev_id="SYSTEM",
        mode="PRODUCTION",
        db_config=app_info["db_config"],
        tier=app_info["tier"],
    )

    # Direct execution via system_service within a DB session
    from src.core.system_service import system_service

    async with db_manager.get_session(
        app_id, app_info["db_config"], app_info["tier"]
    ) as session:
        result = await system_service.deploy_schema(session, ctx)
        return result.to_dict()


@router.patch("/clients/{app_id}/tier", dependencies=[Depends(verify_dev_access)])
async def update_client_tier(app_id: str, tier: str):
    """
    Updates the subscription tier for a specific client.
    """
    success = infrastructure_registry.update_app_tier(app_id, tier)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update tier.")
    return {"success": True, "message": f"Client {app_id} updated to {tier}."}


@router.post("/clients/{app_id}/tokens", dependencies=[Depends(verify_dev_access)])
async def generate_client_token(app_id: str, payload: GenerateClientTokenRequest):
    """
    Generates a production token for a client's agent.
    """

    res = core_db_manager.execute_raw(
        "SELECT agent_id FROM agent_app_mapping WHERE app_id = :aid", {"aid": app_id}
    ).fetchone()
    if not res:
        raise HTTPException(status_code=404, detail="No agent mapped to this app")

    agent_id = res[0]
    with core_db_manager.get_session() as session:
        response = auth_service.create_api_token(
            session=session,
            user_id=payload.user_id,
            agent_id=agent_id,
            token_name=payload.token_name,
        )
    return response.to_dict()


@router.get("/clients", dependencies=[Depends(verify_dev_access)])
async def list_clients():
    """Lists all apps managed by the system."""

    apps = (
        core_db_manager.execute_raw("SELECT id, name, owner_id FROM apps")
        .mappings()
        .all()
    )
    return {"success": True, "data": [dict(a) for a in apps]}


@router.post("/plans", dependencies=[Depends(verify_dev_access)])
async def create_plan(payload: CreatePlanRequest):
    """
    Creates a new subscription plan with a specific hierarchy level.
    """
    from src.core.governance.governance_service import governance_service

    try:
        core_db_manager.execute_raw(
            "INSERT INTO governance_tiers (tier_name, level) VALUES (:name, :level)",
            {"name": payload.tier_name.upper(), "level": payload.level},
        )
        governance_service.clear_tier_cache()
        return {
            "success": True,
            "message": f"Plan {payload.tier_name} created successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans", dependencies=[Depends(verify_dev_access)])
async def list_plans():
    """Lists all available subscription plans and their levels."""

    plans = (
        core_db_manager.execute_raw(
            "SELECT tier_name, level FROM governance_tiers ORDER BY level DESC"
        )
        .mappings()
        .all()
    )
    return {"success": True, "data": [dict(p) for p in plans]}


@router.post("/plans/commands", dependencies=[Depends(verify_dev_access)])
async def map_command_to_plan(payload: MapCommandPlanRequest):
    """
    Maps a specific system command to a minimum required plan.
    """

    try:
        # Upsert the command requirement
        core_db_manager.execute_raw(
            """
            INSERT INTO governance_commands (command_name, min_tier) 
            VALUES (:cmd, :tier) 
            ON CONFLICT(command_name) DO UPDATE SET min_tier = :tier
            """,
            {"cmd": payload.command_name, "tier": payload.min_tier.upper()},
        )
        return {
            "success": True,
            "message": f"Command {payload.command_name} now requires {payload.min_tier}.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans/commands", dependencies=[Depends(verify_dev_access)])
async def list_command_requirements():
    """Lists all commands and their required minimum tiers."""

    reqs = (
        core_db_manager.execute_raw(
            "SELECT command_name, min_tier FROM governance_commands"
        )
        .mappings()
        .all()
    )
    return {"success": True, "data": [dict(r) for r in reqs]}
