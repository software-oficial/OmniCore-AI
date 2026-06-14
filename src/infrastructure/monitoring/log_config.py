import logging
from src.infrastructure.monitoring.logger import setup_logger

# Configure system-wide logging for all modules
logging.basicConfig(level=logging.INFO)

#- Specialized loggers for different components
logger_core = setup_logger("OmniCore.Core")
logger_infra = setup_logger("OmniCore.Infra")
logger_modules = setup_logger("OmniCore.Modules")

def get_logger(name: str):
    """Helper to get a configured logger based on the component name."""
    if "core" in name.lower():
        return logger_core
    elif "infra" in name.lower():
        return logger_infra
    else:
        return logger_modules
