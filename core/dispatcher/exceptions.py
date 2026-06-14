import logging
import traceback
from typing import Optional, Any
from core.dispatcher.core_types import ServiceResponse

logger = logging.getLogger("OmniCore.Exceptions")

class OmniCoreException(Exception):
    """Base exception for all OmniCore-AI errors."""
    def __init__(self, message: str, error_code: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code

class GovernanceException(OmniCoreException):
    """Raised when a governance check fails."""
    pass

class InfrastructureException(OmniCoreException):
    """Raised when infrastructure or DB connection fails."""
    pass

class ModuleException(OmniCoreException):
    """Raised when a business module encounters a logic error."""
    pass

class SchemaException(OmniCoreException):
    """Raised when the external DB schema is outdated."""
    pass

def handle_omnicore_exception(e: Exception) -> ServiceResponse:
    """
    Universal handler to convert exceptions into standardized ServiceResponse.
    MASKING: Hides stack traces and system internals from the client.
    """
    # Log the full trace internally
    logger.error("SYSTEM_ERROR", exc_info=True)

    if isinstance(e, OmniCoreException):
        # We allow the specific message for expected business exceptions
        return ServiceResponse.error_res(e.message, e.error_code)

    # Generic response for unexpected errors
    return ServiceResponse.error_res(
        message="An internal system error occurred. Please contact technical support.", 
        error_code="INTERNAL_SERVER_ERROR"
    )
