FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml ./

# Install dependencies using UV
RUN uv pip install --system -r pyproject.toml

# Copy entrypoint and start scripts
COPY compose/local/fastapi/entrypoint.sh /entrypoint
COPY compose/local/fastapi/start /start
COPY compose/local/fastapi/celery/worker/start /start-celeryworker
COPY compose/local/fastapi/celery/beat/start /start-celerybeat
COPY compose/local/fastapi/celery/flower/start /start-flower

# Convert line endings and make scripts executable
RUN sed -i 's/\r$//' /entrypoint /start /start-celeryworker /start-celerybeat /start-flower && \
    chmod +x /entrypoint /start /start-celeryworker /start-celerybeat /start-flower

# Copy application code
COPY . .

ENTRYPOINT ["/entrypoint"]
