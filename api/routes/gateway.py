from fastapi import APIRouter, Header, Body
from core.dispatcher.gateway import ai_gateway
from core.dispatcher.core_types import ServiceResponse
from core.module_loader import module_loader
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["Gateway"])

@router.get("/gateway/manifest")
async def get_manifest():
    """
    Returns the dynamic manifest of all registered commands.
    Essential for AI Agents to understand the system's capabilities.
    """
    registry = module_loader._command_registry
    manifest = {
        "total_commands": len(registry),
        "commands": [
            {
                "name": name, 
                "metadata": meta if isinstance(meta, dict) else {"handler": "function"}
            } 
            for name, meta in registry.items()
        ]
    }
    return manifest

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
        prefix = name.split('.')[0] if '.' in name else 'general'
        if prefix not in categories:
            categories[prefix] = []
        
        description = meta.get('description', 'No description provided') if isinstance(meta, dict) else 'No description provided'
        schema = meta.get('params_schema', {}) if isinstance(meta, dict) else {}
        
        categories[prefix].append({
            "command": name,
            "description": description,
            "params": schema
        })

    help_guide = {
        "system": "OmniCore-AI Engine",
        "version": "1.0.0",
        "base_url": "/api",
        "instructions": {
            "authentication": {
                "header": "Authorization",
                "format": "Bearer <token> or <token>",
                "description": "Every request must include a valid agent token in the Authorization header."
            },
            "execution_endpoint": {
                "path": "/api/gateway/execute",
                "method": "POST",
                "payload": {
                    "command": "The registered command name (e.g., 'stock.list')",
                    "params": "A dictionary of parameters required by the command"
                },
                "example": {
                    "command": "stock.get",
                    "params": {"product_id": "123"}
                }
            },
            "response_format": {
                "success": True,
                "message": "Human-readable status message",
                "data": "The resulting data from the command execution",
                "error_code": "Machine-readable error code (null on success)",
                "latency_ms": "Processing time in milliseconds"
            }
        },
        "best_practices": {
            "state_management": {
                "guide": "Avoid asking the same question twice. Use 'bot.state.set' to store user data (name, address, cart) and 'bot.state.get' to retrieve it in the next turn.",
                "example_flow": "Settle Name -> bot.state.set(user_id, 'name', 'Juan') -> Next Turn -> bot.state.get(user_id, 'name') -> 'Hola Juan!'"
            },
            "order_of_operations": {
                "complete_sale_flow": [
                    "1. sales.process (Initialize the order)",
                    "2. pay.mp.create (Generate the payment link)",
                    "3. pay.mp.verify (Check if payment was completed)",
                    "4. sales.confirm (Mark order as paid)",
                    "5. stock.update (Decrement inventory)"
                ],
                "onboarding_flow": [
                    "1. /api/dev/clients/onboard (Create client)",
                    "2. /api/dev/clients/{id}/deploy (Setup database tables)",
                    "3. /api/dev/clients/{id}/tokens (Generate agent access)"
                ]
            }
        },
        "available_commands": categories
    }
    return help_guide

@router.post("/gateway/execute")

async def handle_command(
    command: str = Body(..., embed=True),
    params: Dict[str, Any] = Body(..., embed=True),
    authorization: str = Header(None)
):
    if not authorization:
        return ServiceResponse.error_res("Missing Authorization Header", "AUTH_HEADER_MISSING").to_dict()
    
    # Accept both 'Bearer <token>' and direct '<token>'
    token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
    result = await ai_gateway.execute(command, token, params, None)
    return result.to_dict()
