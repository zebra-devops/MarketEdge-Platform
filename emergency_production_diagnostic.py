#!/usr/bin/env python3
"""
EMERGENCY PRODUCTION DIAGNOSTIC
Critical backend outage affecting £925K Zebra Associates opportunity
"""

import asyncio
import logging
import time
import traceback
import sys
import os
from typing import Dict, Any

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test if database connection is working"""
    try:
        from app.core.database import get_async_db
        logger.info("Testing database connection...")

        async for db in get_async_db():
            # Simple query to test connection
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("✅ Database connection successful")
                return True
            else:
                logger.error("❌ Database query returned unexpected result")
                return False

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_module_registry():
    """Test module registry initialization"""
    try:
        logger.info("Testing module registry initialization...")
        from app.core.module_registry import initialize_module_registry
        from app.services.audit_service import AuditService
        from app.core.database import get_async_db

        async for db_session in get_async_db():
            audit_service = AuditService(db_session)
            await initialize_module_registry(
                audit_service=audit_service,
                max_registered_modules=10,  # Reduced for testing
                max_pending_registrations=5
            )
            logger.info("✅ Module registry initialization successful")
            return True

    except Exception as e:
        logger.error(f"❌ Module registry initialization failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_auth0_endpoint():
    """Test the specific Auth0 URL endpoint that's failing"""
    try:
        logger.info("Testing Auth0 endpoint functionality...")

        # Import required modules
        from app.api.api_v1.endpoints.auth import get_auth0_url
        from app.core.config import settings
        from fastapi import Request

        # Create a mock request
        class MockRequest:
            def __init__(self):
                self.url = type('MockURL', (), {'scheme': 'https', 'netloc': 'marketedge-platform.onrender.com'})()

        mock_request = MockRequest()

        # Test the function
        result = await get_auth0_url(mock_request)
        logger.info(f"✅ Auth0 URL endpoint working: {result}")
        return True

    except Exception as e:
        logger.error(f"❌ Auth0 endpoint test failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def test_analytics_modules_table():
    """Test if analytics_modules table exists and is accessible"""
    try:
        logger.info("Testing analytics_modules table...")
        from app.core.database import get_async_db
        from sqlalchemy import text

        async for db in get_async_db():
            # Check if table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables
                   WHERE table_name = 'analytics_modules'
                );
            """))
            table_exists = result.fetchone()[0]

            if table_exists:
                logger.info("✅ analytics_modules table exists")

                # Try to query it
                result = await db.execute(text("SELECT COUNT(*) FROM analytics_modules"))
                count = result.fetchone()[0]
                logger.info(f"✅ analytics_modules table has {count} records")
                return True
            else:
                logger.error("❌ analytics_modules table does not exist")
                return False

    except Exception as e:
        logger.error(f"❌ analytics_modules table test failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run comprehensive diagnostic"""
    logger.info("🚨 EMERGENCY PRODUCTION DIAGNOSTIC STARTED")
    logger.info("🎯 Diagnosing £925K Zebra Associates backend outage")

    results = {
        "database_connection": False,
        "analytics_modules_table": False,
        "module_registry": False,
        "auth0_endpoint": False
    }

    # Test database connection first
    results["database_connection"] = await test_database_connection()

    if results["database_connection"]:
        # Only test table if database is connected
        results["analytics_modules_table"] = await test_analytics_modules_table()

        # Test module registry if database is working
        results["module_registry"] = await test_module_registry()

    # Test Auth0 endpoint functionality
    results["auth0_endpoint"] = await test_auth0_endpoint()

    # Summary
    logger.info("\n" + "="*50)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("="*50)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    if all(results.values()):
        logger.info("🎉 All tests passed - Issue may be deployment-specific")
    else:
        failed_tests = [test for test, result in results.items() if not result]
        logger.error(f"🚨 CRITICAL FAILURES: {', '.join(failed_tests)}")

        # Specific recommendations
        if not results["database_connection"]:
            logger.error("🔴 CRITICAL: Database connection failed - Check DATABASE_URL and migrations")
        if not results["analytics_modules_table"]:
            logger.error("🔴 CRITICAL: analytics_modules table missing - Run migrations")
        if not results["module_registry"]:
            logger.error("🔴 CRITICAL: Module registry failing - Check database and dependencies")
        if not results["auth0_endpoint"]:
            logger.error("🔴 CRITICAL: Auth0 endpoint failing - Check Auth0 configuration")

    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())

        # Exit with error code if any tests failed
        if not all(results.values()):
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        logger.error(f"🚨 DIAGNOSTIC SCRIPT FAILED: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)