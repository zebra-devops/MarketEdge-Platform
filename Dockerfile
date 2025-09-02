FROM python:3.11-slim

# Production Deployment Fix: Optimized base image for fast cold starts
# DEVOPS: Updated 2025-09-02 to resolve deployment issues for £925K opportunity
# Security: Create non-root user early for proper ownership
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

WORKDIR /app

# Lazy Init Optimization: Set environment variables for faster startup
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Lazy Init Optimization: Install minimal system dependencies for faster builds
# Added psutil dependencies for startup performance monitoring
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Security: Copy requirements first for better Docker layer caching
COPY --chown=appuser:appuser requirements.txt .

# Lazy Init Optimization: Install Python packages with optimizations
# Use --no-deps for faster installs where safe, pre-compile bytecode
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m compileall -b /usr/local/lib/python3.11/site-packages/

# Security: Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Security: Create secure log directory with restricted permissions
RUN mkdir -p /var/log/app \
    && chmod 755 /var/log/app \
    && chown appuser:appuser /var/log/app

# Security: Set proper permissions on startup script
RUN chmod 755 start.sh

# Lazy Init Optimization: Optimized health check for faster startup detection
# Reduced start-period for faster deployment detection
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=2 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Security: Switch to non-root user for runtime
USER appuser

# Lazy Initialization Architecture: Optimized Gunicorn deployment
# Pre-load application modules for faster worker startup
RUN python -c "import app.core.lazy_startup; import app.core.startup_metrics" || echo "Optional modules not available"

# STABLE PRODUCTION DEPLOYMENT: Mon 2 Sep 2025 - Option 2 implementation
# DEVOPS: Using stable production version with full API router and minimal dependencies
CMD gunicorn app.main_stable_production:app --config gunicorn_production.conf.py