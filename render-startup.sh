#!/bin/bash

# Render-specific startup script for proper service initialization
set -e
set -u
set -o pipefail

echo "🚀 Render deployment startup script"
echo "PORT: ${PORT:-80}"
echo "FASTAPI_PORT: ${FASTAPI_PORT:-8000}"

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