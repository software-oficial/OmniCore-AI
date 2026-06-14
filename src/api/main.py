from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.api.routes import gateway, infra, agent, admin, auth, dev, business
from src.infrastructure.db.db_manager import db_manager
from src.infrastructure.logging.omni_logger import get_logger
from config.settings import config
from src.core.dispatcher.exceptions import handle_omnicore_exception
import asyncio
from datetime import datetime

app = FastAPI(
    title="OmniCore-AI Engine", 
    description="The AI-Ready Business OS Gateway",
    version=config.VERSION
)
logger = get_logger("OmniCore.Main")

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    """
    Global Safety Net: Ensures the system NEVER returns HTML.
    Internal technical details are masked to prevent leaking system architecture.
    """
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.detail}
        )
    
    # Log the real error internally for the admin
    logger.error("CRITICAL_SYSTEM_ERROR", f"Unhandled exception: {str(exc)}")
    
    # Return a generic response to the developer/client
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "message": "An unexpected internal server error occurred. Please contact technical support."
        }
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
            "heartbeat": "/api/heartbeat"
        },
        "message": "Welcome! Use /api/gateway/help to discover all available business commands."
    }

# 1. Register Business Modules
from src.core.module_loader import module_loader
for module in ["sales", "stock", "whatsapp"]:
    module_loader.load_module(module)

from src.core.system_service import system_service
from src.core.dispatcher.gateway import ai_gateway
from src.core.admin_service import admin_service

ai_gateway.register_command("system.deploy_schema", system_service.deploy_schema, description="Deploys the database schema blueprints to the client's external DB.")

# Developer Control Plane: Commands for the developer to manage their own SaaS clients and plans
ai_gateway.register_command("dev.admin.update_client_tier", admin_service.update_client_tier, is_system=True, description="Upgrade or downgrade a client's subscription tier (e.g., FREE -> PRO).")
ai_gateway.register_command("dev.admin.list_clients", admin_service.list_apps, is_system=True, description="List all clients/apps onboarded by the developer.")
ai_gateway.register_command("dev.admin.create_plan", admin_service.create_custom_plan, is_system=True, description="Create a new subscription plan level for the SaaS.")
ai_gateway.register_command("dev.admin.map_command", admin_service.map_command_to_plan, is_system=True, description="Assign a minimum required plan to a specific business command.")

# 2. Include Modular Routes
app.include_router(gateway.router)
app.include_router(business.router)
app.include_router(infra.router)
app.include_router(agent.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(dev.router)


# 3. Serve Frontend Panel (Disabled - Frontend is now standalone)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirects the root URL to the Developer Panel."""
    from fastapi.responses import RedirectResponse
    # Redirecting to the React dev server or production build
    return RedirectResponse(url="http://localhost:5173")

async def pool_cleanup_worker():
    """Background worker for DB pool cleanup."""
    while True:
        try:
            db_manager.evict_idle_pools()
            logger.info("LOG_INFRA", "Periodic DB pool cleanup executed.")
        except Exception as e:
            logger.error("LOG_SYSTEM", f"Error during DB pool cleanup: {e}")
        await asyncio.sleep(config.POOL_CLEANUP_INTERVAL)

@app.on_event("startup")
async def startup_event():
    # Start background workers
    asyncio.create_task(pool_cleanup_worker())
    
    # Start Async Log Worker
    from src.infrastructure.logging.omni_logger import get_logger
    main_logger = get_logger("OmniCore.Main")
    asyncio.create_task(main_logger.process_logs())
    logger.info("LOG_SYSTEM", "Async Log Worker has been initialized and is running in background.")


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
                "core_db": "connected"
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/heartbeat")
async def heartbeat():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ALIVE",
        "load": len(db_manager._engines)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)

