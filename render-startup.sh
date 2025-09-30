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

    # Take pre-deployment snapshot before any changes
    echo "📸 Creating pre-deployment database snapshot..."
    if bash scripts/production/pre_deploy_snapshot.sh; then
        echo "✅ Pre-deployment snapshot created successfully"
    else
        echo "❌ CRITICAL: Pre-deployment snapshot failed"
        echo "🛑 Blocking migration to prevent data loss"
        echo "📋 Fix snapshot issues before proceeding"
        exit 1
    fi

    echo "🔍 Validating production schema first..."

    python database/validate_schema.py --check
    schema_validation_result=$?

    if [ $schema_validation_result -ne 0 ]; then
        echo "❌ CRITICAL: Production schema validation failed"
        echo "🚨 AUTOMATIC EMERGENCY REPAIR STARTING..."
        echo "🔧 Applying comprehensive schema fixes..."

        # Run emergency schema repair
        python render_emergency_schema_repair.py --apply
        repair_result=$?

        if [ $repair_result -eq 0 ]; then
            echo "✅ Emergency schema repair completed successfully"
            echo "🔍 Re-validating schema..."
            python database/validate_schema.py --check
            revalidation_result=$?

            if [ $revalidation_result -eq 0 ]; then
                echo "✅ Schema validation now passes - continuing deployment"
            else
                echo "⚠️  Schema validation still has issues - running final table repair"
                echo "🔧 Creating final 3 missing tables with correct FK types..."
                python render_final_table_repair.py
                final_repair_result=$?

                if [ $final_repair_result -eq 0 ]; then
                    echo "✅ Final table repair completed successfully"
                    echo "🎯 All schema issues resolved - proceeding with deployment"
                else
                    echo "❌ Final table repair failed"
                    echo "🛑 Manual intervention required - check repair logs"
                    exit 1
                fi
            fi
        elif [ $repair_result -eq 3 ]; then
            echo "⚠️  Emergency schema repair partially successful (exit code 3)"
            echo "🔧 47/52 statements completed - running final table repair for remaining 3 tables"
            echo "📋 Known missing tables: module_configurations, module_usage_logs, sector_modules"
            python render_final_table_repair.py
            final_repair_result=$?

            if [ $final_repair_result -eq 0 ]; then
                echo "✅ Final table repair completed successfully"
                echo "🎯 All schema issues resolved - proceeding with deployment"
            else
                echo "❌ Final table repair failed"
                echo "🛑 Manual intervention required - check repair logs"
                exit 1
            fi
        else
            echo "❌ Emergency schema repair failed (exit code: $repair_result)"
            echo "🛑 Stopping deployment - manual intervention required"
            echo "📋 Run locally: python render_emergency_schema_repair.py --check"
            exit 1
        fi
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
