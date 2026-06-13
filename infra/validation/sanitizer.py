import logging
import re
import html
from typing import Any

logger = logging.getLogger("OmniCore.Sanitizer")

class InputSanitizer:
    """
    OmniCore-AI Input Sanitizer.
    Prevents XSS and injection attacks by cleaning string inputs.
    """
    
    # Basic pattern to detect HTML tags
    HTML_TAG_PATTERN = re.compile(r'<[^>]*?>')

    @classmethod
    def sanitize_string(cls, value: Any) -> Any:
        """
        Sanitizes a value if it's a string. 
        Removes HTML tags and escapes special characters.
        """
        if not isinstance(value, str):
            return value
        
        # 1. Remove HTML tags entirely to prevent XSS
        clean_value = cls.HTML_TAG_PATTERN.sub('', value)
        
        # 2. Escape HTML special characters (e.g., < becomes &lt;)
        clean_value = html.escape(clean_value)
        
        if clean_value != value:
            logger.warning(f"⚠️ Input Sanitized: '{value}' -> '{clean_value}'")
            
        return clean_value

    @classmethod
    def sanitize_params(cls, params: dict) -> dict:
        """Recursively sanitizes all string values in a dictionary."""
        if not params:
            return params
            
        sanitized = {}
        for k, v in params.items():
            if isinstance(v, dict):
                sanitized[k] = cls.sanitize_params(v)
            elif isinstance(v, list):
                sanitized[k] = [cls.sanitize_string(i) if isinstance(i, str) else i for i in v]
            else:
                sanitized[k] = cls.sanitize_string(v)
        
        return sanitized

sanitizer = InputSanitizer()
