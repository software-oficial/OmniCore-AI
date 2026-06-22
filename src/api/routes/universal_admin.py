from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.system.universal_admin_service import universal_admin_service

router = APIRouter(prefix="/api/admin", tags=["Universal Admin"])


class SetupRequest(BaseModel):
    username: str
    password: str
    business_name: str
    plan: Optional[str] = "FREE"


class EmployeeRequest(BaseModel):
    business_id: str
    username: str
    password: str
    role: Optional[str] = "EMPLOYEE"


class CredentialsRequest(BaseModel):
    business_id: str
    provider: str
    data: Dict[str, Any]


class StockRequest(BaseModel):
    business_id: str
    sku: str
    data: Dict[str, Any]


@router.post("/setup")
async def setup(req: SetupRequest):
    res = universal_admin_service.setup_business_and_owner(
        req.username, req.password, req.business_name, req.plan or "FREE"
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.to_dict()


@router.post("/employees/add")
async def add_employee(req: EmployeeRequest):
    res = universal_admin_service.add_employee(
        req.business_id, req.username, req.password, req.role
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.to_dict()


@router.post("/credentials/set")
async def set_credentials(req: CredentialsRequest):
    res = universal_admin_service.set_credentials(
        req.business_id, req.provider, req.data
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.to_dict()


@router.post("/stock/sync")
async def sync_stock(req: StockRequest):
    res = universal_admin_service.sync_stock(req.business_id, req.sku, req.data)
    if not res.success:
        raise HTTPException(status_code=400, detail=res.message)
    return res.to_dict()
