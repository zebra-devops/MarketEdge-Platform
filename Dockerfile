FROM python:3.11-slim

# Security: Create non-root user early for proper ownership
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

WORKDIR /app

# Security: Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Security: Copy requirements first for better Docker layer caching
COPY --chown=appuser:appuser requirements.txt .

# Security: Install Python packages as non-root where possible
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Security: Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Security: Create secure log directory with restricted permissions
RUN mkdir -p /var/log/app \
    && chmod 755 /var/log/app \
    && chown appuser:appuser /var/log/app

# Security: Set proper permissions on startup script
RUN chmod 755 start.sh

# Security: Health check targeting single service on dynamic port
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Security: Switch to non-root user for runtime
USER appuser

# Single-service deployment: Gunicorn with FastAPI workers
# Use shell form to enable environment variable expansion
CMD gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --access-logfile - --error-logfile - --log-level info