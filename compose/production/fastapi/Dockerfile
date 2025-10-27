# Multi-stage build for production FastAPI
# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./

# Install dependencies using UV
RUN uv pip install --system -r pyproject.toml

# Production stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy entrypoint and start scripts
COPY compose/production/fastapi/entrypoint.sh /entrypoint
COPY compose/production/fastapi/start /start
COPY compose/production/fastapi/celery/worker/start /start-celeryworker
COPY compose/production/fastapi/celery/beat/start /start-celerybeat

# Convert line endings, make scripts executable, and set ownership
RUN sed -i 's/\r$//' /entrypoint /start /start-celeryworker /start-celerybeat && \
    chmod +x /entrypoint /start /start-celeryworker /start-celerybeat && \
    chown appuser:appuser /entrypoint /start /start-celeryworker /start-celerybeat

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["/entrypoint"]
