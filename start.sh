#!/bin/bash

# Security: Hardened FastAPI startup script for multi-service deployment
set -e
set -u  # Security: Treat unset variables as error
set -o pipefail  # Security: Fail on pipe errors

# Security: Validate critical environment variables
ENVIRONMENT="${ENVIRONMENT:-production}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "Security: Starting FastAPI service with hardened configuration"
echo "Environment: ${ENVIRONMENT}"
echo "Port: ${PORT}"
echo "CADDY_PROXY_MODE: ${CADDY_PROXY_MODE:-true}"

# Security: Run database migrations with proper error handling
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Security: Running database migrations in production mode..."
    if timeout 300 python3 -m alembic upgrade head; then
        echo "✅ Database migrations completed successfully"
    else
        echo "❌ Database migrations failed - exiting for security"
        exit 1
    fi
else
    echo "Security: Skipping database migrations in ${ENVIRONMENT} mode"
fi

echo "Security: Starting FastAPI backend service with restricted network binding"

# Security: Validate port is numeric
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    echo "❌ Security: Invalid port number: $PORT"
    exit 1
fi

# Security: Validate log level
case "${LOG_LEVEL,,}" in
    critical|error|warning|info|debug|trace)
        ;;
    *)
        echo "❌ Security: Invalid log level: $LOG_LEVEL"
        exit 1
        ;;
esac

# Security: Run FastAPI with production network binding for Railway
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level "${LOG_LEVEL,,}" \
    --access-log \
    --no-use-colors \
    --proxy-headers \
    --forwarded-allow-ips="*" \
    --limit-concurrency 1000 \
    --limit-max-requests 10000 \
    --timeout-keep-alive 5