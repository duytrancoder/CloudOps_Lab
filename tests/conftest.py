"""Pytest fixtures for CloudOps Lab."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import AppConfig
from app.main import create_app


@pytest.fixture
def test_config() -> AppConfig:
    """Fixture providing a deterministic test configuration."""
    return AppConfig(
        app_name="CloudOps Lab Test App",
        version="1.0.0-test",
        environment="testing",
        log_level="DEBUG",
        port=8000,
    )


@pytest.fixture
def app(test_config: AppConfig) -> Flask:
    """Fixture creating a test-configured Flask application."""
    application = create_app(config=test_config)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Fixture providing Flask HTTP test client."""
    return app.test_client()
