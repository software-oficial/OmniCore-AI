from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from api.routes import gateway, infra, agent, admin, auth
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
    Every single error is converted into a structured OmniCore JSON response.
    """
    service_res = handle_omnicore_exception(exc)
    return JSONResponse(
        status_code=getattr(exc, 'status_code', 500),
        content=service_res.to_dict()
    )

# 1. Register Business Modules
register_stock_commands()
register_sales_commands()
register_whatsapp_commands()

# 2. Include Modular Routes
app.include_router(gateway.router)
app.include_router(infra.router)
app.include_router(agent.router)
app.include_router(admin.router)
app.include_router(auth.router)

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
