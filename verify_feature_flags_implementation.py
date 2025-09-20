#!/usr/bin/env python3
"""
Verify current implementation of /admin/feature-flags endpoint
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

async def verify_implementation():
    """Verify the current implementation matches expected patterns"""

    print("🔍 Verifying /admin/feature-flags implementation...")

    # Check the endpoint implementation
    try:
        from app.api.api_v1.endpoints.admin import list_feature_flags
        print("✅ list_feature_flags function imported successfully")

        # Check if it's async
        import inspect
        if inspect.iscoroutinefunction(list_feature_flags):
            print("✅ list_feature_flags is correctly defined as async")
        else:
            print("❌ list_feature_flags is NOT async")

        # Check AdminService.get_feature_flags method
        from app.services.admin_service import AdminService
        if hasattr(AdminService, 'get_feature_flags'):
            print("✅ AdminService.get_feature_flags method exists")

            # Check if it's async
            if inspect.iscoroutinefunction(AdminService.get_feature_flags):
                print("✅ AdminService.get_feature_flags is correctly async")
            else:
                print("❌ AdminService.get_feature_flags is NOT async")
        else:
            print("❌ AdminService.get_feature_flags method does NOT exist")

        # Check the current implementation pattern
        import ast
        import inspect

        source = inspect.getsource(list_feature_flags)
        print(f"\n📝 Current list_feature_flags implementation:")
        print("=" * 60)
        print(source)
        print("=" * 60)

        # Look for await patterns
        if "await admin_service.get_feature_flags(" in source:
            print("✅ Correctly awaiting admin_service.get_feature_flags()")
        else:
            print("❌ NOT awaiting admin_service.get_feature_flags() - THIS IS THE ISSUE!")

        # Check import statement
        if "from ....services.admin_service import AdminService" in source or "AdminService" in source:
            print("✅ AdminService is properly imported and used")
        else:
            print("❌ AdminService is NOT properly imported")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_implementation())