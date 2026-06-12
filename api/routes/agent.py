from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from infra.db.core_db_manager import core_db_manager
from core.auth.token_manager import token_manager
import uuid

router = APIRouter(prefix="/api/agent", tags=["Agent"])

class RegisterRequest(BaseModel):
    name: str

class RegisterResponse(BaseModel):
    agent_id: str
    token: str
    message: str

@router.post("/register", response_model=RegisterResponse)
async def register_agent(request: RegisterRequest):
    """
    Registers a new AI Agent in the system and generates an initial access token.
    """
    agent_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4()) # Secret key for internal auth

    try:
        with core_db_manager.get_session() as session:
            # Check if agent name is unique (optional, but good practice)
            session.execute(
                core_db_manager.execute_raw(
                    "INSERT INTO agents (id, name, api_key) VALUES (:id, :name, :key)",
                    {"id": agent_id, "name": request.name, "key": api_key}
                )
            )

        # Generate initial Learning token
        token = token_manager.generate_token(agent_id, mode="LEARNING")

        return RegisterResponse(
            agent_id=agent_id,
            token=token,
            message="Agent registered successfully. You are now in LEARNING mode."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.get("/manifest")
async def get_manifest():
...
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
