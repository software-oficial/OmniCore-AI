from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Body, Header

from src.core.dispatcher.core_types import ServiceResponse
from src.core.dispatcher.gateway import ai_gateway
from src.core.module_loader import module_loader

router = APIRouter(prefix="/api", tags=["Gateway"])


@router.get("/gateway/openapi")
async def get_openapi():
    """
    Generates a full OpenAPI 3.0 specification of the Gateway's command-driven API.
    This allows developers to use Swagger UI or Postman to explore and test the API.
    """
    registry = module_loader._command_registry

    # Base OpenAPI structure
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "OmniCore-AI Gateway API",
            "description": "Command-driven API for AI Agents and Developers to manage business logic.",
            "version": "1.0.0",
        },
        "servers": [{"url": "/api"}],
        "components": {
            "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
            "schemas": {
                "ServiceResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"},
                        "data": {"type": "object", "nullable": True},
                        "error_code": {"type": "string", "nullable": True},
                        "latency_ms": {"type": "number"},
                    },
                }
            },
        },
        "security": [{"BearerAuth": []}],
        "paths": {},
    }

    # We model the Gateway as a single endpoint that takes a command name and params.
    # However, for better DX, we can represent each command as a virtual path.
    for name, meta in registry.items():
        if not isinstance(meta, dict):
            continue

        description = meta.get("description", "No description provided")
        params_schema = meta.get("params_schema", {})

        # Create a virtual path for each command to make it visible in Swagger
        # e.g., /gateway/execute/stock.add
        path = f"/gateway/execute/{name}"

        # Map our simple type hints to OpenAPI types
        properties = {}
        for p_name, p_type in params_schema.items():
            oa_type = "string"
            if p_type == "float":
                oa_type = "number"
            elif p_type == "int":
                oa_type = "integer"
            elif p_type == "boolean":
                oa_type = "boolean"
            elif "list" in p_type:
                oa_type = "array"

            properties[p_name] = {"type": oa_type}

        openapi_spec["paths"][path] = {
            "post": {
                "summary": f"Execute {name}",
                "description": description,
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": properties,
                                "required": [
                                    p
                                    for p, t in params_schema.items()
                                    if t != "optional"
                                ],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ServiceResponse"
                                }
                            }
                        },
                    }
                },
            }
        }

    return openapi_spec


@router.get("/gateway/help")
async def get_help():
    """
    Provides comprehensive usage instructions for the OmniCore-AI Gateway.
    This endpoint is designed to be consumed by AI Agents to bootstrap their integration.
    """
    registry = module_loader._command_registry

    # Categorize commands by their prefix (e.g., 'stock', 'sales', 'bot')
    categories = {}
    for name, meta in registry.items():
        prefix = name.split(".")[0] if "." in name else "general"
        if prefix not in categories:
            categories[prefix] = []

        description = (
            meta.get("description", "No description provided")
            if isinstance(meta, dict)
            else "No description provided"
        )
        schema = meta.get("params_schema", {}) if isinstance(meta, dict) else {}

        categories[prefix].append(
            {"command": name, "description": description, "params": schema}
        )

    help_guide = {
        "system": "OmniCore-AI Engine",
        "version": "1.0.0",
        "base_url": "/api",
        "instructions": {
            "authentication": {
                "header": "Authorization",
                "format": "Bearer <token> or <token>",
                "description": "Every request must include a valid agent token in the Authorization header.",
            },
            "execution_endpoint": {
                "path": "/api/gateway/execute",
                "method": "POST",
                "payload": {
                    "command": "The registered command name (e.g., 'stock.list')",
                    "params": "A dictionary of parameters required by the command",
                },
                "example": {"command": "stock.get", "params": {"product_id": "123"}},
            },
            "response_format": {
                "success": True,
                "message": "Human-readable status message",
                "data": "The resulting data from the command execution",
                "error_code": "Machine-readable error code (null on success)",
                "latency_ms": "Processing time in milliseconds",
            },
        },
        "best_practices": {
            "state_management": {
                "guide": "Avoid asking the same question twice. Use 'bot.state.set' to store user data (name, address, cart) and 'bot.state.get' to retrieve it in the next turn.",
                "example_flow": "Settle Name -> bot.state.set(user_id, 'name', 'Juan') -> Next Turn -> bot.state.get(user_id, 'name') -> 'Hola Juan!'",
            },
            "order_of_operations": {
                "complete_sale_flow": [
                    "1. sales.process (Initialize the order)",
                    "2. pay.mp.create (Generate the payment link)",
                    "3. pay.mp.verify (Check if payment was completed)",
                    "4. sales.confirm (Mark order as paid)",
                    "5. stock.update (Decrement inventory)",
                ],
                "onboarding_flow": [
                    "1. /api/dev/clients/onboard (Create client)",
                    "2. /api/dev/clients/{id}/deploy (Setup database tables)",
                    "3. /api/dev/clients/{id}/tokens (Generate agent access)",
                ],
            },
        },
        "available_commands": categories,
    }
    return help_guide


@router.get("/gateway/inspect/{command}")
async def inspect_command(command: str):
    """
    ODDS Pilar 2: Detailed inspection of a command's contract.
    Returns required/optional parameters, types, and examples.
    Now PUBLIC to ensure seamless auto-learning.
    """
    registry = module_loader._command_registry
    if command not in registry:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Command {command} not found")

    meta = registry[command]
    schema = meta.get("params_schema", {})

    # Process parameters to handle nested structures (lists of dicts)
    processed_types = {}
    required = []
    optional = []

    for p_name, p_val in schema.items():
        if isinstance(p_val, dict) and p_val.get("type") == "list":
            # Handle nested list schema
            item_schema = p_val.get("item_schema", {})
            type_desc = f"list of objects: {item_schema}"
            processed_types[p_name] = type_desc
            required.append(p_name)  # Assume lists are required if defined this way
        else:
            # Standard type
            processed_types[p_name] = p_val
            if p_val == "optional":
                optional.append(p_name)
            else:
                required.append(p_name)

    return {
        "command": command,
        "required_params": required,
        "optional_params": optional,
        "types": processed_types,
        "example": meta.get("example"),
    }


@router.post("/gateway/execute")
async def handle_command(
    command: Optional[str] = Body(None, embed=True),
    params: Optional[Dict[str, Any]] = Body(None, embed=True),
    flow: Optional[List[Dict[str, Any]]] = Body(None, embed=True),
    authorization: str = Header(None),
    x_omnicore_mode: Optional[str] = Header(None),
):
    if not authorization:
        return ServiceResponse.error_res(
            "Missing Authorization Header", "AUTH_HEADER_MISSING"
        ).to_dict()

    # Accept both 'Bearer <token>' and direct '<token>'
    token = (
        authorization.split(" ")[1]
        if authorization.startswith("Bearer ")
        else authorization
    )

    from fastapi import Request

    # Pass all possible execution modes to the gateway
    result = await ai_gateway.execute(
        command_name=command,
        token=token,
        params=params,
        request=cast(Any, Request({"type": "http"})),
        flow=flow,
        requested_mode=x_omnicore_mode,
    )
    return result.to_dict()
