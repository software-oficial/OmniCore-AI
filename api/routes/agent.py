from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from infra.db.core_db_manager import core_db_manager
from core.auth.token_manager import token_manager
import uuid

router = APIRouter(prefix="/api/agent", tags=["Agent"])

class RegisterRequest(BaseModel):
    name: str
    platform_name: str

class RegisterResponse(BaseModel):
    agent_id: str
    app_id: str
    token: str
    message: str

@router.post("/register", response_model=RegisterResponse)
async def register_agent(request: RegisterRequest):
    """
    Registers a new AI Agent and automatically provisions a Sandbox Infrastructure.
    This allows the developer to start testing immediately in LEARNING mode.
    """
    agent_id = str(uuid.uuid4())
    app_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())
    
    try:
        # 1. Create Agent
        core_db_manager.execute_raw(
            "INSERT INTO agents (id, name, api_key) VALUES (:id, :name, :key)",
            {"id": agent_id, "name": request.name, "key": api_key}
        )
        
        # 2. Create App
        core_db_manager.execute_raw(
            "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner)",
            {"id": app_id, "name": request.platform_name, "owner": agent_id}
        )
        
        # 3. Provision Sandbox Infrastructure (Learning Mode)
        core_db_manager.execute_raw(
            "INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier) "
            "VALUES (:app_id, :host, :port, :user, :pass, :db, :tier)",
            {
                "app_id": app_id,
                "host": "sandbox.omnicore.internal",
                "port": 5432,
                "user": "sandbox_user",
                "pass": "sandbox_pass",
                "db": "sandbox_db",
                "tier": "FREE"
            }
        )

        # 4. Map Agent to App
        core_db_manager.execute_raw(
            "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id)",
            {"agent_id": agent_id, "app_id": app_id}
        )
        
        # Generate initial Learning token
        token = token_manager.generate_token(agent_id, mode="LEARNING")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    return RegisterResponse(
        agent_id=agent_id,
        app_id=app_id,
        token=token,
        message="Welcome to OmniCore-AI! Your Sandbox environment is ready."
    )

@router.get("/manifest")
async def get_manifest():
    """
    Returns the Semantic Business Manifest for AI Agents.
    """
    return {
        "ontology": "Business-as-a-Service (BaaS) for Stock, Bot, and Payments",
        "modes": {
            "LEARNING": "Sandbox mode for AI exploration. No real DB impact.",
            "PRODUCTION": "Live mode. Real DB impact, billed by usage."
        },
        "commands": {
            "stock.add": {
                "description": "Adds a product to the developer's inventory.",
                "params": {"name": "string", "price": "float", "quantity": "int"},
                "example": {"name": "Laptop", "price": 1200.50, "quantity": 10}
            }
        }
    }

