import logging
from typing import Any, Dict, Optional, Tuple

from src.core.dispatcher.core_types import ServiceResponse
from src.infrastructure.validation.sanitizer import sanitizer
from src.infrastructure.validation.type_checker import type_checker

logger = logging.getLogger("OmniCore.RequestValidator")


class RequestValidator:
    """
    Handles request validation: Sanity checks, sanitization,
    type checking, and mass assignment prevention.
    """

    @staticmethod
    def validate(
        command_name: str, params: Dict[str, Any], cmd_schema: Any
    ) -> Tuple[bool, Optional[ServiceResponse], Dict[str, Any]]:
        """
        Validates request parameters.
        Supports both legacy dict schemas and strict Pydantic models.
        Returns (isValid, errorResponse, cleanedParams).
        """

        # 1. Sanity Filter
        if params:
            sanity_keywords = {"price", "quantity", "amount", "total", "stock", "cost"}
            for key, value in params.items():
                if any(kw in key.lower() for kw in sanity_keywords):
                    try:
                        if float(value) < 0:
                            return (
                                False,
                                ServiceResponse.error_res(
                                    message=f"🚫 SANITY ERROR: Field '{key}' cannot have a negative value ({value}).",
                                    error_code="INVALID_DATA_RANGE",
                                ),
                                {},
                            )
                    except (ValueError, TypeError):
                        pass

            # 2. Sanitization
            params = sanitizer.sanitize_params(params)

        # 3. Validation & Mass Assignment Filtering
        if command_name and params:
            # CASE A: Strict Pydantic Model Validation
            from pydantic import BaseModel, ValidationError

            if isinstance(cmd_schema, type) and issubclass(cmd_schema, BaseModel):
                try:
                    # Validate and parse using Pydantic
                    model_instance = cmd_schema(**params)
                    # Convert back to dict to maintain compatibility with existing handlers
                    filtered_params = model_instance.model_dump()
                    return True, None, filtered_params
                except ValidationError as e:
                    # Transform Pydantic error into a pedagogical ServiceResponse
                    error_details = e.errors()
                    msg = "Validation failed: " + "; ".join(
                        [f"{err['loc'][0]}: {err['msg']}" for err in error_details]
                    )
                    return (
                        False,
                        ServiceResponse.error_res(
                            message=f"🚫 CONTRACT ERROR: {msg}",
                            error_code="CONTRACT_VIOLATION",
                        ),
                        {},
                    )

            # CASE B: Legacy Dict Schema Validation
            if isinstance(cmd_schema, dict):
                # Strict Type Validation
                is_valid_type, type_err = type_checker.validate_types(
                    params, cmd_schema
                )
                if not is_valid_type:
                    return False, type_err, {}

                # Strict Parameter Filtering (Anti-Mass Assignment)
                filtered_params = {k: v for k, v in params.items() if k in cmd_schema}
                if len(filtered_params) != len(params):
                    logger.warning(
                        f"⚠️ Mass Assignment Attempt blocked for {command_name}. Dropped keys: {set(params.keys()) - set(cmd_schema.keys())}"
                    )

                return True, None, filtered_params

        return True, None, params
