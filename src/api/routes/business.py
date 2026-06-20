from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, Response

from src.core.dispatcher.gateway import ai_gateway

router = APIRouter(prefix="/api/business", tags=["Business REST API"])


async def get_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return (
        authorization.split(" ")[1]
        if authorization.startswith("Bearer ")
        else authorization
    )


# --- Resource: Business Settings ---


@router.get("/settings")
async def get_business_settings(
    request: Request, response: Response, token: str = Depends(get_token)
):
    """
    GET /api/business/settings
    Retrieves all dynamic configuration variables for the business.
    """
    response.headers["Cache-Control"] = "no-cache"

    result = await ai_gateway.execute("system.settings.get", token, {}, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.patch("/settings")
async def update_business_setting(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    PATCH /api/business/settings
    Updates or creates a business configuration variable.
    Payload: {key, value, description}
    """
    result = await ai_gateway.execute("system.settings.set", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Credentials Management ---


@router.get("/credentials")
async def list_credentials(
    request: Request,
    response: Response,
    token: str = Depends(get_token),
    provider: Optional[str] = None,
):
    """
    GET /api/business/credentials
    Lists all service credentials for the business.
    Supports filtering by provider (e.g., ?provider=mercadopago).
    """
    response.headers["Cache-Control"] = "no-cache"

    params = {"provider": provider}
    result = await ai_gateway.execute("system.credentials.list", token, params, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.post("/credentials")
async def create_credential(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/credentials
    Creates a new service credential.
    Payload: {account_name, provider, api_key, secret, metadata, is_default}
    """
    result = await ai_gateway.execute(
        "system.credentials.create", token, payload, request
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    request: Request,
    token: str = Depends(get_token),
):
    """
    DELETE /api/business/credentials/{credential_id}
    Removes a service credential.
    """
    params = {"credential_id": credential_id}
    result = await ai_gateway.execute(
        "system.credentials.delete", token, params, request
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Team Management ---


@router.get("/team")
async def list_team(
    request: Request, response: Response, token: str = Depends(get_token)
):
    """
    GET /api/business/team
    Lists all employees and their permissions.
    """
    response.headers["Cache-Control"] = "no-cache"

    result = await ai_gateway.execute("user.list", token, {}, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.post("/team")
async def create_employee(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/team
    Adds a new employee to the business.
    Payload: {username, password, role}
    """
    result = await ai_gateway.execute("user.create_employee", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.patch("/team/{username}/role")
async def update_employee_role(
    username: str,
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    PATCH /api/business/team/{username}/role
    Updates the role of a specific employee.
    Payload: {role}
    """
    params = {"username": username, **payload}
    result = await ai_gateway.execute("user.change_role", token, params, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Audit Trail ---


@router.get("/audit")
async def get_audit_logs(
    request: Request,
    response: Response,
    token: str = Depends(get_token),
    limit: int = 50,
    offset: int = 0,
    command: Optional[str] = None,
):
    """
    GET /api/business/audit
    Retrieves the audit trail of all commands executed for this business.
    Supports pagination and optional filtering by command name.
    """
    response.headers["Cache-Control"] = "no-cache"

    params = {"limit": limit, "offset": offset, "command": command}
    result = await ai_gateway.execute("system.audit.get_logs", token, params, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Stock Import ---


@router.post("/import/preview")
async def preview_stock_import(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/import/preview
    Uploads raw data and receives a suggested mapping and preview.
    Payload: {raw_data: List[Dict], custom_mapping: Optional[Dict]}
    """
    result = await ai_gateway.execute("stock.import.preview", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.post("/import/execute")
async def execute_stock_import(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/import/execute
    Performs the final bulk import using a confirmed mapping.
    Payload: {raw_data: List[Dict], mapping: Dict}
    """
    result = await ai_gateway.execute("stock.import.execute", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Products ---


@router.get("/products")
async def list_products(
    request: Request, response: Response, token: str = Depends(get_token)
):
    """
    GET /api/business/products
    Lists all products. Implements HTTP caching.
    """
    response.headers["Cache-Control"] = "public, max-age=60"

    result = await ai_gateway.execute("stock.list", token, {}, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.get("/products/{code}")
async def get_product(
    code: str, request: Request, response: Response, token: str = Depends(get_token)
):
    """
    GET /api/business/products/{code}
    Retrieves a specific product by its business code.
    """
    response.headers["Cache-Control"] = "public, max-age=30"

    result = await ai_gateway.execute("stock.get", token, {"code": code}, request)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result.to_dict()


@router.post("/products")
async def create_product(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/products
    Adds a new product to the inventory.
    """
    result = await ai_gateway.execute("stock.add", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.patch("/products/{code}")
async def update_product(
    code: str,
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    PATCH /api/business/products/{code}
    Updates product details or quantity.
    """
    params = {"code": code, **payload}
    result = await ai_gateway.execute("stock.update", token, params, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


# --- Resource: Sales ---


@router.post("/sales")
async def process_sale(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/sales
    Processes a complete sale.
    """
    result = await ai_gateway.execute("venta.cobrar", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.post("/sales/pending")
async def create_pending_sale(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    token: str = Depends(get_token),
):
    """
    POST /api/business/sales/pending
    Creates a draft sale.
    """
    result = await ai_gateway.execute("sales.pending", token, payload, request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()


@router.patch("/sales/{sale_id}/confirm")
async def confirm_sale(sale_id: str, request: Request, token: str = Depends(get_token)):
    """
    PATCH /api/business/sales/{sale_id}/confirm
    Confirms payment and finalizes the sale.
    """
    result = await ai_gateway.execute(
        "sales.confirm", token, {"sale_id": sale_id}, request
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.to_dict()
