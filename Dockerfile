FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Caddy and supervisord
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    supervisor \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update \
    && apt-get install -y caddy \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Create supervisord configuration directory
RUN mkdir -p /etc/supervisor/conf.d

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create Caddyfile
COPY Caddyfile /app/Caddyfile

# Create non-root user for services (supervisord runs as root, services as appuser)
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Create log directories for supervisor
RUN mkdir -p /var/log/supervisor /var/log/caddy
RUN chown -R appuser:appuser /var/log/supervisor /var/log/caddy

# Expose ports - Caddy (80/443) and FastAPI (8000)
EXPOSE 80 443 8000

# Health check for Railway - check both services
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/health || curl -f http://localhost:${PORT:-8000}/health || exit 1

# Production command using supervisord for multi-service management
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]