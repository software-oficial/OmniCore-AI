
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from src.core.auth.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Request Models ---
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenCreateRequest(BaseModel):
    agent_id: str
    token_name: str
    mode: str = "PRODUCTION"


class TokenResponse(BaseModel):
    token_name: str
    agent_id: str
    created_at: str


# --- Endpoints ---


@router.post("/register")
async def register(request: RegisterRequest):
    """Registers a new user account for the OmniCore Panel."""
    res = auth_service.register_user(request.email, request.password)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.to_dict()


@router.post("/login")
async def login(request: LoginRequest):
    """Authenticates a user and returns session data."""
    res = auth_service.login(request.email, request.password)
    if not res.success:
        raise HTTPException(status_code=401, detail=res.message)
    return res.to_dict()


@router.post("/tokens/create")
async def create_token(request: TokenCreateRequest, authorization: str = Header(None)):
    """
    Generates a new API token for a specific agent.
    Requires a valid user session (Authorization header).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    # In a full JWT implementation, we would decode the token to get the user_id.
    # For now, we assume the authorization header contains the user_id or a session token.
    user_id = authorization.replace("Bearer ", "")

    res = auth_service.create_api_token(
        user_id, request.agent_id, request.token_name, request.mode
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.to_dict()


@router.get("/tokens")
async def list_tokens(authorization: str = Header(None)):
    """Lists all API tokens owned by the authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    user_id = authorization.replace("Bearer ", "")
    res = auth_service.list_user_tokens(user_id)
    if not res.success:
        raise HTTPException(status_code=500, detail=res.message)
    return res.to_dict()


@router.delete("/tokens/{token_hash}")
async def revoke_token(token_hash: str, authorization: str = Header(None)):
    """Revokes a specific API token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    res = auth_service.revoke_token(token_hash)
    if not res.success:
        raise HTTPException(status_code=500, detail=res.message)
    return res.to_dict()
