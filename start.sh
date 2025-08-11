#!/bin/bash

# Production startup script for Railway deployment
set -e

echo "Starting Platform Wrapper Backend..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"

# Start the application without migrations first (for health check)
# Railway health checks need the app to respond quickly
echo "Starting FastAPI application..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level $(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]') \
    --access-log \
    --use-colors