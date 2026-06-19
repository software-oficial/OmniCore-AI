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
    """

    def __init__(
        self,
        agent_id: str,
        app_id: str,
        dev_id: str,
        mode: str,
        db_config: Optional[Dict[str, Any]] = None,
        tier: str = "FREE",
        permissions: Optional[List[str]] = None,
        entity: str = "API",
        execution_strategy: str = "DIRECT",
        settings: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.user_id = agent_id  # Defaulting user_id to agent_id
        self.app_id = app_id
        self.dev_id = dev_id
        self.mode = mode  # 'LEARNING' or 'PRODUCTION'
        self.db_config = db_config  # Host, User, Pass, etc.
        self.tier = tier
        self.permissions = permissions or []
        self.entity = entity
        self.execution_strategy = execution_strategy
        self.settings = settings or {}
        self.active_credentials: Dict[str, Any] = {}
        self.credential_id: Optional[str] = None
