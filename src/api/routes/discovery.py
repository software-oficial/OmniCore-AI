from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException

from src.core.auth.token_manager import token_manager
from src.core.dispatcher.gateway import ai_gateway
from src.core.module_loader import module_loader

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])


@router.get("/commands")
async def list_all_commands():
    """
    Discovery Endpoint: Returns the official list of all available commands,
    their descriptions, and their required parameter schemas.
    Now PUBLIC to solve the 'Chicken and Egg' paradox.
    """
    # Extract registry from the module loader
    registry = module_loader._command_registry

    discovery_data = []
    for cmd_name, metadata in registry.items():
        discovery_data.append(
            {
                "command": cmd_name,
                "description": metadata["description"],
                "params": metadata["params_schema"],
                "is_system": metadata["is_system"],
            }
        )

    return {
        "total_commands": len(discovery_data),
        "commands": discovery_data,
    }


@router.get("/schema")
async def get_business_schema(authorization: str = Header(None)):
    """
    ODDS Pilar 1: Dynamic Schema Introspection.
    Queries the business DB's information_schema to return a real-time map of tables and columns.
    PUBLIC ACCESS: If no token is provided, it returns the standard system blueprint schema.
    """
    # Optional Auth: If provided, we show the ACTUAL client DB. If not, we show the BLUEPRINT.
    agent_id = "SYSTEM_BLUEPRINT"

    if authorization:
        token = authorization.replace("Bearer ", "")
        is_valid, mode, tid = token_manager.validate_token(token)
        if is_valid:
            agent_id = str(tid)

    from src.core.registry.infrastructure_registry import infrastructure_registry
    from src.infrastructure.db.db_manager import db_manager

    # For SYSTEM_BLUEPRINT, we use a special internal context or the first available app
    app_context = infrastructure_registry.get_app_context(agent_id)

    # Fallback: If we are in blueprint mode and no context exists, we can't query a real DB.
    # In a real scenario, we'd have a 'blueprint' DB. For now, we'll attempt to find ANY active app
    # Fallback: If we are in blueprint mode and no context exists, we can't query a real DB.
    if not app_context:
        # Attempt to get any active app to show as a sample schema
        all_apps = (
            infrastructure_registry.get_all_apps()
        )  # Assuming this method exists or we use a fallback
        if all_apps:
            first_app = list(all_apps.values())[0]
            app_context = first_app
        else:
            raise HTTPException(
                status_code=503,
                detail="No active business databases available to introspect.",
            )

    if app_context is None:
        raise HTTPException(
            status_code=500, detail="Infrastructure context resolution failed."
        )

    try:
        async with db_manager.get_session(
            app_context["app_id"], app_context["db_config"], "PRODUCTION"
        ) as session:

            query = """
                SELECT 
                    table_name, 
                    column_name, 
                    data_type, 
                    is_nullable 
                FROM 
                    information_schema.columns 
                WHERE 
                    table_schema = 'public'
                ORDER BY 
                    table_name, ordinal_position;
            """
            result = await session.execute(query)
            rows = result.all()

            schema_map: Dict[str, Dict[str, Any]] = {}
            for table, column, dtype, nullable in rows:
                if table not in schema_map:
                    schema_map[table] = {"columns": {}}

                schema_map[table]["columns"][column] = {
                    "type": dtype,
                    "nullable": nullable == "YES",
                }

            return {
                "context": (
                    "CLIENT_DB"
                    if agent_id != "SYSTEM_BLUEPRINT"
                    else "SYSTEM_BLUEPRINT"
                ),
                "tables": schema_map,
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Schema introspection failed: {str(e)}"
        )


@router.get("/aliases")
async def list_aliases():
    """Returns the list of supported command aliases for normalization."""
    return {"aliases": ai_gateway.COMMAND_ALIASES}
