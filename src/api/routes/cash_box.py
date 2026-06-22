from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from src.application.cash_box_use_case import CashBoxUseCase
from src.core.auth.token_manager import token_manager
from src.infrastructure.db.core_db_manager import core_db_manager

router = APIRouter(prefix="/api/business/cash_box", tags=["Cash Box"])


# Helper para extraer y validar el token
async def get_token_payload(authorization: str = Header(...)) -> Dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    payload = token_manager.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


class OpenCashRequest(BaseModel):
    monto_inicial: float


class CloseCashRequest(BaseModel):
    monto_real: float


@router.post("/open")
async def open_cash(
    req: OpenCashRequest, payload: Dict[str, Any] = Depends(get_token_payload)
):
    app_id = payload.get("app_id")
    if not app_id:
        raise HTTPException(status_code=401, detail="No app_id in token")

    with core_db_manager.get_session() as session:
        from src.core.dispatcher.core_types import CoreContext

        context = CoreContext(
            business_id=app_id,
            user_id=payload.get("user_id", "system"),
            tier=payload.get("tier", "FREE"),
        )

        use_case = CashBoxUseCase(session, context)
        res = use_case.open_box(req.monto_inicial)

        if not res.success:
            raise HTTPException(status_code=400, detail=res.message)
        return res.to_dict()


@router.post("/close")
async def close_cash(
    req: CloseCashRequest, payload: Dict[str, Any] = Depends(get_token_payload)
):
    app_id = payload.get("app_id")
    if not app_id:
        raise HTTPException(status_code=401, detail="No app_id in token")

    with core_db_manager.get_session() as session:
        from src.core.dispatcher.core_types import CoreContext

        context = CoreContext(
            business_id=app_id,
            user_id=payload.get("user_id", "system"),
            tier=payload.get("tier", "FREE"),
        )

        use_case = CashBoxUseCase(session, context)
        res = use_case.close_box(req.monto_real)

        if not res.success:
            raise HTTPException(status_code=400, detail=res.message)
        return res.to_dict()


@router.get("/status")
async def get_status(payload: Dict[str, Any] = Depends(get_token_payload)):
    app_id = payload.get("app_id")
    if not app_id:
        raise HTTPException(status_code=401, detail="No app_id in token")

    with core_db_manager.get_session() as session:
        from src.core.dispatcher.core_types import CoreContext

        context = CoreContext(
            business_id=app_id,
            user_id=payload.get("user_id", "system"),
            tier=payload.get("tier", "FREE"),
        )

        use_case = CashBoxUseCase(session, context)
        res = use_case.get_status()

        if not res.success:
            raise HTTPException(status_code=400, detail=res.message)
        return res.to_dict()
