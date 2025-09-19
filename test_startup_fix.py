#!/usr/bin/env python3
"""
Test the startup fix to ensure no more hanging
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_startup_module_registry():
    """Test the fixed module registry initialization"""
    try:
        logger.info("Testing fixed module registry startup...")

        from app.core.module_registry import initialize_module_registry
        from app.services.audit_service import AuditService
        from app.core.database import get_async_db

        logger.info("✅ Imports successful")

        # Test the async database session pattern
        async for db_session in get_async_db():
            logger.info("✅ Async database session created")

            audit_service = AuditService(db_session)
            logger.info("✅ Audit service created")

            await initialize_module_registry(
                audit_service=audit_service,
                max_registered_modules=5,  # Small number for testing
                max_pending_registrations=2
            )
            logger.info("✅ Module registry initialized successfully")
            break

        logger.info("🎉 Startup fix works - no hanging!")
        return True

    except Exception as e:
        logger.error(f"❌ Startup test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

async def main():
    """Test the startup fix"""
    logger.info("🧪 Testing startup fix for production deployment")

    success = await test_startup_module_registry()

    if success:
        logger.info("✅ STARTUP FIX VERIFIED - Ready for deployment")
        return True
    else:
        logger.error("❌ STARTUP FIX FAILED - Do not deploy")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        sys.exit(1)