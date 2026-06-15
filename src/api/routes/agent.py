from fastapi import APIRouter, HTTPException, Header
from typing import List, Dict, Any
from pydantic import BaseModel
from src.infrastructure.db.core_db_manager import core_db_manager
from src.core.auth.token_manager import token_manager
from src.infrastructure.monitoring.logger import logger
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

@router.get("/me")
async def get_my_agent(authorization: str = Header(None)):
    """
    Retrieves the agent associated with the authenticated user.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = authorization.replace("Bearer ", "")
    try:
        result = core_db_manager.execute_raw(
            "SELECT id, name FROM agents WHERE owner_user_id = :uid LIMIT 1",
            {"uid": user_id}
        )
        agent = result.fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail="No agent found for this user")
        return {"agent_id": agent[0], "name": agent[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal server error occurred. Please contact support.")

@router.get("/projects", response_model=List[Dict[str, Any]])
async def list_projects(authorization: str = Header(None)):
    """
    Lists all projects (apps) associated with the authenticated user's agent.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    user_id = authorization.replace("Bearer ", "")
    
    try:
        # 1. Find the agent associated with this user
        agent_res = core_db_manager.execute_raw(
            "SELECT id FROM agents WHERE owner_user_id = :uid LIMIT 1",
            {"uid": user_id}
        ).fetchone()
        
        if not agent_res:
            # If no agent exists, we return an empty list (or could trigger auto-provisioning)
            return []
            
        agent_id = agent_res[0]

        # 2. Find all app_ids mapped to this agent
        mappings = core_db_manager.execute_raw(
            "SELECT app_id FROM agent_app_mapping WHERE agent_id = :aid",
            {"aid": agent_id}
        ).fetchall()
        
        app_ids = [m[0] for m in mappings]
        
        if not app_ids:
            return []
            
        # 3. Get app details
        apps = core_db_manager.execute_raw(
            "SELECT id, name FROM apps WHERE id IN :ids",
            {"ids": tuple(app_ids)}
        ).fetchall()
        
        return [{"id": a[0], "name": a[1]} for a in apps]
    except Exception as e:
        logger.error(f"Error retrieving projects: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while retrieving projects.")

class ProjectCreateRequest(BaseModel):
    name: str

@router.post("/projects/create")
async def create_project(request: ProjectCreateRequest, authorization: str = Header(None)):
    """
    Creates a new project (app) for the authenticated user's agent.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    user_id = authorization.replace("Bearer ", "")
    
    try:
        # 1. Find or Create the Agent for this user
        agent_res = core_db_manager.execute_raw(
            "SELECT id FROM agents WHERE owner_user_id = :uid LIMIT 1",
            {"uid": user_id}
        ).fetchone()
        
        if agent_res:
            agent_id = agent_res[0]
        else:
            # Auto-provision an agent if one doesn't exist for the new user
            agent_id = str(uuid.uuid4())
            core_db_manager.execute_raw(
                "INSERT INTO agents (id, name, api_key, owner_user_id) VALUES (:id, :name, :key, :uid)",
                {"id": agent_id, "name": f"Agent_{user_id[:8]}", "key": str(uuid.uuid4()), "uid": user_id}
            )
        
        app_id = str(uuid.uuid4())
        # 2. Create App
        core_db_manager.execute_raw(
            "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner)",
            {"id": app_id, "name": request.name, "owner": agent_id}
        )
        
        # 3. Map Agent to App
        core_db_manager.execute_raw(
            "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id)",
            {"agent_id": agent_id, "app_id": app_id}
        )
        
        return {"success": True, "app_id": app_id, "message": f"Project {request.name} created successfully."}
    except Exception as e:
        logger.error(f"Project creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project.")

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
        token = token_manager.generate_token(agent_id, tier="FREE")

    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed due to an internal server error.")

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

