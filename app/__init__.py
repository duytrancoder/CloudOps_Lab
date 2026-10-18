"""CloudOps Lab Sample Application Package."""

from app.config import AppConfig

# Package-level version is synchronized directly with config
__version__ = AppConfig.from_env().version

from app.main import create_app  # noqa: E402

__all__ = ["create_app", "__version__"]
