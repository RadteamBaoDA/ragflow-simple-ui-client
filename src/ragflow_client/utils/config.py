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
        websocket_url: URL of the RAGFlow WebSocket server.
        user_email: Optional user email for identification.
        log_level: Logging verbosity level.
        json_logs: Enable JSON format for logs (daemon mode).
        ragflow_home: Base directory for RAGFlow client data.
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
        description="URL of the RAGFlow WebSocket server",
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
    json_logs: bool = Field(
        default=False,
        description="Enable JSON format for logs (daemon mode)",
    )
    
    # Path Configuration
    ragflow_home: Path = Field(
        default_factory=lambda: Path.home() / ".ragflow",
        description="Base directory for RAGFlow client data",
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
        return self.ragflow_home / "client.pid"
    
    @property
    def log_dir(self) -> Path:
        """Path to the log directory."""
        return self.ragflow_home / "logs"
    
    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.ragflow_home.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
