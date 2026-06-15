import logging
from typing import Tuple

logger = logging.getLogger("OmniCore.CommandNormalizer")


class CommandNormalizer:
    """
    Handles translation of command aliases to official command names.
    This keeps the Gateway clean and focused on orchestration.
    """

    ALIASES = {
        "ventas": "sales",
        "caja": "cash",
        "infraestructura": "infrastructure",
        "infra": "infrastructure",
        "bot": "bot",
        "whatsapp": "whatsapp",
    }

    @classmethod
    def normalize(cls, command_name: str) -> Tuple[str, bool]:
        """Translates aliases to official command names. Returns (normalized_name, was_aliased)."""
        if not command_name or "." not in command_name:
            return command_name, False

        prefix, suffix = command_name.split(".", 1)
        if prefix in cls.ALIASES:
            return f"{cls.ALIASES[prefix]}.{suffix}", True
        return command_name, False
