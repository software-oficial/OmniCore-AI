from fastapi import APIRouter, Depends
from core.telemetry.telemetry_service import telemetry_service
from infra.db.db_manager import db_manager
from typing import Dict, Any

router = APIRouter(prefix="/api/admin", tags=["Admin Monitoring"])

@router.get("/metrics")
async def get_system_metrics():
    """
    Returns real-time system metrics for the Administrative Dashboard.
    Includes concurrency, request volume, and resource load.
    """
    # 1. Get Telemetry Data from Redis
    metrics = telemetry_service.get_realtime_metrics()
    
    # 2. Get Infrastructure Data (Hot Store)
    # We check the current number of active engines in the pool
    infra_status = {
        "active_db_pools": len(db_manager._engines),
        "system_status": "HEALTHY" if len(db_manager._engines) < 100 else "HIGH_LOAD"
    }
    
    return {
        "telemetry": metrics,
        "infrastructure": infra_status
    }
