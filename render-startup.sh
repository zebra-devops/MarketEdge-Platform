#!/bin/bash

# Render Startup Script
# Supports both production and preview/staging environments

echo "🚀 MarketEdge Platform Starting..."
echo "🔧 Environment: ${ENVIRONMENT:-production}"
echo "🐍 Python version: $(python --version 2>&1)"

# Environment-specific startup logic
if [ "$ENVIRONMENT" = "staging" ] || [ "$USE_STAGING_AUTH0" = "true" ]; then
    echo "🔄 STAGING/PREVIEW ENVIRONMENT DETECTED"
    echo "📊 Auth0 Environment: staging"
    echo "🔐 Using staging Auth0 credentials"

    # Schema validation and migrations for staging
    echo "🔍 Validating database schema..."
    python database/validate_schema.py --check
    schema_validation_result=$?

    if [ $schema_validation_result -ne 0 ]; then
        echo "⚠️  Schema validation issues detected"
        echo "🔧 Generating schema fixes..."
        python database/validate_schema.py --fix > /tmp/schema_fixes.sql

        if [ -s /tmp/schema_fixes.sql ]; then
            echo "📄 Schema fixes generated, applying baseline schema..."
            python database/generate_baseline.py --apply
            baseline_result=$?

            if [ $baseline_result -ne 0 ]; then
                echo "❌ Failed to apply baseline schema"
                exit 1
            fi

            echo "✅ Baseline schema applied successfully"
        fi
    else
        echo "✅ Schema validation passed"
    fi

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
    echo "🔍 Validating production schema first..."

    python database/validate_schema.py --check
    schema_validation_result=$?

    if [ $schema_validation_result -ne 0 ]; then
        echo "❌ CRITICAL: Production schema validation failed"
        echo "🛑 Stopping deployment - manual intervention required"
        echo "📋 Run locally: python database/validate_schema.py --check"
        echo "🔧 Generate fixes: python database/validate_schema.py --fix"
        exit 1
    fi

    echo "✅ Production schema validation passed"
    echo "🎯 Proceeding with emergency migration"

    python apply_production_migrations_emergency.py
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

    # For regular production startup, do a quick schema validation
    echo "🔍 Quick production schema validation..."
    python database/validate_schema.py --check
    if [ $? -ne 0 ]; then
        echo "⚠️  Production schema validation warnings detected"
        echo "📋 Check logs and run: python database/validate_schema.py --check"
        echo "🚀 Continuing startup (non-blocking for production)"
    else
        echo "✅ Production schema validation passed"
    fi
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
