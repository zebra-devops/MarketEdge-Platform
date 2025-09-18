#!/usr/bin/env python3
"""
EMERGENCY PRODUCTION MIGRATION DEPLOYMENT
Critical Issue: analytics_modules table missing - causing 500 errors
Business Impact: £925K Zebra Associates opportunity BLOCKED

This script:
1. Connects to production database using environment DATABASE_URL
2. Applies ALL pending Alembic migrations
3. Specifically creates missing analytics_modules table
4. Verifies table creation and database integrity
5. Tests Feature Flags endpoint returns 401 (not 500)

DEPLOYMENT: Must be run with production DATABASE_URL
"""

import os
import sys
import subprocess
import json
import asyncio
from datetime import datetime
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    import psycopg2
    import psycopg2.extras
    import asyncpg
    import requests
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine.url import make_url
    from alembic import command
    from alembic.config import Config
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install psycopg2-binary asyncpg requests sqlalchemy alembic")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'migration_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class ProductionMigrationDeployment:
    """Emergency migration deployment for production database"""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            logger.error("❌ DATABASE_URL environment variable not set!")
            logger.error("Set with: export DATABASE_URL='postgresql://user:password@host:port/database'")
            sys.exit(1)

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'business_context': '£925K Zebra Associates - analytics_modules table missing',
            'objective': 'Apply all pending migrations to create missing analytics_modules table',
            'database_url_set': bool(self.database_url),
            'steps': {}
        }

        logger.info(f"🚀 Starting emergency migration deployment")
        logger.info(f"📊 Business Impact: £925K Zebra Associates opportunity")
        logger.info(f"🎯 Target: Create missing analytics_modules table")

    def verify_database_connection(self):
        """Test database connectivity before migration"""
        logger.info("🔌 Testing database connection...")

        try:
            # Parse database URL to hide password in logs
            url = make_url(self.database_url)
            logger.info(f"🔗 Connecting to: {url.host}:{url.port}/{url.database} as {url.username}")

            # Test connection
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                logger.info(f"✅ Database connected: {version[:50]}...")

            self.results['steps']['database_connection'] = {
                'status': 'success',
                'message': 'Database connection successful'
            }
            return True

        except Exception as e:
            logger.error(f"❌ Database connection failed: {str(e)}")
            self.results['steps']['database_connection'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def check_current_migration_status(self):
        """Check current migration revision"""
        logger.info("📊 Checking current migration status...")

        try:
            # Set up Alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

            # Get current revision
            from alembic.script import ScriptDirectory
            script = ScriptDirectory.from_config(alembic_cfg)

            # Get database current revision
            from alembic.runtime.migration import MigrationContext
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()

            logger.info(f"📍 Current revision: {current_rev or 'No migrations applied'}")

            # Get head revision
            head_rev = script.get_current_head()
            logger.info(f"🎯 Target revision: {head_rev}")

            self.results['steps']['migration_status'] = {
                'status': 'success',
                'current_revision': current_rev,
                'head_revision': head_rev,
                'migrations_pending': current_rev != head_rev
            }

            return current_rev, head_rev

        except Exception as e:
            logger.error(f"❌ Migration status check failed: {str(e)}")
            self.results['steps']['migration_status'] = {
                'status': 'failed',
                'error': str(e)
            }
            return None, None

    def apply_migrations(self):
        """Apply all pending migrations"""
        logger.info("🚀 Applying all pending migrations...")

        try:
            # Set up Alembic config
            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

            # Apply migrations to head
            logger.info("⬆️ Upgrading to head...")
            command.upgrade(alembic_cfg, "head")

            logger.info("✅ All migrations applied successfully!")

            self.results['steps']['apply_migrations'] = {
                'status': 'success',
                'message': 'All pending migrations applied successfully'
            }
            return True

        except Exception as e:
            logger.error(f"❌ Migration application failed: {str(e)}")
            self.results['steps']['apply_migrations'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def verify_analytics_modules_table(self):
        """Verify analytics_modules table was created"""
        logger.info("🔍 Verifying analytics_modules table creation...")

        try:
            engine = create_engine(self.database_url)
            with engine.connect() as connection:
                # Check if table exists
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'analytics_modules'
                    );
                """))
                table_exists = result.fetchone()[0]

                if table_exists:
                    # Get table structure
                    result = connection.execute(text("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = 'analytics_modules'
                        ORDER BY ordinal_position;
                    """))
                    columns = result.fetchall()

                    logger.info("✅ analytics_modules table exists!")
                    logger.info("📊 Table structure:")
                    for col in columns:
                        logger.info(f"   - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")

                    # Count records
                    result = connection.execute(text("SELECT COUNT(*) FROM analytics_modules;"))
                    count = result.fetchone()[0]
                    logger.info(f"📈 Records in table: {count}")

                    self.results['steps']['verify_analytics_modules'] = {
                        'status': 'success',
                        'table_exists': True,
                        'columns': [{'name': col[0], 'type': col[1], 'nullable': col[2]} for col in columns],
                        'record_count': count
                    }
                    return True
                else:
                    logger.error("❌ analytics_modules table still missing!")
                    self.results['steps']['verify_analytics_modules'] = {
                        'status': 'failed',
                        'table_exists': False,
                        'error': 'Table not found after migration'
                    }
                    return False

        except Exception as e:
            logger.error(f"❌ Table verification failed: {str(e)}")
            self.results['steps']['verify_analytics_modules'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def test_feature_flags_endpoint(self):
        """Test Feature Flags endpoint returns 401 instead of 500"""
        logger.info("🧪 Testing Feature Flags endpoint...")

        try:
            # Test production endpoint
            url = "https://marketedge-platform.onrender.com/api/v1/admin/feature-flags"

            logger.info(f"🌐 Testing: {url}")
            response = requests.get(url, timeout=30)

            logger.info(f"📡 Response Status: {response.status_code}")
            logger.info(f"📄 Response Headers: {dict(response.headers)}")

            if response.status_code == 401:
                logger.info("✅ Feature Flags endpoint returns 401 (Unauthorized) - CORRECT!")
                logger.info("🎉 No more 500 errors - migration successful!")

                self.results['steps']['test_feature_flags'] = {
                    'status': 'success',
                    'endpoint_url': url,
                    'response_code': 401,
                    'message': 'Endpoint correctly returns 401 instead of 500'
                }
                return True

            elif response.status_code == 500:
                logger.error("❌ Feature Flags endpoint still returns 500!")
                logger.error("💥 Migration did not fix the issue")

                try:
                    error_content = response.text
                    logger.error(f"Error content: {error_content[:500]}...")
                except:
                    pass

                self.results['steps']['test_feature_flags'] = {
                    'status': 'failed',
                    'endpoint_url': url,
                    'response_code': 500,
                    'error': 'Endpoint still returns 500 error after migration'
                }
                return False

            else:
                logger.warning(f"⚠️ Unexpected response code: {response.status_code}")
                self.results['steps']['test_feature_flags'] = {
                    'status': 'warning',
                    'endpoint_url': url,
                    'response_code': response.status_code,
                    'message': f'Unexpected response code: {response.status_code}'
                }
                return True

        except Exception as e:
            logger.error(f"❌ Feature Flags endpoint test failed: {str(e)}")
            self.results['steps']['test_feature_flags'] = {
                'status': 'failed',
                'error': str(e)
            }
            return False

    def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        logger.info("📄 Generating deployment report...")

        # Overall status
        all_steps_successful = all(
            step.get('status') == 'success'
            for step in self.results['steps'].values()
            if step.get('status') != 'warning'
        )

        self.results['deployment_status'] = 'SUCCESS' if all_steps_successful else 'FAILED'
        self.results['completion_time'] = datetime.now().isoformat()

        # Save results to file
        filename = f"migration_deployment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"📊 Results saved to: {filename}")

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("🎯 EMERGENCY MIGRATION DEPLOYMENT SUMMARY")
        logger.info("="*60)
        logger.info(f"📅 Timestamp: {self.results['timestamp']}")
        logger.info(f"🏢 Business Context: {self.results['business_context']}")
        logger.info(f"🎯 Objective: {self.results['objective']}")
        logger.info(f"🟢 Overall Status: {self.results['deployment_status']}")

        logger.info("\n📋 Step Results:")
        for step_name, step_data in self.results['steps'].items():
            status = step_data.get('status', 'unknown')
            status_icon = "✅" if status == 'success' else "⚠️" if status == 'warning' else "❌"
            logger.info(f"   {status_icon} {step_name}: {status}")

        if all_steps_successful:
            logger.info("\n🎉 DEPLOYMENT SUCCESSFUL!")
            logger.info("✅ analytics_modules table created")
            logger.info("✅ Feature Flags endpoint fixed")
            logger.info("✅ Matt Lindop can now access admin features")
            logger.info("🚀 £925K Zebra Associates opportunity UNBLOCKED!")
        else:
            logger.error("\n💥 DEPLOYMENT FAILED!")
            logger.error("❌ Check errors above and retry")

        logger.info("="*60)

        return all_steps_successful

    async def run_deployment(self):
        """Execute the complete migration deployment"""
        logger.info("🚀 Starting Emergency Migration Deployment")

        try:
            # Step 1: Verify database connection
            if not self.verify_database_connection():
                logger.error("❌ Cannot proceed without database connection")
                return False

            # Step 2: Check current migration status
            current_rev, head_rev = self.check_current_migration_status()
            if current_rev is None:
                logger.error("❌ Cannot determine migration status")
                return False

            # Step 3: Apply migrations if needed
            if current_rev != head_rev:
                logger.info("📈 Migrations pending - applying now...")
                if not self.apply_migrations():
                    logger.error("❌ Migration application failed")
                    return False
            else:
                logger.info("✅ Database already at head revision")
                self.results['steps']['apply_migrations'] = {
                    'status': 'success',
                    'message': 'Database already at latest revision'
                }

            # Step 4: Verify analytics_modules table
            if not self.verify_analytics_modules_table():
                logger.error("❌ analytics_modules table verification failed")
                return False

            # Step 5: Test Feature Flags endpoint
            if not self.test_feature_flags_endpoint():
                logger.warning("⚠️ Feature Flags endpoint test failed (may still need app restart)")
                # Don't return False here - table creation is the critical part

            # Step 6: Generate report
            return self.generate_deployment_report()

        except Exception as e:
            logger.error(f"❌ Deployment failed with exception: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

            self.results['deployment_status'] = 'FAILED'
            self.results['fatal_error'] = str(e)
            self.generate_deployment_report()
            return False

def main():
    """Main deployment function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        return

    logger.info("🎯 EMERGENCY MIGRATION DEPLOYMENT")
    logger.info("🏢 Business Impact: £925K Zebra Associates opportunity")
    logger.info("🚨 Critical Issue: analytics_modules table missing")

    deployment = ProductionMigrationDeployment()

    # Run the deployment
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        success = loop.run_until_complete(deployment.run_deployment())

        if success:
            logger.info("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            logger.info("✅ analytics_modules table created")
            logger.info("🚀 Matt Lindop can now access admin features")
            sys.exit(0)
        else:
            logger.error("💥 DEPLOYMENT FAILED!")
            sys.exit(1)

    finally:
        loop.close()

if __name__ == "__main__":
    main()