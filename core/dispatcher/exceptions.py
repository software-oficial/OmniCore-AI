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
    Includes stack trace for detailed debugging.
    """
    stack_trace = traceback.format_exc()

    if isinstance(e, OmniCoreException):
        return ServiceResponse.error_res(e.message, e.error_code, debug_info=stack_trace)

    logger.exception(f"Unhandled system error: {str(e)}")
    return ServiceResponse.error_res(
        message=f"An internal system error occurred: {str(e)}", 
        error_code="INTERNAL_SERVER_ERROR",
        debug_info=stack_trace
    )
