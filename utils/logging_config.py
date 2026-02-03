"""
Centralized logging configuration for all modules.
Provides a simple interface to set up consistent loggers across the project.
"""

import logging
import sys


def setup_logging(name: str | None = None) -> logging.Logger:
    """
    Set up and return a logger with standard formatting.
    
    Args:
        name: Logger name. Defaults to "battleship-match" if None.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name or "battleship-match")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
