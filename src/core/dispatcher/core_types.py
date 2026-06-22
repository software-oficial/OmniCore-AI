from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class ServiceResponse(Generic[T]):
    """
    Standardized Response for OmniCore-AI.
    Designed to be parsed by both AI Agents and Human Developers.
    """

    def __init__(
        self,
        success: bool,
        message: str,
        data: Optional[T] = None,
        error_code: Optional[str] = None,
        guide: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        debug_info: Optional[Any] = None,
    ):
        self.success = success
        self.message = message
        self.data = data
        self.error_code = error_code
        self.guide = guide  # Used in LEARNING_MODE for pedagogical feedback
        self.latency_ms = latency_ms
        self.debug_info = debug_info

    @classmethod
    def success_res(
        cls,
        data: Optional[T] = None,
        message: str = "Operation successful",
        latency_ms: Optional[float] = None,
        debug_info: Optional[Any] = None,
    ):
        return cls(
            success=True,
            message=message,
            data=data,
            latency_ms=latency_ms,
            debug_info=debug_info,
        )

    @classmethod
    def error_res(
        cls,
        message: str,
        error_code: str = "GENERAL_ERROR",
        guide: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None,
        debug_info: Optional[Any] = None,
    ):
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            guide=guide,
            latency_ms=latency_ms,
            debug_info=debug_info,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error_code": self.error_code,
            "guide": self.guide,
            "latency_ms": self.latency_ms,
            "debug_info": self.debug_info,
        }


class CoreContext:
    """
    The 'Passport' of every request.
    Carries the identity and infrastructure config across the system.
    Simplified for Unified Universal Schema (UUS).
    """

    def __init__(
        self,
        user_id: str,
        business_id: str,
        role: str = "EMPLOYEE",
        tier: str = "FREE",
        permissions: Optional[List[str]] = None,
        entity: str = "API",
        mode: str = "PRODUCTION",
        settings: Optional[Dict[str, Any]] = None,
        execution_strategy: str = "DIRECT",
    ):
        self.user_id = user_id
        self.business_id = business_id
        self.app_id = business_id  # Aliased for backward compatibility with domains
        self.role = role
        self.tier = tier
        self.permissions = permissions or []
        self.entity = entity
        self.mode = mode  # 'LEARNING' or 'PRODUCTION'
        self.settings = settings or {}
        self.execution_strategy = execution_strategy
        self.active_credentials: Dict[str, Any] = {}
        self.credential_id: Optional[str] = None

    @property
    def agent_id(self) -> str:
        return self.user_id
