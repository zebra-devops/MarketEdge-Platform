#!/bin/bash

# Production startup script for Railway deployment
set -e

echo "Starting Platform Wrapper Backend..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"
echo "Workers: ${WORKERS:-4}"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --worker-class uvicorn.workers.UvicornWorker \
    --log-level ${LOG_LEVEL:-info} \
    --access-log \
    --use-colors \
    --loop asyncio