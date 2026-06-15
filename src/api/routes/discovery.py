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


@router.get("/aliases")
async def list_aliases():
    """Returns the list of supported command aliases for normalization."""
    return {"aliases": ai_gateway.COMMAND_ALIASES}
