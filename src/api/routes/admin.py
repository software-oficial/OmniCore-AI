from fastapi import APIRouter, Depends, HTTPException
from src.core.telemetry.telemetry_service import telemetry_service
from src.infrastructure.db.db_manager import db_manager
from src.core.registry.infrastructure_registry import infrastructure_registry
from typing import Dict, Any, List

router = APIRouter(prefix="/api/admin", tags=["System Administration"])

@router.get("/metrics")
async def get_system_metrics():
    """
    Returns real-time system metrics for the Administrative Dashboard.
    Includes concurrency, request volume, and resource load.
    """
    metrics = telemetry_service.get_realtime_metrics()
    infra_status = {
        "active_db_pools": len(db_manager._engines),
        "system_status": "HEALTHY" if len(db_manager._engines) < 100 else "HIGH_LOAD"
    }
    return {
        "telemetry": metrics,
        "infrastructure": infra_status
    }

@router.post("/apps/onboard")
async def onboard_app(payload: Dict[str, Any]):
    """
    Administrative endpoint to onboard a new SaaS client into OmniCore-AI.
    Required payload: {agent_id, app_name, db_config: {host, port, user, password, dbname}, tier}
    """
    try:
        app_id = infrastructure_registry.register_app(
            agent_id=payload['agent_id'],
            app_name=payload['app_name'],
            db_config=payload['db_config'],
            tier=payload.get('tier', 'FREE')
        )
        return {"success": True, "app_id": app_id, "message": f"App {payload['app_name']} onboarded successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/apps/{app_id}/tier")
async def update_tier(app_id: str, tier: str):
    """
    Administrative endpoint to upgrade or downgrade a client's subscription tier.
    Example: /api/admin/apps/uuid-123/tier?tier=PRO
    """
    success = infrastructure_registry.update_app_tier(app_id, tier)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update application tier.")
    return {"success": True, "message": f"Application {app_id} updated to tier {tier}."}

@router.get("/apps/{app_id}")
async def get_app_details(app_id: str):
    """
    Retrieves the full infrastructure and tier configuration for a specific app.
    """
    app = infrastructure_registry.get_app_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"success": True, "data": app}

@router.get("/apps")
async def list_apps():
    """
    Lists all onboarded SaaS instances in the system.
    """
    try:
        from src.infrastructure.db.core_db_manager import core_db_manager
        apps = core_db_manager.execute_raw("SELECT id, name, owner_id FROM apps").mappings().all()
        return {"success": True, "data": [dict(a) for a in apps]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
