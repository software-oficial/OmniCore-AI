import uuid
from typing import Any, Dict, List, cast

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from src.core.auth.token_manager import token_manager
from src.infrastructure.db.core_db_manager import core_db_manager
from src.infrastructure.monitoring.logger import engine_logger

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

    # Extract user_id from token
    token = authorization.replace("Bearer ", "")
    try:
        payload = token_manager.decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = payload.get("user_id")
        if not user_id:
            user_id = token

        result = core_db_manager.execute_raw(
            "SELECT id, name FROM agents WHERE owner_user_id = :uid LIMIT 1",
            {"uid": user_id},
        )
        agent = result.fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail="No agent found for this user")
        return {"agent_id": agent[0], "name": agent[1]}
    except HTTPException:
        raise
    except Exception as e:
        engine_logger.error(f"Error in get_my_agent: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred. Please contact support.",
        )


@router.get("/projects", response_model=List[Dict[str, Any]])
async def list_projects(authorization: str = Header(None)):
    """
    Lists all projects (apps) associated with the authenticated user's agent.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Extract user_id from token
    token = authorization.replace("Bearer ", "")
    try:
        payload = token_manager.decode_token(token)
        user_id = payload.get("user_id") if payload else token
    except Exception:
        user_id = token

    try:
        # 1. Find the agent associated with this user
        agent_res = core_db_manager.execute_raw(
            "SELECT id FROM agents WHERE owner_user_id = :uid LIMIT 1", {"uid": user_id}
        ).fetchone()

        if not agent_res:
            # If no agent exists, we return an empty list (or could trigger auto-provisioning)
            return []

        agent_id = agent_res[0]

        # 2. Find all app_ids mapped to this agent
        mappings = core_db_manager.execute_raw(
            "SELECT app_id FROM agent_app_mapping WHERE agent_id = :aid",
            {"aid": agent_id},
        ).fetchall()

        app_ids = [m[0] for m in mappings]

        if not app_ids:
            return []

        # 3. Get app details
        apps = core_db_manager.execute_raw(
            "SELECT id, name FROM apps WHERE id IN :ids", {"ids": tuple(app_ids)}
        ).fetchall()

        return [{"id": a[0], "name": a[1]} for a in apps]
    except Exception as e:
        engine_logger.error(f"Error retrieving projects: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while retrieving projects.",
        )


class ProjectCreateRequest(BaseModel):
    name: str
    db_host: str
    db_port: int = 5432
    db_user: str
    db_password: str
    db_name: str


@router.post("/projects/create")
async def create_project(
    request: ProjectCreateRequest, authorization: str = Header(None)
):
    """
    Creates a new project (app) for the authenticated user's agent.
    The developer MUST provide their own database credentials.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Extract user_id from token
    token = authorization.replace("Bearer ", "")
    try:
        payload = token_manager.decode_token(token)
        user_id = payload.get("user_id") if payload else token
    except Exception:
        user_id = token

    try:
        # 1. Find or Create the Agent for this user
        agent_res = core_db_manager.execute_raw(
            "SELECT id FROM agents WHERE owner_user_id = :uid LIMIT 1", {"uid": user_id}
        ).fetchone()

        if agent_res:
            agent_id = agent_res[0]
        else:
            # Auto-provision an agent if one doesn't exist for the new user
            agent_id = str(uuid.uuid4())
            uid_str = cast(str, user_id)
            core_db_manager.execute_raw(
                "INSERT INTO agents (id, name, api_key, owner_user_id) VALUES (:id, :name, :key, :uid)",
                {
                    "id": agent_id,
                    "name": f"Agent_{uid_str[:8]}",
                    "key": str(uuid.uuid4()),
                    "uid": uid_str,
                },
            )

        app_id = str(uuid.uuid4())
        # 2. Create App
        core_db_manager.execute_raw(
            "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner)",
            {"id": app_id, "name": request.name, "owner": agent_id},
        )

        # 2.1 Provision Infrastructure (BYODB - Bring Your Own Database)
        core_db_manager.execute_raw(
            "INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier) "
            "VALUES (:app_id, :host, :port, :user, :pass, :db, :tier)",
            {
                "app_id": app_id,
                "host": request.db_host,
                "port": request.db_port,
                "user": request.db_user,
                "pass": request.db_password,
                "db": request.db_name,
                "tier": "FREE",
            },
        )

        # 3. Map Agent to App
        core_db_manager.execute_raw(
            "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id)",
            {"agent_id": agent_id, "app_id": app_id},
        )

        return {
            "success": True,
            "app_id": app_id,
            "message": f"Project {request.name} created successfully. Your database configuration has been linked. Please ensure your DB is accessible from OmniCore-AI.",
        }
    except Exception as e:
        engine_logger.error(f"Project creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project.")


@router.post("/register", response_model=RegisterResponse)
async def register_agent(request: RegisterRequest):
    """
    Registers a new AI Agent.
    The developer will need to create a project and provide their own database
    credentials to start using the API.
    """
    agent_id = str(uuid.uuid4())
    app_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())

    try:
        # 1. Create Agent
        core_db_manager.execute_raw(
            "INSERT INTO agents (id, name, api_key) VALUES (:id, :name, :key)",
            {"id": agent_id, "name": request.name, "key": api_key},
        )

        # 2. Create App
        core_db_manager.execute_raw(
            "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner)",
            {"id": app_id, "name": request.platform_name, "owner": agent_id},
        )

        # 3. Map Agent to App
        core_db_manager.execute_raw(
            "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id)",
            {"agent_id": agent_id, "app_id": app_id},
        )

        # Generate initial Learning token
        token = token_manager.generate_token(agent_id, tier="FREE")

    except Exception as e:
        engine_logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed due to an internal server error.",
        )

    return RegisterResponse(
        agent_id=agent_id,
        app_id=app_id,
        token=token,
        message="Welcome to OmniCore-AI! Please create a project and link your database to get started.",
    )


@router.get("/manifest")
async def get_manifest():
    """
    Returns the Semantic Business Manifest for AI Agents.
    Now includes critical onboarding information for the BYODB model.
    """
    return {
        "ontology": "Business-as-a-Service (BaaS) for Stock, Bot, and Payments",
        "onboarding": {
            "model": "BYODB (Bring Your Own Database)",
            "concept": "OmniCore-AI is a stateless orchestrator. You are responsible for hosting and managing your own business database (PostgreSQL).",
            "quick_steps": [
                "1. Deploy a PostgreSQL instance.",
                "2. Execute OmniCore Blueprints (SQL scripts) on your DB.",
                "3. Link your DB via POST /api/agent/projects/create.",
                "4. Consume the API.",
            ],
            "docs_endpoint": "/api/agent/guides",
        },
        "modes": {
            "LEARNING": "Sandbox mode for AI exploration. No real DB impact.",
            "PRODUCTION": "Live mode. Real DB impact, billed by usage.",
        },
        "commands": {
            "stock.add": {
                "description": "Adds a product to the developer's inventory.",
                "params": {"name": "string", "price": "float", "quantity": "int"},
                "example": {"name": "Laptop", "price": 1200.50, "quantity": 10},
            }
        },
    }


@router.get("/guides")
async def get_guides():
    """
    Provides detailed step-by-step guides for developers to set up their
    infrastructure and connect it to OmniCore-AI.
    """
    return {
        "title": "Developer Onboarding Guide - OmniCore-AI",
        "infrastructure_model": "BYODB (Bring Your Own Database)",
        "steps": [
            {
                "step": 1,
                "title": "Database Deployment",
                "description": "Deploy a PostgreSQL instance. You can use services like Railway, Supabase, AWS RDS, or your own VPS.",
                "requirement": "Ensure the database is accessible from the internet (OmniCore-AI servers must be able to connect to it).",
            },
            {
                "step": 2,
                "title": "Schema Initialization (Blueprints)",
                "description": "Execute the provided SQL blueprints on your new database. These scripts create the necessary tables for the business modules.",
                "action": "Download and run the .sql files from the /src/domains/ folder of the repository.",
                "essential_tables": [
                    "bot_states",
                    "whatsapp_menus",
                    "stock_inventory",
                    "sales_records",
                ],
            },
            {
                "step": 3,
                "title": "Project Linking",
                "description": "Connect your database to your OmniCore Agent.",
                "endpoint": "POST /api/agent/projects/create",
                "payload_example": {
                    "name": "My Awesome App",
                    "db_host": "your-db-host.com",
                    "db_port": 5432,
                    "db_user": "admin",
                    "db_password": "securepassword",
                    "db_name": "my_business_db",
                },
            },
            {
                "step": 4,
                "title": "API Consumption",
                "description": "You are now ready to use the API. Use your agent token and the app_id generated in Step 3 to execute business commands.",
                "verification": "Try executing 'stock.list' to verify the connection.",
            },
        ],
        "troubleshooting": {
            "INFRA_NOT_FOUND": "Your project is not linked to a database or the credentials provided in Step 3 are incorrect.",
            "ConnectionError": "OmniCore-AI cannot reach your database. Check your firewall settings and ensure the DB is public/accessible.",
        },
    }
