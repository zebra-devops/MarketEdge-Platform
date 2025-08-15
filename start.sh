#!/bin/bash

# FastAPI startup script for supervisord multi-service deployment
set -e

echo "Starting FastAPI service..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"
echo "CORS-001: Multi-Service Configuration Active"

# Run database migrations before starting the application
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running database migrations..."
    if python3 -m alembic upgrade head; then
        echo "✅ Database migrations completed"
    else
        echo "❌ Database migrations failed"
        exit 1
    fi
fi

echo "Starting FastAPI backend service..."

# CORS-001: FastAPI runs as internal service behind Caddy proxy
export FORWARDED_ALLOW_IPS="*"
export PROXY_HEADERS=1

# Run FastAPI on internal port 8000 (Caddy proxies from port 80)
exec uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --log-level $(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]') \
    --access-log \
    --use-colors \
    --proxy-headers \
    --forwarded-allow-ips="127.0.0.1"