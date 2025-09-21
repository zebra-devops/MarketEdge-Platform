#!/usr/bin/env python3
"""
MarketEdge Platform - Staging Database Setup
Configures and seeds staging databases for Preview Environments
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.database import get_async_db, async_engine
from app.models import *  # Import all models
from database.seeds.initial_data import create_initial_data
from database.seeds.phase3_data import create_phase3_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StagingDatabaseSetup:
    """Handles staging database setup and seeding"""

    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.is_staging = self.environment == 'staging'

    async def setup_staging_database(self):
        """Complete staging database setup process"""
        if not self.is_staging:
            logger.info(f"Environment is {self.environment}, skipping staging setup")
            return

        logger.info("🚀 Starting staging database setup...")

        try:
            # Verify database connection
            await self.verify_connection()

            # Setup extensions
            await self.setup_extensions()

            # Seed with initial data
            await self.seed_initial_data()

            # Seed with test data for staging
            await self.seed_staging_test_data()

            # Create test organizations
            await self.create_test_organizations()

            # Verify setup
            await self.verify_setup()

            logger.info("✅ Staging database setup complete!")

        except Exception as e:
            logger.error(f"❌ Staging database setup failed: {e}")
            raise

    async def verify_connection(self):
        """Verify database connection is working"""
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✅ Database connected: {version}")

    async def setup_extensions(self):
        """Setup required PostgreSQL extensions"""
        async with async_engine.begin() as conn:
            # UUID extension for ID generation
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            logger.info("✅ UUID extension enabled")

            # Trigram extension for text search
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pg_trgm"'))
            logger.info("✅ Trigram extension enabled")

    async def seed_initial_data(self):
        """Seed database with initial required data"""
        logger.info("📦 Seeding initial data...")

        async for db in get_async_db():
            try:
                await create_initial_data(db)
                logger.info("✅ Initial data seeded")
                break
            except Exception as e:
                logger.error(f"❌ Initial data seeding failed: {e}")
                raise

    async def seed_staging_test_data(self):
        """Seed database with staging-specific test data"""
        logger.info("🧪 Seeding staging test data...")

        async for db in get_async_db():
            try:
                await create_phase3_data(db)
                logger.info("✅ Phase 3 test data seeded")
                break
            except Exception as e:
                logger.error(f"❌ Test data seeding failed: {e}")
                raise

    async def create_test_organizations(self):
        """Create test organizations for staging environment"""
        from app.models.organization import Organization
        from app.models.user_role import UserRole

        test_orgs = [
            {
                "name": "Zebra Associates (Staging)",
                "domain": "zebra.associates",
                "industry": "B2B",
                "sic_code": "70221",  # Management consultancy
                "is_active": True
            },
            {
                "name": "ODEON Cinemas (Staging)",
                "domain": "odeon.co.uk",
                "industry": "Cinema",
                "sic_code": "59140",  # Motion picture projection
                "is_active": True
            },
            {
                "name": "Test Hotel Group",
                "domain": "testhotel.staging",
                "industry": "Hotel",
                "sic_code": "55100",  # Hotels and similar accommodation
                "is_active": True
            }
        ]

        async for db in get_async_db():
            try:
                for org_data in test_orgs:
                    # Check if organization already exists
                    existing = await db.execute(
                        text("SELECT id FROM organizations WHERE domain = :domain"),
                        {"domain": org_data["domain"]}
                    )

                    if existing.fetchone():
                        logger.info(f"✅ Organization {org_data['name']} already exists")
                        continue

                    # Create organization
                    await db.execute(
                        text("""
                        INSERT INTO organizations (name, domain, industry, sic_code, is_active)
                        VALUES (:name, :domain, :industry, :sic_code, :is_active)
                        """),
                        org_data
                    )
                    logger.info(f"✅ Created test organization: {org_data['name']}")

                await db.commit()
                break

            except Exception as e:
                logger.error(f"❌ Test organization creation failed: {e}")
                await db.rollback()
                raise

    async def verify_setup(self):
        """Verify staging database setup is complete"""
        async with async_engine.begin() as conn:
            # Check tables exist
            tables_check = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))

            tables = [row[0] for row in tables_check.fetchall()]
            expected_tables = [
                'organizations', 'users', 'feature_flags',
                'analytics_modules', 'user_roles', 'alembic_version'
            ]

            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                raise Exception(f"Missing tables: {missing_tables}")

            logger.info(f"✅ Database tables verified: {len(tables)} tables found")

            # Check data exists
            org_count = await conn.execute(text("SELECT COUNT(*) FROM organizations"))
            org_total = org_count.scalar()

            user_count = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_total = user_count.scalar()

            logger.info(f"✅ Data verification: {org_total} organizations, {user_total} users")

    def get_staging_info(self) -> Dict[str, Any]:
        """Get staging environment information"""
        return {
            "environment": self.environment,
            "database_url": os.getenv('DATABASE_URL', 'Not set'),
            "redis_url": os.getenv('REDIS_URL', 'Not set'),
            "auth0_domain": os.getenv('AUTH0_DOMAIN_STAGING', 'Not set'),
            "cors_origins": os.getenv('ALLOWED_ORIGINS', '*'),
            "debug_logging": os.getenv('ENABLE_DEBUG_LOGGING', 'false')
        }

async def main():
    """Main staging setup function"""
    setup = StagingDatabaseSetup()

    logger.info("🎯 MarketEdge Staging Database Setup")
    logger.info("=" * 50)

    # Print environment info
    info = setup.get_staging_info()
    for key, value in info.items():
        logger.info(f"{key}: {value}")

    logger.info("=" * 50)

    # Run setup
    await setup.setup_staging_database()

if __name__ == "__main__":
    asyncio.run(main())