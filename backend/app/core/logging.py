"""
Logging configuration using Loguru.
"""

import sys
from loguru import logger

from app.core.config import settings


def setup_logging():
    """Configure structured logging for the application."""

    # Remove default handler
    logger.remove()

    # Console handler with colored output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )

    # File handler for persistent logs
    logger.add(
        "logs/aegisscan.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        compression="gz",
    )

    return logger


# Initialize logger
log = setup_logging()
