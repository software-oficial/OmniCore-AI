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
        # Attach metadata to the function object itself
        func._is_omnicore_command = True
        func._command_name = name
        func._command_description = description
        func._command_params_schema = params_schema or {}
        func._command_is_system = is_system
        return wraps(func)(func)

    return decorator
