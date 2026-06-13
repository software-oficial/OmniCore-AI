from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from api.routes import gateway, infra, agent, admin, auth, dev, business
from infra.db.db_manager import db_manager
from infra.logging.omni_logger import get_logger
from config.settings import config
from modules.stock.commands import register_stock_commands
from modules.sales.commands import register_sales_commands
from modules.whatsapp.commands import register_whatsapp_commands
from core.dispatcher.exceptions import handle_omnicore_exception
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

# 1. Register Business Modules
register_stock_commands()
register_sales_commands()
register_whatsapp_commands()

from core.system_service import system_service
from core.dispatcher.gateway import ai_gateway
from core.admin_service import admin_service

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

# 3. Serve Frontend Panel
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirects the root URL to the Developer Panel."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

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
    asyncio.create_task(pool_cleanup_worker())

@app.get("/health")
async def health():
    try:
        from infra.cache.redis_manager import cache_manager
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
