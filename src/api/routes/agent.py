import uuid
from typing import Any, Dict, List, cast

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from src.core.auth.auth_service import auth_service
from src.core.auth.token_manager import token_manager
from src.infrastructure.db.core_db_manager import core_db_manager
from src.infrastructure.monitoring.logger import engine_logger

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class RegisterRequest(BaseModel):
    name: str = Field(
        ..., description="Friendly name for the AI Agent (e.g. 'SalesBot_v1')"
    )
    platform_name: str = Field(
        ..., description="Name of the business platform the agent will serve"
    )


class RegisterResponse(BaseModel):
    agent_id: str
    app_id: str
    token: str
    message: str


class OnboardRequest(BaseModel):
    name: str = Field(..., description="Friendly name for the AI Agent")
    platform_name: str = Field(..., description="Name of the business platform")
    db_host: str = Field(
        ...,
        description="Host address of the PostgreSQL database (e.g. 'localhost' or 'db.example.com')",
    )
    db_port: int = Field(5432, description="PostgreSQL port")
    db_user: str = Field(
        ..., description="Database user with superuser or schema-owner privileges"
    )
    db_password: str = Field(..., description="Password for the database user")
    db_name: str = Field(
        ..., description="Name of the database where blueprints will be deployed"
    )


@router.post("/onboard", response_model=RegisterResponse)
async def onboard_agent(request: OnboardRequest, authorization: str = Header(None)):
    """
    Zero-to-Hero Onboarding for AI Agents.
    Automates: Agent Registration -> Project Creation -> Infra Linking -> Schema Deployment.
    """
    # 1. Handle Identity
    user_id = None
    if authorization:
        token = authorization.replace("Bearer ", "")
        try:
            payload = token_manager.decode_token(token)
            if payload:
                user_id = payload.get("user_id")
            else:
                user_id = token
        except Exception:
            user_id = token

    # Validate user existence to prevent ForeignKeyViolation
    if user_id:
        user_exists = core_db_manager.execute_raw(
            "SELECT 1 FROM users WHERE id = :uid", {"uid": user_id}
        ).fetchone()
        if not user_exists:
            engine_logger.warning(
                f"Provided user_id {user_id} not found. Onboarding as guest."
            )
            user_id = None

    agent_id = str(uuid.uuid4())
    app_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())

    try:
        # 2. Create Agent
        core_db_manager.execute_raw(
            "INSERT INTO agents (id, name, api_key, owner_user_id) VALUES (:id, :name, :key, :uid)",
            {"id": agent_id, "name": request.name, "key": api_key, "uid": user_id},
        )

        # 3. Create App
        core_db_manager.execute_raw(
            "INSERT INTO apps (id, name, owner_id) VALUES (:id, :name, :owner)",
            {"id": app_id, "name": request.platform_name, "owner": agent_id},
        )

        # 4. Provision Infrastructure (BYODB)
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

        # 5. Map Agent to App
        core_db_manager.execute_raw(
            "INSERT INTO agent_app_mapping (agent_id, app_id) VALUES (:agent_id, :app_id)",
            {"agent_id": agent_id, "app_id": app_id},
        )

        # 6. Automatic Schema Deployment (Zero-to-Hero)
        from src.core.dispatcher.core_types import CoreContext
        from src.core.system_service import system_service
        from src.infrastructure.db.db_manager import db_manager

        db_config = {
            "host": request.db_host,
            "port": request.db_port,
            "user": request.db_user,
            "password": request.db_password,
            "dbname": request.db_name,
        }

        ctx = CoreContext(
            agent_id=agent_id,
            app_id=app_id,
            dev_id="SYSTEM",
            mode="PRODUCTION",
            db_config=db_config,
            tier="FREE",
        )

        async with db_manager.get_session(app_id, db_config, "FREE") as session:
            deploy_res = system_service.deploy_schema(session, ctx)
            if not deploy_res.success:
                engine_logger.error(
                    f"Schema deployment failed during onboarding: {deploy_res.message}"
                )
                # We don't fail the whole onboarding, but we notify the user
                deployment_status = f"FAILED: {deploy_res.message}"
            else:
                deployment_status = "SUCCESSFUL"

        # 7. Generate Token
        token = token_manager.generate_token(
            agent_id=agent_id, app_id=app_id, dev_id="SYSTEM"
        )

    except Exception as e:
        engine_logger.exception("Zero-to-Hero Onboarding critical error")
        raise HTTPException(
            status_code=500,
            detail=f"Onboarding failed: {str(e)}",
        )

    return RegisterResponse(
        agent_id=agent_id,
        app_id=app_id,
        token=token,
        message=f"Zero-to-Hero successful! Agent registered, DB linked, and schema deployment was {deployment_status}.",
    )


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
            # In case the token is an Agent token (agent_id) instead of User token
            user_id = payload.get("agent_id")
            if not user_id:
                raise HTTPException(
                    status_code=401, detail="Identity not found in token"
                )

        user_id = cast(str, user_id)

        result = core_db_manager.execute_raw(
            "SELECT id, name FROM agents WHERE id = :uid OR owner_user_id = :uid LIMIT 1",
            {"uid": user_id},
        )
        agent = result.fetchone()
        if not agent:
            raise HTTPException(
                status_code=404, detail="No agent found for this identity"
            )
        return {"agent_id": agent[0], "name": agent[1]}
    except HTTPException:
        raise
    except Exception:
        engine_logger.exception("Error in get_my_agent")
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

    # Extract identity from token
    token = authorization.replace("Bearer ", "")
    try:
        payload = token_manager.decode_token(token)
        # Handle potential None from decode_token
        data = payload if payload is not None else {}
        user_id = data.get("user_id")
        agent_id_from_token = data.get("agent_id")
    except Exception:
        user_id = None
        agent_id_from_token = None

    try:
        # Find the agent
        if user_id:
            agent_res = core_db_manager.execute_raw(
                "SELECT id FROM agents WHERE owner_user_id = :uid LIMIT 1",
                {"uid": user_id},
            ).fetchone()
        elif agent_id_from_token:
            agent_res = core_db_manager.execute_raw(
                "SELECT id FROM agents WHERE id = :aid LIMIT 1",
                {"aid": agent_id_from_token},
            ).fetchone()
        else:
            return []

        if not agent_res:
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
    except Exception:
        engine_logger.exception("Error retrieving projects")
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
        # 1. Validate user existence first to prevent ForeignKeyViolation
        with core_db_manager.get_session() as session:
            if not auth_service.validate_user_exists(session, cast(str, user_id)):
                raise HTTPException(
                    status_code=401, detail="Invalid user identity. Please login again."
                )

        # Find or Create the Agent for this user
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
    except Exception:
        engine_logger.exception("Project creation error")
        raise HTTPException(status_code=500, detail="Failed to create project.")


@router.post("/register", response_model=RegisterResponse)
async def register_agent(request: RegisterRequest):
    """
    Registers a new AI Agent and auto-provisions infrastructure.
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

        # 4. Auto-provision Infrastructure (Using default configuration)
        from config.settings import config

        db_config = {
            "host": config.DB_HOST,
            "port": config.DB_PORT,
            "user": config.DB_USER,
            "password": config.DB_PASSWORD,
            "dbname": config.DB_NAME,
        }

        core_db_manager.execute_raw(
            "INSERT INTO app_infrastructure (app_id, db_host, db_port, db_user, db_password, db_name, tier) "
            "VALUES (:app_id, :host, :port, :user, :pass, :db, :tier)",
            {
                "app_id": app_id,
                "host": db_config["host"],
                "port": db_config["port"],
                "user": db_config["user"],
                "pass": db_config["password"],
                "db": db_config["dbname"],
                "tier": "FREE",
            },
        )

        # 5. Schema Deployment
        from src.core.dispatcher.core_types import CoreContext
        from src.core.system_service import system_service
        from src.infrastructure.db.db_manager import db_manager

        ctx = CoreContext(
            agent_id=agent_id,
            app_id=app_id,
            dev_id="SYSTEM",
            mode="PRODUCTION",
            db_config=db_config,
            tier="FREE",
        )

        async with db_manager.get_session(app_id, db_config, "FREE") as session:
            system_service.deploy_schema(session, ctx)

        # Generate initial token
        token = token_manager.generate_token(
            agent_id=agent_id, app_id=app_id, dev_id="SYSTEM"
        )

    except Exception:
        engine_logger.exception("Registration error")
        raise HTTPException(
            status_code=500,
            detail="Registration failed due to an internal server error.",
        )

    return RegisterResponse(
        agent_id=agent_id,
        app_id=app_id,
        token=token,
        message="Welcome to OmniCore-AI! Infrastructure provisioned and ready.",
    )


@router.get("/manifest")
async def get_manifest():
    """
    Returns the Semantic Business Manifest for AI Agents.
    Now focused on Local Linux Zero-to-Hero Onboarding.
    """
    return {
        "ontology": "Business-as-a-Service (BaaS) for Stock, Bot, and Payments",
        "onboarding": {
            "model": "BYODB (Bring Your Own Database) - Local Linux",
            "concept": "OmniCore-AI is a stateless orchestrator. You must install PostgreSQL on your local Linux server to host your business data.",
            "quick_steps": [
                "1. Install PostgreSQL on Linux (sudo apt install postgresql).",
                "2. Create local DB and User (sudo -u postgres psql).",
                "3. Run the Auto-Onboarding: POST /api/agent/onboard.",
                "4. Verify and Consume the API.",
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
    infrastructure on a LOCAL LINUX server and connect it to OmniCore-AI.
    """
    return {
        "title": "Local Linux Deployment Guide - OmniCore-AI",
        "infrastructure_model": "BYODB (Bring Your Own Database) - Local Install",
        "steps": [
            {
                "step": 1,
                "title": "Database Installation (Local Linux)",
                "description": "Install PostgreSQL on your Ubuntu/Debian server.",
                "commands": [
                    "sudo apt update",
                    "sudo apt install postgresql postgresql-contrib -y",
                    "sudo systemctl start postgresql",
                    "sudo systemctl enable postgresql",
                ],
                "setup_db": {
                    "command": "sudo -u postgres psql",
                    "sql": [
                        "CREATE DATABASE omnicore_biz;",
                        "CREATE USER omni_admin WITH PASSWORD 'secure_password';",
                        "GRANT ALL PRIVILEGES ON DATABASE omnicore_biz TO omni_admin;",
                        "\\c omnicore_biz",
                        "GRANT ALL ON SCHEMA public TO omni_admin;",
                    ],
                },
            },
            {
                "step": 2,
                "title": "Zero-to-Hero Automation",
                "description": "Use the onboard endpoint to let OmniCore-AI configure your database automatically.",
                "endpoint": "POST /api/agent/onboard",
                "payload_example": {
                    "name": "MyLocalAgent",
                    "platform_name": "MyLocalSaaS",
                    "db_host": "localhost",
                    "db_port": 5432,
                    "db_user": "omni_admin",
                    "db_password": "secure_password",
                    "db_name": "omnicore_biz",
                },
                "benefit": "OmniCore-AI will automatically deploy all SQL blueprints (tables, indexes) into your local DB.",
            },
            {
                "step": 3,
                "title": "Connectivity Verification",
                "description": "Run these commands via the Gateway to ensure everything is working.",
                "verification_checklist": [
                    {
                        "command": "system.get_version",
                        "expected": "Version string (e.g. 1.0.0-stable)",
                    },
                    {
                        "command": "system.get_health",
                        "expected": '{"db": "OK", "api": "OK"}',
                    },
                    {
                        "command": "stock.list",
                        "expected": "Empty list [] (meaning DB is connected but empty)",
                    },
                ],
            },
        ],
        "troubleshooting": {
            "ConnectionRefused": "Ensure PostgreSQL is running on port 5432 and allows connections from the API host.",
            "AuthFailed": "Verify that the db_user and db_password match what you created in Step 1.",
            "INFRA_NOT_FOUND": "The onboarding failed or you are using a token not linked to any project.",
        },
    }
