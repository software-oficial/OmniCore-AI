# Decorator for marking functions as API commands.
# This allows the ModuleLoader to automatically discover and register them.

from functools import wraps
from typing import Any, Callable, Dict, Optional


def command(
    name: str,
    description: str = "No description provided",
    params_schema: Optional[Dict[str, Any]] = None,
    is_system: bool = False,
):
    """
    Decorates a function to mark it as an OmniCore-AI API command.
    The ModuleLoader will automatically detect this decorator and register the function.
    """

    def decorator(func: Callable):
        # Cast to Any to allow dynamic attribute assignment for metadata
        f: Any = func
        # Attach metadata to the function object itself
        f._is_omnicore_command = True
        f._command_name = name
        f._command_description = description
        f._command_params_schema = params_schema or {}
        f._command_is_system = is_system
        return wraps(func)(func)

    return decorator
