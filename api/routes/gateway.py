from fastapi import APIRouter, Header, Body
from core.dispatcher.gateway import ai_gateway
from core.dispatcher.core_types import ServiceResponse
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["Gateway"])

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
