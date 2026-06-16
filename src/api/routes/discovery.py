from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException

from src.core.auth.token_manager import token_manager
from src.core.dispatcher.gateway import ai_gateway
from src.core.module_loader import module_loader

router = APIRouter(prefix="/api/discovery", tags=["Discovery"])


@router.get("/commands")
async def list_all_commands(authorization: str = Header(None)):
    """
    Discovery Endpoint: Returns the official list of all available commands,
    their descriptions, and their required parameter schemas.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    is_valid, mode, agent_id = token_manager.validate_token(token)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

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
        "agent_id": agent_id,
        "mode": mode,
        "total_commands": len(discovery_data),
        "commands": discovery_data,
    }


@router.get("/schema")
async def get_business_schema(authorization: str = Header(None)):
    """
    ODDS Pilar 1: Dynamic Schema Introspection.
    Queries the business DB's information_schema to return a real-time map of tables and columns.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    is_valid, mode, agent_id = token_manager.validate_token(token)

    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Ensure agent_id is treated as a string for the registry lookup
    safe_agent_id = str(agent_id) if agent_id else "unknown"

    from src.core.registry.infrastructure_registry import infrastructure_registry
    from src.infrastructure.db.db_manager import db_manager

    app_context = infrastructure_registry.get_app_context(safe_agent_id)
    if not app_context:
        raise HTTPException(status_code=404, detail="Infrastructure context not found")

    try:
        async with db_manager.get_session(
            app_context["app_id"], app_context["db_config"], "PRODUCTION"
        ) as session:
            # Information Schema Query (Postgres compatible)
            # We fetch tables and columns that are NOT in system schemas
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
                "agent_id": safe_agent_id,
                "app_id": app_context["app_id"],
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
