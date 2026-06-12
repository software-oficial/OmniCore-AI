from fastapi import APIRouter
from typing import Dict

router = APIRouter(prefix="/api/agent", tags=["Agent"])

@router.get("/manifest")
async def get_manifest():
    """
    Returns the Semantic Business Manifest for AI Agents.
    """
    return {
        "ontology": "Business-as-a-Service (BaaS) for Stock, Bot, and Payments",
        "modes": {
            "LEARNING": "Sandbox mode for AI exploration. No real DB impact.",
            "PRODUCTION": "Live mode. Real DB impact, billed by usage."
        },
        "commands": {
            "stock.add": {
                "description": "Adds a product to the developer's inventory.",
                "params": {"name": "string", "price": "float", "quantity": "int"},
                "example": {"name": "Laptop", "price": 1200.50, "quantity": 10}
            }
        }
    }
