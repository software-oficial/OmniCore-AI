import logging
from typing import Any, Dict, Tuple, Optional
from core.dispatcher.core_types import ServiceResponse

logger = logging.getLogger("OmniCore.TypeChecker")

class TypeChecker:
    """
    OmniCore-AI Type Validator.
    Ensures that input parameters match the expected types defined in the command registry.
    """

    # Map of schema type strings to Python types/validators
    TYPE_MAP = {
        "string": str,
        "int": int,
        "float": (int, float),
        "boolean": bool,
        "list": list,
        "dict": dict,
        "optional": object # Handled separately
    }

    @classmethod
    def validate_types(cls, params: Dict[str, Any], schema: Dict[str, str]) -> Tuple[bool, Optional[ServiceResponse]]:
        """
        Validates parameters against the provided schema.
        Returns (isValid, optional_error_response).
        """
        if not schema:
            return True, None

        for param_name, expected_type_str in schema.items():
            # Skip optional parameters if they are missing
            if expected_type_str == "optional" or "optional" in expected_type_str:
                if param_name not in params:
                    continue
            
            if param_name not in params:
                # This should be caught by the handler's signature check, 
                # but we provide a clear error here for the Gateway.
                return False, ServiceResponse.error_res(
                    message=f"Missing required parameter: {param_name}",
                    error_code="MISSING_PARAMETER"
                )

            value = params[param_name]
            
            # Handle complex types (e.g., 'list[dict]')
            if "[" in expected_type_str:
                base_type = expected_type_str.split("[")[0]
                if not cls._check_base_type(value, base_type):
                    return False, cls._type_error_res(param_name, expected_type_str, value)
                continue

            if not cls._check_base_type(value, expected_type_str):
                return False, cls._type_error_res(param_name, expected_type_str, value)

        return True, None

    @classmethod
    def _check_base_type(cls, value: Any, type_str: str) -> bool:
        """Internal helper to validate basic types."""
        target_type = cls.TYPE_MAP.get(type_str.lower())
        if not target_type:
            return True # If type is unknown, we allow it (fail-open for extensibility)
            
        return isinstance(value, target_type)

    @classmethod
    def _type_error_res(cls, param: str, expected: str, actual: Any) -> ServiceResponse:
        """Generates a standardized type error response."""
        actual_type = type(actual).__name__
        return ServiceResponse.error_res(
            message=f"Invalid type for parameter '{param}'. Expected {expected}, got {actual_type} ('{actual}').",
            error_code="INVALID_TYPE"
        )

type_checker = TypeChecker()
