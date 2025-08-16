FROM python:3.11-slim

# Security: Create non-root user early for proper ownership
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

WORKDIR /app

# Security: Install system dependencies with minimal privileges
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    supervisor \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    ca-certificates \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends caddy \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first for better Docker layer caching
COPY platform-wrapper/backend/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all backend files
COPY --chown=appuser:appuser platform-wrapper/backend/ .

# Create necessary directories
RUN mkdir -p /var/log/supervisor /var/log/caddy /var/run \
    && chmod 755 /var/log/supervisor /var/log/caddy \
    && chown appuser:appuser /var/log/supervisor /var/log/caddy

# Create supervisord configuration directory
RUN mkdir -p /etc/supervisor/conf.d \
    && chmod 755 /etc/supervisor/conf.d

# Copy supervisord configuration
COPY --chown=root:root platform-wrapper/backend/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set proper permissions
RUN chmod 755 start.sh \
    && chmod 644 /etc/supervisor/conf.d/supervisord.conf \
    && chmod 644 Caddyfile

# Expose ports
EXPOSE 80 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run supervisord as root for process management
USER root
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]