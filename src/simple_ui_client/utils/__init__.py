"""
Utility modules for Simple UI client.

Provides configuration management and structured logging.
"""

from simple_ui_client.utils.config import Settings, get_settings
from simple_ui_client.utils.logger import setup_logger, get_logger

__all__ = ["Settings", "get_settings", "setup_logger", "get_logger"]
