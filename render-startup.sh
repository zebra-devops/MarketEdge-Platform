#!/bin/bash

# Render-specific startup script with deployment mode detection
set -e
set -u
set -o pipefail

echo "🚀 Render deployment startup script"
echo "PORT: ${PORT:-80}"
echo "CADDY_PROXY_MODE: ${CADDY_PROXY_MODE:-true}"

# Detect deployment mode based on CADDY_PROXY_MODE
if [ "${CADDY_PROXY_MODE:-true}" = "false" ]; then
    echo "🔧 Single-service mode: Starting FastAPI directly on port ${PORT:-80}"
    
    # Set FastAPI port to Render's PORT
    export FASTAPI_PORT="${PORT:-80}"
    
    # Ensure proper permissions for app user
    chown -R appuser:appuser /app
    
    # Switch to app user and start FastAPI directly
    exec su -s /bin/bash -c "cd /app && ./start.sh" appuser
else
    echo "🔧 Multi-service mode: Starting Caddy + FastAPI with supervisord"
    export FASTAPI_PORT="${FASTAPI_PORT:-8000}"
    
    # Ensure proper permissions for log directories
    mkdir -p /var/log/caddy /var/log/supervisor
    chown -R appuser:appuser /var/log/caddy
    chmod 755 /var/log/supervisor /var/log/caddy

    # Test port availability
    echo "🔍 Testing port availability..."
    if netstat -tuln | grep -q ":${PORT:-80} "; then
        echo "⚠️  Port ${PORT:-80} already in use"
    else
        echo "✅ Port ${PORT:-80} is available"
    fi

    # Start supervisord with proper configuration
    echo "🔧 Starting supervisord for multi-service deployment..."
    exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi