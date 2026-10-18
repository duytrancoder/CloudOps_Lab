"""Application configuration module."""

import os
from dataclasses import dataclass, field
from typing import List

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
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables with safe fallbacks."""
        warnings: List[str] = []

        raw_log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if raw_log_level in VALID_LOG_LEVELS:
            log_level = raw_log_level
        else:
            log_level = "INFO"
            warnings.append(
                f"Invalid LOG_LEVEL '{raw_log_level}'. Falling back to default 'INFO'."
            )

        raw_port = os.getenv("PORT", "8000").strip()
        try:
            port = int(raw_port)
            if port < 1 or port > 65535:
                raise ValueError("Port out of valid range (1-65535)")
        except ValueError:
            port = 8000
            warnings.append(
                f"Invalid PORT '{raw_port}'. Falling back to default 8000."
            )

        return cls(
            app_name=os.getenv("APP_NAME", "CloudOps Lab App").strip(),
            version=os.getenv("APP_VERSION", DEFAULT_APP_VERSION).strip(),
            environment=os.getenv("APP_ENV", "production").strip().lower(),
            log_level=log_level,
            port=port,
            warnings=warnings,
        )
