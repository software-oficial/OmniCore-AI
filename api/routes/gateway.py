from fastapi import APIRouter, Header, Body
from core.dispatcher.gateway import ai_gateway
from core.dispatcher.core_types import ServiceResponse
from core.module_loader import module_loader
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["Gateway"])

@router.get("/gateway/manifest")
async def get_manifest():
    """
    Returns the dynamic manifest of all registered commands.
    Essential for AI Agents to understand the system's capabilities.
    """
    registry = module_loader._command_registry
    manifest = {
        "total_commands": len(registry),
        "commands": [
            {
                "name": name, 
                "metadata": meta if isinstance(meta, dict) else {"handler": "function"}
            } 
            for name, meta in registry.items()
        ]
    }
    return manifest

@router.post("/gateway/execute")
async def handle_command(
    command: str = Body(..., embed=True),
    params: Dict[str, Any] = Body(..., embed=True),
    authorization: str = Header(None)
):
    if not authorization:
        return ServiceResponse.error_res("Missing Authorization Header", "AUTH_HEADER_MISSING").to_dict()
    
    # Accept both 'Bearer <token>' and direct '<token>'
    token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
    result = await ai_gateway.execute(command, token, params, None)
    return result.to_dict()
