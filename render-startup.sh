#!/bin/bash

# DEPRECATED: Single-service architecture migration complete
# This script is no longer used - Gunicorn starts directly from Dockerfile
# Architecture migrated from: Caddy + supervisord + FastAPI
# Architecture migrated to: Gunicorn + FastAPI (single service)

echo "⚠️  DEPRECATED: render-startup.sh is no longer used"
echo "🔄 Architecture migrated to single-service deployment"
echo "✅ Gunicorn starts directly from Dockerfile CMD"
echo "📦 Single service: Gunicorn + FastAPI on PORT=${PORT:-8000}"

# If this script is somehow called, fall back to Gunicorn startup
echo "🔧 Fallback: Starting Gunicorn directly..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --access-logfile - --error-logfile - --log-level info