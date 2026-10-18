# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install curl for Docker HEALTHCHECK probe and clean up apt cache
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Standard Python runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Create dedicated non-root user and group (Principle of Least Privilege)
RUN groupadd -r -g 1001 appuser \
    && useradd -r -u 1001 -g appuser -d /app -s /sbin/nologin appuser

# Install production dependencies first to maximize Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the application source directory with non-root ownership
COPY --chown=appuser:appuser app/ /app/app/

# Switch to non-root user
USER appuser

# Expose internal service port
EXPOSE 8000

# Container-level liveness health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f -s http://127.0.0.1:8000/health/live || exit 1


# Launch application via Gunicorn WSGI in exec form for graceful signal handling
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app.main:app"]
