"""Functional and unit tests for CloudOps Lab application."""

import logging
import time

from flask.testing import FlaskClient

import app as app_pkg
from app.config import AppConfig
from app.main import create_app


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


def test_health_ready_endpoint_healthy(client: FlaskClient) -> None:
    """Verify that /health/ready probe returns 200 OK when initialized."""
    now = time.time()
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "ready"
    assert data["checks"]["initialization"] == "ready"
    assert isinstance(data["timestamp"], (int, float))
    assert data["timestamp"] >= now - 5


def test_health_ready_extensibility_when_dependency_fails(
    test_config: AppConfig,
) -> None:
    """Verify readiness returns 503 without rewriting routes when a dependency fails."""
    custom_app = create_app(config=test_config)

    # Register a failing readiness check (e.g. database unreachable in future drill)
    def broken_dependency_check():
        return "database", False, "Connection refused: db.internal:5432"

    custom_app.config["READINESS_CHECKS"] = [broken_dependency_check]
    custom_client = custom_app.test_client()

    response = custom_client.get("/health/ready")
    assert response.status_code == 503
    assert response.is_json

    data = response.get_json()
    assert data["status"] == "not_ready"
    assert data["checks"]["database"] == "Connection refused: db.internal:5432"

    # Composite health should also reflect degraded state
    comp_response = custom_client.get("/health")
    assert comp_response.status_code == 503
    comp_data = comp_response.get_json()
    assert comp_data["status"] == "degraded"
    assert comp_data["readiness"] == "not_ready"


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


def test_internal_server_error_500_logs_traceback_and_sanitizes_response(
    test_config: AppConfig, caplog
) -> None:
    """Verify 500 handler preserves traceback in logger and returns secret-free JSON."""
    crash_app = create_app(config=test_config)
    # Set testing=False so Flask delegates exceptions to the errorhandler
    crash_app.config["TESTING"] = False

    @crash_app.route("/test-crash")
    def crash_route():
        raise RuntimeError("Simulated internal crash: secret_db_token_12345")

    client = crash_app.test_client()

    with caplog.at_level(logging.ERROR, logger="cloudops_app"):
        response = client.get("/test-crash")

    assert response.status_code == 500
    assert response.is_json

    data = response.get_json()
    assert data["error"] == "Internal Server Error"
    assert data["status_code"] == 500
    # Client MUST NOT receive raw traceback or internal secret
    assert "secret_db_token" not in data["message"]
    assert "RuntimeError" not in data["message"]

    # Internal logs MUST contain the error and traceback for troubleshooting
    has_error_log = any(
        "Internal server error encountered" in r.message for r in caplog.records
    )
    assert has_error_log
    assert any(record.exc_info is not None for record in caplog.records)


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
    assert len(config.warnings) == 0


def test_version_synchronization_with_env(monkeypatch) -> None:
    """Verify that APP_VERSION updates API response and matches package version."""
    monkeypatch.setenv("APP_VERSION", "2.0.0")

    config = AppConfig.from_env()
    assert config.version == "2.0.0"

    test_app = create_app(config=config)
    test_client = test_app.test_client()

    response = test_client.get("/")
    assert response.get_json()["version"] == "2.0.0"

    health_response = test_client.get("/health")
    assert health_response.get_json()["version"] == "2.0.0"

    # Package version matches configuration
    assert app_pkg.AppConfig.from_env().version == "2.0.0"


def test_config_invalid_fallbacks_and_warnings(monkeypatch) -> None:
    """Verify safe fallbacks and warning collection when given invalid config."""
    monkeypatch.setenv("LOG_LEVEL", "NON_EXISTENT_LEVEL")
    monkeypatch.setenv("PORT", "not-a-number")

    config = AppConfig.from_env()

    assert config.log_level == "INFO"
    assert config.port == 8000
    assert len(config.warnings) == 2
    assert "Invalid LOG_LEVEL" in config.warnings[0]
    assert "Invalid PORT" in config.warnings[1]
