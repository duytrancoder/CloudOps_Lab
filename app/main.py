"""Main application module for CloudOps Lab."""

import logging
import sys
import time
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from app.config import AppConfig


def configure_logging(log_level_name: str) -> None:
    """Configure structured logging for standard output.

    Ensures single handler setup to prevent duplicate log lines.
    """
    level = getattr(logging, log_level_name.upper(), logging.INFO)
    logger = logging.getLogger("cloudops_app")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if configure_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Allow propagation so test fixtures (like pytest caplog) can inspect records
    logger.propagate = True


def check_readiness(application: Flask) -> Tuple[bool, Dict[str, Any]]:
    """Evaluate readiness of the service and any registered dependencies.

    Designed for clean extensibility: future dependencies (database, cache, etc.)
    can be registered under application.config['READINESS_CHECKS'] without
    rewriting the route handlers.
    """
    checks: Dict[str, Any] = {
        "initialization": "ready",
    }

    # Evaluate any dynamic readiness checks registered in app configuration
    custom_checks = application.config.get("READINESS_CHECKS", [])
    for check_fn in custom_checks:
        name, is_ok, details = check_fn()
        checks[name] = details
        if not is_ok:
            return False, checks

    return True, checks


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Application factory for the CloudOps Lab Flask service."""
    app_config = config or AppConfig.from_env()

    configure_logging(app_config.log_level)
    logger = logging.getLogger("cloudops_app")

    app = Flask(__name__)
    app.config["APP_CONFIG"] = app_config

    logger.info(
        "Initializing %s (v%s) in '%s' environment with log_level=%s",
        app_config.app_name,
        app_config.version,
        app_config.environment,
        app_config.log_level,
    )

    # Log any fallback warnings detected during config parsing
    for warning_msg in app_config.warnings:
        logger.warning("Configuration fallback: %s", warning_msg)

    @app.before_request
    def log_request_info() -> None:
        """Log incoming request details without leaking sensitive payloads."""
        logger.info(
            "Incoming request: %s %s from %s",
            request.method,
            request.path,
            request.remote_addr,
        )

    @app.route("/", methods=["GET"])
    def index():
        """Root endpoint returning introductory service metadata."""
        return jsonify(
            {
                "app": app_config.app_name,
                "version": app_config.version,
                "environment": app_config.environment,
                "status": "running",
                "message": (
                    "Welcome to CloudOps Lab — "
                    "Automated Deployment, Monitoring & Incident Response API"
                ),
            }
        ), 200

    @app.route("/health/live", methods=["GET"])
    def health_live():
        """Liveness probe.

        Verifies that the web server process is alive, responding to HTTP traffic,
        and not stuck in a deadlock.
        """
        return jsonify(
            {
                "status": "alive",
                "timestamp": time.time(),
            }
        ), 200

    @app.route("/health/ready", methods=["GET"])
    def health_ready():
        """Readiness probe.

        Verifies that the service is ready to accept incoming traffic.
        Returns 200 OK when ready, 503 Service Unavailable when degraded/failing.
        """
        is_ready, details = check_readiness(app)
        status_code = 200 if is_ready else 503
        return jsonify(
            {
                "status": "ready" if is_ready else "not_ready",
                "checks": details,
                "timestamp": time.time(),
            }
        ), status_code

    @app.route("/health", methods=["GET"])
    def health_composite():
        """Composite health check endpoint.

        Aggregates liveness and readiness states into an overarching health report.
        """
        is_ready, details = check_readiness(app)
        status_code = 200 if is_ready else 503
        return jsonify(
            {
                "status": "healthy" if is_ready else "degraded",
                "version": app_config.version,
                "liveness": "alive",
                "readiness": "ready" if is_ready else "not_ready",
                "checks": details,
                "timestamp": time.time(),
            }
        ), status_code

    @app.errorhandler(404)
    def not_found_error(error):
        """Standardized JSON response for 404 Not Found."""
        logger.warning("Resource not found: %s %s", request.method, request.path)
        return jsonify(
            {
                "error": "Not Found",
                "message": "The requested URL was not found on the server.",
                "status_code": 404,
            }
        ), 404

    @app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        """Standardized JSON response for unhandled exceptions (500).

        Preserves full traceback in internal logger for debugging/incident triage,
        while returning a sanitized, secret-free JSON response to the client.
        """
        # Pass standard HTTP exceptions (like 404) to their respective handlers
        if isinstance(error, HTTPException):
            return error

        logger.error(
            "Internal server error encountered on %s %s",
            request.method,
            request.path,
            exc_info=error,
        )
        return jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred on the server.",
                "status_code": 500,
            }
        ), 500

    return app


# Application instance for WSGI servers (Gunicorn)
app = create_app()

if __name__ == "__main__":
    current_config = app.config["APP_CONFIG"]
    app.run(
        host="0.0.0.0",
        port=current_config.port,
        debug=(current_config.environment == "development"),
    )
