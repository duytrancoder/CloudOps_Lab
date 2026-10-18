"""Functional and unit tests for CloudOps Lab application."""

import time

from flask.testing import FlaskClient

from app.config import AppConfig


def test_index_endpoint(client: FlaskClient, test_config: AppConfig) -> None:
    """Verify that root endpoint returns introductory metadata with 200 OK."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["app"] == test_config.app_name
    assert data["version"] == test_config.version
    assert data["environment"] == test_config.environment
    assert data["status"] == "running"
    assert "CloudOps Lab" in data["message"]


def test_health_live_endpoint(client: FlaskClient) -> None:
    """Verify that /health/live probe returns alive status."""
    now = time.time()
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "alive"
    assert isinstance(data["timestamp"], (int, float))
    assert data["timestamp"] >= now - 5


def test_health_ready_endpoint(client: FlaskClient) -> None:
    """Verify that /health/ready probe returns ready status."""
    now = time.time()
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "ready"
    assert isinstance(data["timestamp"], (int, float))
    assert data["timestamp"] >= now - 5


def test_health_composite_endpoint(client: FlaskClient, test_config: AppConfig) -> None:
    """Verify that composite /health endpoint aggregates liveness and readiness."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["version"] == test_config.version
    assert data["liveness"] == "alive"
    assert data["readiness"] == "ready"
    assert isinstance(data["timestamp"], (int, float))


def test_not_found_returns_json_404(client: FlaskClient) -> None:
    """Verify that 404 errors return a clean JSON payload instead of default HTML."""
    response = client.get("/non-existent-endpoint-123")

    assert response.status_code == 404
    assert response.is_json

    data = response.get_json()
    assert data["error"] == "Not Found"
    assert data["status_code"] == 404
    assert "not found" in data["message"].lower()


def test_config_defaults(monkeypatch) -> None:
    """Verify default values when environment variables are unset."""
    for key in ["APP_NAME", "APP_VERSION", "APP_ENV", "LOG_LEVEL", "PORT"]:
        monkeypatch.delenv(key, raising=False)

    config = AppConfig.from_env()

    assert config.app_name == "CloudOps Lab App"
    assert config.version == "1.0.0"
    assert config.environment == "production"
    assert config.log_level == "INFO"
    assert config.port == 8000


def test_config_custom_env(monkeypatch) -> None:
    """Verify loading custom environment variables."""
    monkeypatch.setenv("APP_NAME", "Custom App")
    monkeypatch.setenv("APP_VERSION", "2.1.0")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("PORT", "9090")

    config = AppConfig.from_env()

    assert config.app_name == "Custom App"
    assert config.version == "2.1.0"
    assert config.environment == "staging"
    assert config.log_level == "DEBUG"
    assert config.port == 9090


def test_config_invalid_fallbacks(monkeypatch) -> None:
    """Verify safe fallbacks when given invalid log level or non-numeric port."""
    monkeypatch.setenv("LOG_LEVEL", "NON_EXISTENT_LEVEL")
    monkeypatch.setenv("PORT", "not-a-number")

    config = AppConfig.from_env()

    assert config.log_level == "INFO"
    assert config.port == 8000
