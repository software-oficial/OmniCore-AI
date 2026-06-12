import logging
from core.dispatcher.gateway import ai_gateway
from .whatsapp_service import whatsapp_service

logger = logging.getLogger("OmniCore.WhatsappCommands")

def register_whatsapp_commands():
    """
    Registers WhatsApp bot functions into the AIGateway.
    """
    ai_gateway.register_command("whatsapp.process", whatsapp_service.process_incoming_message)
    
    logger.info("💬 WhatsApp module commands registered successfully.")
