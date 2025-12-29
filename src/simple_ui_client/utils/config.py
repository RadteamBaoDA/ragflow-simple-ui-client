"""
Configuration management using Pydantic-Settings.

Loads settings from environment variables and .env files with validation.
Provides a singleton pattern for accessing application configuration.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Type alias for log levels (PEP 695)
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        websocket_api_key: API key for WebSocket authentication.
        websocket_url: URL of the Simple UI WebSocket server.
        user_email: Optional user email for identification.
        log_level: Logging verbosity level.
        json_logs: Enable JSON format for logs (daemon mode).
        simple_ui_home: Base directory for Simple UI client data.
        pid_file: Path to the PID file for daemon mode.
        reconnect_max_delay: Maximum delay between reconnection attempts (seconds).
        ping_interval: WebSocket ping interval (seconds).
        ping_timeout: WebSocket ping timeout (seconds).
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # WebSocket Configuration
    websocket_api_key: str = Field(
        default="",
        description="API key for WebSocket authentication",
    )
    websocket_url: str = Field(
        default="ws://localhost:3000",
        description="URL of the Simple UI WebSocket server",
    )
    user_email: str = Field(
        default="",
        description="User email for identification",
    )
    
    # Logging Configuration
    log_level: LogLevel = Field(
        default="INFO",
        description="Logging verbosity level",
    )
    log_rotation: str = Field(
        default="00:00",
        description="Log rotation interval or size (e.g., '00:00', '10 MB')",
    )
    log_filename_template: str = Field(
        default="simple-ui-client_{time:YYYYMMDDHHmmss}.log",
        description="Template for log filenames (supports {time} tokens)",
    )
    log_retention: str = Field(
        default="1 year",
        description="Log retention period (e.g., '1 year', '30 days')",
    )
    log_compression: str = Field(
        default="gz",
        description="Log compression format (e.g., 'gz', 'zip')",
    )
    json_logs: bool = Field(
        default=False,
        description="Enable JSON format for logs (daemon mode)",
    )
    
    # Path Configuration
    simple_ui_home: Path = Field(
        default_factory=lambda: Path.home() / ".simple-ui",
        description="Base directory for Simple UI client data",
    )
    log_dir: Path | None = Field(
        default=None,
        description="Explicit directory for log files (overrides default)",
    )
    
    # Connection Configuration
    reconnect_max_delay: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Maximum delay between reconnection attempts (seconds)",
    )
    ping_interval: int = Field(
        default=25,
        ge=5,
        le=60,
        description="WebSocket ping interval (seconds)",
    )
    ping_timeout: int = Field(
        default=60,
        ge=10,
        le=120,
        description="WebSocket ping timeout (seconds)",
    )
    
    @field_validator("log_level", mode="before")
    @classmethod
    def uppercase_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v
    
    @property
    def pid_file(self) -> Path:
        """Path to the PID file for daemon mode."""
        return self.simple_ui_home / "client.pid"
    
    @property
    def effective_log_dir(self) -> Path:
        """Path to the effective log directory (explicit or default)."""
        if self.log_dir:
            return self.log_dir
        return self.simple_ui_home / "logs"
    
    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.simple_ui_home.mkdir(parents=True, exist_ok=True)
        self.effective_log_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
