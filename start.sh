#!/bin/bash

# Production startup script for Railway deployment
set -e

echo "Starting Platform Wrapper Backend..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"

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

echo "Starting FastAPI application..."

# PRIORITY 2 FIX: Railway proxy header handling for CORS
export FORWARDED_ALLOW_IPS="*"
export PROXY_HEADERS=1

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level $(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]') \
    --access-log \
    --use-colors \
    --proxy-headers \
    --forwarded-allow-ips="*"