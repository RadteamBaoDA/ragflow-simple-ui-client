"""
Structured logging setup using Loguru.

Provides JSON-formatted logs for daemon mode and human-readable logs for
interactive mode. Supports rotating file handlers and customizable log levels.
"""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from simple_ui_client.utils.config import Settings


def setup_logger(
    settings: "Settings",
    *,
    daemon_mode: bool = False,
) -> None:
    """
    Configure the Loguru logger based on application settings.
    
    Args:
        settings: Application settings containing log configuration.
        daemon_mode: If True, suppress console output and enable JSON logs.
    """
    # Remove default handler
    logger.remove()
    
    # Ensure log directory exists
    settings.ensure_directories()
    
    # Console handler (only in non-daemon mode)
    if not daemon_mode:
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
        )
    
    # File handler with rotation
    log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    
    if settings.json_logs or daemon_mode:
        # JSON format for daemon mode / production
        logger.add(
            settings.effective_log_dir / settings.log_filename_template,
            level=settings.log_level,
            format=log_format,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
            serialize=True,  # JSON output
        )
    else:
        # Human-readable format
        logger.add(
            settings.effective_log_dir / settings.log_filename_template,
            level=settings.log_level,
            format=log_format,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression=settings.log_compression,
        )
    
    logger.info(
        f"Logger initialized | level={settings.log_level} | "
        f"daemon_mode={daemon_mode} | json_logs={settings.json_logs}"
    )


def get_logger(name: str = "simple_ui_client") -> "logger":
    """
    Get a contextualized logger instance.
    
    Args:
        name: The name/context for the logger.
        
    Returns:
        A Loguru logger instance bound to the given name.
    """
    return logger.bind(name=name)
