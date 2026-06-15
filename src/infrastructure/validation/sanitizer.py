import html
import logging
from typing import Any, Dict

logger = logging.getLogger("OmniCore.Sanitizer")


class InputSanitizer:
    """
    OmniCore-AI Input Sanitizer.
    Prevents XSS and injection attacks by escaping HTML characters.
    """

    @classmethod
    def sanitize_string(cls, value: Any) -> Any:
        """
        Robust sanitization to prevent XSS.
        Escapes all HTML special characters to ensure they are rendered as text.
        """
        if not isinstance(value, str):
            return value

        original_value = value
        # The ultimate defense: < becomes &lt;, > becomes &gt;, etc.
        # This prevents any HTML from being injected and executed.
        final_value = html.escape(original_value)

        if final_value != original_value:
            logger.warning(
                f"🛡️ XSS Attack Blocked/Sanitized: '{original_value}' -> '{final_value}'"
            )

        return final_value

    @classmethod
    def sanitize_params(cls, params: dict) -> dict:
        """Recursively sanitizes all string values in a dictionary."""
        if not params:
            return params

        sanitized: Dict[Any, Any] = {}
        for k, v in params.items():
            if isinstance(v, dict):
                sanitized[k] = cls.sanitize_params(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    cls.sanitize_string(i) if isinstance(i, str) else i for i in v
                ]
            else:
                sanitized[k] = cls.sanitize_string(v)

        return sanitized


sanitizer = InputSanitizer()
