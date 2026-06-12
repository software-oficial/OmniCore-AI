import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Ensure log directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name: str, log_file: str = "omnicore.log", level=logging.INFO):
    """
    Configures a standardized logger for OmniCore-AI.
    Supports both console output and rotating file storage.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger is called multiple times
    if not logger.handlers:
        # 1. Console Handler for real-time debugging
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 2. Rotating File Handler for persistence (prevents disk overflow)
        file_handler = RotatingFileHandler(
            LOG_DIR / log_file, 
            maxBytes=10*1024*1024, # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        
        # Formatting: [Timestamp] [Level] [LoggerName] [Message]
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger

# Global logger instance for the Engine
engine_logger = setup_logger("OmniCore.Engine")
error_logger = setup_logger("OmniCore.Error", log_file="error.log", level=logging.ERROR)
