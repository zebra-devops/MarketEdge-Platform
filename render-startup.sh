#!/bin/bash

# Render Production Startup Script
# Includes emergency migration deployment

echo "🚀 MarketEdge Platform Starting..."
echo "🔧 Checking for emergency migrations..."

# Check if this is a migration deployment
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🚨 EMERGENCY MIGRATION MODE"
    echo "🎯 Creating analytics_modules table"

    python3 apply_production_migrations_emergency.py
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo "✅ Emergency migrations completed successfully"
        echo "🎉 analytics_modules table created"
    else
        echo "❌ Emergency migrations failed"
        exit 1
    fi
fi

# Normal startup
echo "🟢 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
