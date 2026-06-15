from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Response, Request

from src.core.dispatcher.gateway import ai_gateway

router = APIRouter(prefix="/api/business", tags=["Business REST API"])

# ... (rest of the file remains the same, but I will apply a broad replace for the execute calls)

router = APIRouter(prefix="/api/business", tags=["Business REST API"])


async def get_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return (
        authorization.split(" ")[1]
        if authorization.startswith("Bearer ")
        else authorization
    )


# --- Resource: Products ---


@router.get("/products")
async def list_products(request: Request, response: Response, token: str = Depends(get_token)):
    """
    GET /api/business/products
    Lists all products. Implements HTTP caching.
    """
    # Cache for 60 seconds
    response.headers["Cache-Control"] = "public, max-age=60"

    result = await ai_gateway.execute("stock.list", token, {}, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.get("/products/{code}")
async def get_product(code: str, request: Request, response: Response, token: str = Depends(get_// la respuesta se cortó aquí por el límite de tokens, pero el objetivo es corregir la llamada.
    result = await ai_gateway.execute("stock.get", token, {"code": code}, request)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result.to_// la respuesta se cortó aquí por el límite de tokens, pero el objetivo es corregir la llamada.


@router.post("/products")
async def create_product(
    payload: Dict[str, Any] = Body(...), token: str = Depends(get_token)
):
    """
    POST /api/business/products
    Adds a new product to the inventory.
    """
    result = await ai_gateway.execute("stock.add", token, payload, None)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.patch("/products/{code}")
async def update_product(
    code: str, payload: Dict[str, Any] = Body(...), token: str = Depends(get_token)
):
    """
    PATCH /api/business/products/{code}
    Updates product details or quantity.
    """
    params = {"code": code, **payload}
    result = await ai_gateway.execute("stock.update", token, params, None)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Sales ---


@router.post("/sales")
async def process_sale(
    payload: Dict[str, Any] = Body(...), token: str = Depends(get_token)
):
    """
    POST /api/business/sales
    Processes a complete sale.
    """
    result = await ai_gateway.execute("sales.process", token, payload, None)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.post("/sales/pending")
async def create_pending_sale(
    payload: Dict[str, Any] = Body(...), token: str = Depends(get_token)
):
    """
    POST /api/business/sales/pending
    Creates a draft sale.
    """
    result = await ai_gateway.execute("sales.pending", token, payload, None)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.patch("/sales/{sale_id}/confirm")
async def confirm_sale(sale_id: str, token: str = Depends(get_token)):
    """
    PATCH /api/business/sales/{sale_id}/confirm
    Confirms payment and finalizes the sale.
    """
    result = await ai_gateway.execute(
        "sales.confirm", token, {"sale_id": sale_id}, None
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()
