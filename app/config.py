"""Application configuration module."""

import os
from dataclasses import dataclass

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
DEFAULT_APP_VERSION = "1.0.0"


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""

    app_name: str
    version: str
    environment: str
    log_level: str
    port: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables with sensible defaults."""
        raw_log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        log_level = raw_log_level if raw_log_level in VALID_LOG_LEVELS else "INFO"

        raw_port = os.getenv("PORT", "8000").strip()
        try:
            port = int(raw_port)
        except ValueError:
            port = 8000

        return cls(
            app_name=os.getenv("APP_NAME", "CloudOps Lab App").strip(),
            version=os.getenv("APP_VERSION", DEFAULT_APP_VERSION).strip(),
            environment=os.getenv("APP_ENV", "production").strip().lower(),
            log_level=log_level,
            port=port,
        )
