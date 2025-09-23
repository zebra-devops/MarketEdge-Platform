#!/usr/bin/env python3
"""
Deploy Schema Repair to Render Production
========================================

This script creates a deployment-ready schema repair that can be executed
on Render's production environment. It uses the existing production_schema_repair.py
but adds Render-specific deployment capabilities.

Usage:
    # Generate deployment script for Render
    python deploy_schema_repair_to_render.py --generate

    # Execute repair directly (if DATABASE_URL is available)
    python deploy_schema_repair_to_render.py --execute

Exit Codes:
    0: Success
    1: Schema validation failed or fixes needed
    2: Database connection failed
    3: Critical error during repair
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_filename = f'render_schema_repair_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_filename)
    ]
)
logger = logging.getLogger(__name__)

def create_render_deployment_script():
    """Create a standalone script that can be deployed to Render"""

    deployment_script = '''#!/bin/bash

# Render Schema Repair Deployment Script
# This script applies comprehensive schema fixes to production database

echo "🚀 MarketEdge Schema Repair - Render Production"
echo "⏰ Started: $(date)"
echo "🔧 Environment: ${ENVIRONMENT:-production}"

# Verify we're in production environment
if [ "$ENVIRONMENT" != "production" ] && [ -z "$FORCE_REPAIR" ]; then
    echo "❌ ERROR: This script is designed for production only"
    echo "💡 Set FORCE_REPAIR=true to override for staging"
    exit 1
fi

# Verify DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    echo "💡 Ensure DATABASE_URL is configured in Render environment group"
    exit 2
fi

echo "✅ Environment validation passed"
echo "📊 DATABASE_URL configured: YES"

# Run comprehensive schema validation first
echo "🔍 Running production schema validation..."
python database/production_schema_repair.py --dry-run

validation_result=$?
if [ $validation_result -eq 0 ]; then
    echo "✅ Production schema is valid - no repairs needed"
    echo "🎉 Deployment complete"
    exit 0
elif [ $validation_result -eq 1 ]; then
    echo "⚠️  Schema issues detected - proceeding with repair"
else
    echo "❌ Critical validation error - aborting"
    exit $validation_result
fi

# Create backup timestamp
backup_timestamp=$(date +"%Y%m%d_%H%M%S")
echo "📋 Backup timestamp: $backup_timestamp"

# Apply schema repairs
echo "🔧 Applying schema repairs to production database..."
python database/production_schema_repair.py --apply

repair_result=$?
if [ $repair_result -eq 0 ]; then
    echo "✅ Schema repairs applied successfully"

    # Verify the fixes
    echo "🔍 Verifying schema repairs..."
    python database/production_schema_repair.py --dry-run

    verify_result=$?
    if [ $verify_result -eq 0 ]; then
        echo "✅ Schema verification passed"
        echo "🎉 Production schema repair completed successfully"
        echo "📊 Log file: $log_filename"
        exit 0
    else
        echo "❌ Schema verification failed after repair"
        echo "🚨 Manual intervention required"
        exit 3
    fi
else
    echo "❌ Schema repair failed"
    echo "📋 Check logs for details"
    exit $repair_result
fi
'''

    # Write the deployment script
    script_path = Path("render_schema_repair_deploy.sh")
    script_path.write_text(deployment_script)
    script_path.chmod(0o755)

    logger.info(f"✅ Deployment script created: {script_path}")
    return script_path

def create_render_yaml_update():
    """Create render.yaml configuration for schema repair deployment"""

    render_config = '''
# Add this to your render.yaml for schema repair deployment

services:
  - type: web
    name: marketedge-schema-repair
    env: python-3.11
    plan: free
    buildCommand: "pip install --upgrade pip && pip install -r requirements.txt"
    startCommand: ./render_schema_repair_deploy.sh
    envVars:
      - fromGroup: production-env
      - key: FORCE_REPAIR
        value: "true"
      - key: RUN_MIGRATIONS
        value: "false"  # Schema repair, not migrations
'''

    config_path = Path("render_schema_repair.yaml")
    config_path.write_text(render_config)

    logger.info(f"✅ Render config created: {config_path}")
    return config_path

def execute_schema_repair():
    """Execute schema repair directly if DATABASE_URL is available"""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not set - cannot execute repair")
        logger.info("💡 Use --generate to create deployment scripts for Render")
        return False

    # Import and run the production schema repair
    sys.path.append(str(Path(__file__).parent))

    try:
        from database.production_schema_repair import ProductionSchemaRepairer

        logger.info("🔍 Initializing production schema repair...")
        repairer = ProductionSchemaRepairer(database_url)

        # Validate current schema
        logger.info("🔍 Validating current production schema...")
        validation_results = repairer.validate_current_schema()

        if validation_results['total_issues'] == 0:
            logger.info("✅ Production schema is valid - no repairs needed")
            return True

        logger.warning(f"⚠️  Found {validation_results['total_issues']} schema issues:")
        logger.warning(f"   - Missing tables: {len(validation_results['missing_tables'])}")
        logger.warning(f"   - Missing columns: {sum(len(cols) for cols in validation_results['missing_columns'].values())}")

        # Generate repair SQL
        logger.info("🔧 Generating schema repair SQL...")
        repair_sql = repairer.generate_repair_sql(validation_results)

        # Apply repairs
        logger.info("🚀 Applying schema repairs to production...")
        success = repairer.apply_repairs(repair_sql, dry_run=False)

        if success:
            logger.info("✅ Schema repairs applied successfully")

            # Verify fixes
            logger.info("🔍 Verifying schema repairs...")
            post_validation = repairer.validate_current_schema()

            if post_validation['total_issues'] == 0:
                logger.info("✅ Schema verification passed - repair complete")
                return True
            else:
                logger.error(f"❌ {post_validation['total_issues']} issues remain after repair")
                return False
        else:
            logger.error("❌ Schema repair failed")
            return False

    except Exception as e:
        logger.error(f"❌ Critical error during repair: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Deploy schema repair to Render production")
    parser.add_argument("--generate", action="store_true", help="Generate deployment scripts for Render")
    parser.add_argument("--execute", action="store_true", help="Execute schema repair directly")

    args = parser.parse_args()

    if not any([args.generate, args.execute]):
        args.generate = True  # Default to generate

    try:
        if args.generate:
            logger.info("🛠️  Generating Render deployment scripts...")

            script_path = create_render_deployment_script()
            config_path = create_render_yaml_update()

            logger.info("✅ Deployment scripts generated successfully!")
            logger.info("📋 Next steps:")
            logger.info(f"   1. Upload {script_path} to your Render service")
            logger.info(f"   2. Update render.yaml with config from {config_path}")
            logger.info("   3. Deploy to trigger schema repair")
            logger.info("   4. Monitor logs for repair progress")

            return 0

        if args.execute:
            logger.info("🚀 Executing schema repair directly...")

            if execute_schema_repair():
                logger.info("✅ Schema repair completed successfully")
                return 0
            else:
                logger.error("❌ Schema repair failed")
                return 1

    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        return 3

if __name__ == "__main__":
    sys.exit(main())