#!/bin/bash

# Render Startup Script
# Supports both production and preview/staging environments

echo "🚀 MarketEdge Platform Starting..."
echo "🔧 Environment: ${ENVIRONMENT:-production}"

# Environment-specific startup logic
if [ "$ENVIRONMENT" = "staging" ] || [ "$USE_STAGING_AUTH0" = "true" ]; then
    echo "🔄 STAGING/PREVIEW ENVIRONMENT DETECTED"
    echo "📊 Auth0 Environment: staging"
    echo "🔐 Using staging Auth0 credentials"

    # Run migrations for staging
    echo "🗃️  Running staging database migrations..."
    alembic upgrade head

    # Seed with test data for staging
    echo "🌱 Seeding staging environment with test data..."
    python database/seeds/initial_data.py
    python database/seeds/phase3_data.py

    echo "✅ Staging environment setup complete"
elif [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🚨 EMERGENCY MIGRATION MODE (PRODUCTION)"
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
else
    echo "🟢 PRODUCTION ENVIRONMENT"
    echo "📊 Auth0 Environment: production"
    echo "🔐 Using production Auth0 credentials"
fi

# Display environment configuration for validation
echo "📋 Environment Configuration:"
echo "   ENVIRONMENT: ${ENVIRONMENT:-production}"
echo "   USE_STAGING_AUTH0: ${USE_STAGING_AUTH0:-false}"
echo "   AUTH0_DOMAIN: ${AUTH0_DOMAIN:-not-set}"
echo "   CORS_ORIGINS: ${CORS_ORIGINS:-not-set}"

# Normal startup
echo "🟢 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
