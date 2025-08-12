"""Configuration settings for Metabase MCP Server."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the Metabase MCP server."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Metabase Settings - REQUIRED
    METABASE_URL: str
    METABASE_API_KEY: str

    # API Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # MCP Server Configuration
    MCP_SERVER_NAME: str = "metabase-mcp"
    MCP_TRANSPORT: Literal["streamable-http", "stdio"] = "streamable-http"

    # HTTP Client Configuration (for per-request clients)
    HTTP_CONNECT_TIMEOUT: float = Field(
        default=10.0, ge=1.0, le=60.0, description="Connection timeout in seconds"
    )
    HTTP_READ_TIMEOUT: float = Field(
        default=30.0, ge=5.0, le=300.0, description="Read timeout in seconds"
    )
    HTTP_ENABLE_HTTP2: bool = Field(
        default=False, description="Enable HTTP/2 support for better performance"
    )


def get_settings() -> Settings:
    """Factory function to create settings instance."""
    return Settings()  # type: ignore


# Create settings instance - works in both test and non-test environments
settings = get_settings()
