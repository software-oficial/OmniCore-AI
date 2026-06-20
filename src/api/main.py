import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config.settings import config
from src.api.routes import (
    admin,
    agent,
    auth,
    business,
    dev,
    discovery,
    gateway,
    infra,
    sdk,
)
from src.core.admin_service import admin_service
from src.core.dispatcher.gateway import ai_gateway
from src.core.module_loader import module_loader
from src.core.system_service import system_service
from src.infrastructure.db.db_manager import db_manager
from src.infrastructure.logging.omni_logger import get_logger

app = FastAPI(
    title="OmniCore-AI Engine",
    description="The AI-Ready Business OS Gateway",
    version=config.VERSION,
)

# Hybrid CORS Configuration
# Allows both internal (same-origin) and external (SaaS frontend) requests
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background workers
    asyncio.create_task(pool_cleanup_worker())

    # Start Async Log Worker
    from src.infrastructure.logging.omni_logger import get_logger

    main_logger = get_logger("OmniCore.Main")
    asyncio.create_task(main_logger.process_logs())
    logger.info(
        "LOG_SYSTEM",
        "Async Log Worker has been initialized and is running in background.",
    )
    yield


app.router.lifespan_context = lifespan
logger = get_logger("OmniCore.Main")


@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    """
    Global Safety Net: Ensures the system NEVER returns HTML.
    Handles standard HTTPExceptions, Pydantic validation errors, and critical system failures.
    """
    from fastapi.exceptions import RequestValidationError

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.detail},
        )

    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error in request payload",
                "details": exc.errors(),
            },
        )

    # Log the real error internally for the admin
    logger.error("CRITICAL_SYSTEM_ERROR", f"Unhandled exception: {str(exc)}")

    # Return a generic response to the developer/client
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected internal server error occurred. Please contact technical support.",
        },
    )


@app.get("/api")
async def api_root():
    """
    Welcome endpoint for the API.
    Provides immediate discovery links for developers.
    """
    return {
        "system": "OmniCore-AI Gateway",
        "version": config.VERSION,
        "status": "ONLINE",
        "discovery": {
            "help": "/api/gateway/help",
            "openapi": "/api/gateway/openapi",
            "heartbeat": "/api/heartbeat",
        },
        "message": "Welcome! Use /api/gateway/help to discover all available business commands.",
    }


# 1. Register Business Modules

for module in ["sales", "stock", "whatsapp"]:
    module_loader.load_module(module)

logger.info(
    "SYSTEM_BOOT",
    f"ModuleLoader initialized. Total commands registered: {len(module_loader._command_registry)}",
)

ai_gateway.register_command(
    "system.deploy_schema",
    system_service.deploy_schema,
    description="Deploys the database schema blueprints to the client's external DB.",
)

ai_gateway.register_command(
    "system.get_health",
    system_service.get_health,
    description="Performs a comprehensive health check of the infrastructure (DB, API Tokens, Connectivity).",
)

# Developer Control Plane: Commands for the developer to manage their own SaaS clients and plans
ai_gateway.register_command(
    "dev.admin.update_client_tier",
    admin_service.update_client_tier,
    is_system=True,
    description="Upgrade or downgrade a client's subscription tier (e.g., FREE -> PRO).",
)
ai_gateway.register_command(
    "dev.admin.list_clients",
    admin_service.list_apps,
    is_system=True,
    description="List all clients/apps onboarded by the developer.",
)
ai_gateway.register_command(
    "dev.admin.create_plan",
    admin_service.create_custom_plan,
    is_system=True,
    description="Create a new subscription plan level for the SaaS.",
)
ai_gateway.register_command(
    "dev.admin.map_command",
    admin_service.map_command_to_plan,
    is_system=True,
    description="Assign a minimum required plan to a specific business command.",
)

# 2. Include Modular Routes
app.include_router(gateway.router)
app.include_router(discovery.router)
app.include_router(business.router)
app.include_router(infra.router)
app.include_router(agent.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(dev.router)
app.include_router(sdk.router)


# 3. Serve Frontend Panel


@app.get("/debug/filesystem")
async def debug_filesystem():
    """
    Temporary diagnostic endpoint to inspect container filesystem.
    """
    results = {}
    paths_to_inspect = ["/", "/app", "/src"]
    for p in paths_to_inspect:
        try:
            results[p] = os.listdir(p)
        except Exception as e:
            results[p] = f"Error: {str(e)}"
    return results


def find_static_dir():
    """
    Robustly attempts to find the 'static' directory by locating the project root.
    """
    current_path = os.path.abspath(__file__)

    # 1. Try to find project root by looking for known markers
    root_path = None
    check_path = os.path.dirname(current_path)

    while check_path != os.path.dirname(check_path):  # Stop at system root
        if os.path.exists(os.path.join(check_path, "GEMINI.md")) or os.path.exists(
            os.path.join(check_path, ".git")
        ):
            root_path = check_path
            break
        check_path = os.path.dirname(check_path)

    if root_path:
        # Use debug logger for diagnostics
        logger.debug(f"Project root identified at: {root_path}")
        static_candidate = os.path.join(root_path, "static")
        logger.debug(f"Checking static candidate: {static_candidate}")
        if os.path.isdir(static_candidate):
            return static_candidate

    # 2. Fallback: Exhaustive search in immediate parents
    logger.debug("Root markers not found, attempting fallback search...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    paths_to_check = [
        os.path.join(
            os.path.dirname(os.path.dirname(current_dir)), "static"
        ),  # /app/static
        os.path.join(os.path.dirname(current_dir), "static"),  # /app/src/static
        "static",  # CWD/static
        "/app/static",  # Absolute common
        "/static",  # Absolute system
    ]

    for path in paths_to_check:
        abs_path = os.path.abspath(path)
        logger.debug(f"Checking fallback path: {abs_path}")
        if os.path.isdir(abs_path):
            return abs_path

    logger.error(
        "LOG_SYSTEM",
        "Static directory NOT found in any expected location. Frontend will be unavailable.",
    )
    return None


static_path = find_static_dir()
if static_path:
    app.mount("/static", StaticFiles(directory=static_path), name="static")
else:

    @app.get("/static/{file_path:path}")
    async def static_fallback(file_path: str):
        raise HTTPException(
            status_code=404, detail="Static assets directory is missing on the server."
        )


@app.get("/")
async def root():
    """Redirects the root URL to the Developer Panel."""
    from fastapi.responses import RedirectResponse

    if static_path:
        return RedirectResponse(url="/static/index.html")
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Frontend assets not found. Please contact administrator.",
        },
    )


async def pool_cleanup_worker():
    """Background worker for DB pool cleanup."""
    while True:
        try:
            db_manager.evict_idle_pools()
            logger.info("LOG_INFRA", "Periodic DB pool cleanup executed.")
        except Exception as e:
            logger.error("LOG_SYSTEM", f"Error during DB pool cleanup: {e}")
        await asyncio.sleep(config.POOL_CLEANUP_INTERVAL)


@app.get("/health")
async def health():
    try:
        from src.infrastructure.cache.redis_manager import cache_manager

        redis_ok = cache_manager.is_available()
        pool_load = len(db_manager._engines)
        return {
            "status": "ok",
            "engine": "OmniCore-AI",
            "version": config.VERSION,
            "components": {
                "redis": "online" if redis_ok else "offline",
                "db_pool_size": pool_load,
                "core_db": "connected",
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/heartbeat")
async def heartbeat():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ALIVE",
        "load": len(db_manager._engines),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)
