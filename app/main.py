"""Main application module for CloudOps Lab."""

import logging
import sys
import time
from typing import Optional

from flask import Flask, jsonify, request

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

    # Prevent propagation to root logger to avoid duplicated logs
    logger.propagate = False


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

        Verifies that the service is ready to accept user requests.
        At this stage, there are no mandatory external dependencies (e.g. database),
        so readiness confirms internal initialization is complete.
        """
        return jsonify(
            {
                "status": "ready",
                "timestamp": time.time(),
            }
        ), 200

    @app.route("/health", methods=["GET"])
    def health_composite():
        """Composite health check endpoint.

        Provides an aggregated status report combining liveness and readiness states.
        """
        return jsonify(
            {
                "status": "healthy",
                "version": app_config.version,
                "liveness": "alive",
                "readiness": "ready",
                "timestamp": time.time(),
            }
        ), 200

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

    @app.errorhandler(500)
    def internal_error(error):
        """Standardized JSON response for 500 Internal Server Error."""
        logger.error(
            "Internal server error encountered on %s %s",
            request.method,
            request.path,
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
