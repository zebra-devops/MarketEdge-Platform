#!/bin/bash

# Render Startup Script - Production and Staging
# Handles both production and preview environments

echo "🚀 MarketEdge Platform Starting..."
echo "🌍 Environment: ${ENVIRONMENT:-production}"

# Determine environment type
if [ "$ENVIRONMENT" = "staging" ]; then
    echo "🧪 STAGING MODE - Preview Environment"
    STARTUP_MODE="staging"
else
    echo "🔐 PRODUCTION MODE"
    STARTUP_MODE="production"
fi

# Check if this is a migration deployment
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "🔧 Running database migrations..."

    if [ "$STARTUP_MODE" = "staging" ]; then
        echo "🧪 Staging migration setup"

        # Run standard migrations for staging
        echo "⬆️  Running Alembic migrations..."
        alembic upgrade head
        migration_exit=$?

        if [ $migration_exit -eq 0 ]; then
            echo "✅ Staging migrations completed"

            # Setup staging database with test data
            echo "📦 Setting up staging database..."
            python3 database/staging_setup.py
            setup_exit=$?

            if [ $setup_exit -eq 0 ]; then
                echo "✅ Staging database setup complete"
            else
                echo "⚠️  Staging database setup failed, continuing with basic setup"
                # Continue anyway for staging - seed basic data
                python3 database/seeds/initial_data.py || echo "⚠️  Basic seeding failed"
            fi
        else
            echo "❌ Staging migrations failed"
            exit 1
        fi

    else
        echo "🚨 PRODUCTION MIGRATION MODE"
        echo "🎯 Running production migrations"

        # Production-specific migration logic
        if [ -f "apply_production_migrations_emergency.py" ]; then
            python3 apply_production_migrations_emergency.py
            exit_code=$?
        else
            # Standard migration path
            alembic upgrade head
            exit_code=$?
        fi

        if [ $exit_code -eq 0 ]; then
            echo "✅ Production migrations completed successfully"
        else
            echo "❌ Production migrations failed"
            exit 1
        fi
    fi
fi

# Environment-specific startup configuration
if [ "$STARTUP_MODE" = "staging" ]; then
    echo "🧪 Configuring staging environment..."

    # Enable debug logging for staging
    export LOG_LEVEL="DEBUG"
    export ENABLE_CORS_DEBUG="true"

    # Use staging-specific Auth0 configuration if available
    if [ -n "$AUTH0_DOMAIN_STAGING" ]; then
        export AUTH0_DOMAIN="$AUTH0_DOMAIN_STAGING"
        export AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID_STAGING"
        export AUTH0_CLIENT_SECRET="$AUTH0_CLIENT_SECRET_STAGING"
        export AUTH0_AUDIENCE="$AUTH0_AUDIENCE_STAGING"
        echo "✅ Using staging Auth0 configuration"
    fi

    echo "🧪 Staging configuration complete"

    # Start with single worker for staging (resource efficiency)
    echo "🟢 Starting FastAPI application (staging mode)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level debug

else
    echo "🔐 Configuring production environment..."

    # Production logging configuration
    export LOG_LEVEL="INFO"

    echo "🔐 Production configuration complete"

    # Start with single worker for production (free tier limitation)
    echo "🟢 Starting FastAPI application (production mode)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

fi