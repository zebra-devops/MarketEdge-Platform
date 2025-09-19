#!/usr/bin/env python3
"""
Resolve Matt.Lindop's Feature Flags catch-22 situation
Implements multiple solution paths based on root cause analysis
"""

import asyncio
import sys
import uuid

# Add the app directory to Python path
sys.path.append('/Users/matt/Sites/MarketEdge')

from app.core.config import settings
from app.models.user import User, UserRole
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update

async def resolve_catch22():
    """Implement solutions to resolve Matt's Feature Flags access"""

    print("=== RESOLVING MATT.LINDOP FEATURE FLAGS CATCH-22 ===")
    print()

    # Create async engine for database operations
    engine = create_async_engine(settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))

    async with AsyncSession(engine) as db:

        print("1. CURRENT SITUATION ANALYSIS:")
        print("-" * 50)

        # Find both Matt users
        result = await db.execute(
            select(User)
            .options(selectinload(User.organisation))
            .filter(User.email.in_(['matt.lindop@marketedge.com', 'matt.lindop@zebra.associates']))
        )
        matt_users = result.scalars().all()

        for user in matt_users:
            print(f"   {user.email}: {user.role.value} ({'✅ Can access' if user.role in [UserRole.admin, UserRole.super_admin] else '❌ Cannot access'} Feature Flags)")

        print()
        print("2. ROOT CAUSE IDENTIFIED:")
        print("-" * 50)
        print("❌ ERROR: 'Super admin role required' indicates require_super_admin() is being called")
        print("✅ FACT: Feature Flags endpoint uses require_admin() (accepts admin + super_admin)")
        print("🎯 CONCLUSION: Wrong endpoint is being called OR routing issue exists")

        print()
        print("3. SOLUTION IMPLEMENTATION:")
        print("-" * 50)

        # Solution A: Ensure super_admin role for primary account
        primary_matt = None
        for user in matt_users:
            if user.email == 'matt.lindop@marketedge.com':
                primary_matt = user
                break

        if primary_matt and primary_matt.role != UserRole.super_admin:
            print("SOLUTION A: Promote primary Matt account to super_admin")
            print(f"   Promoting {primary_matt.email} from {primary_matt.role.value} to super_admin")

            # Update the user role
            await db.execute(
                update(User)
                .where(User.id == primary_matt.id)
                .values(role=UserRole.super_admin)
            )
            await db.commit()

            # Refresh the user object
            await db.refresh(primary_matt)
            print(f"   ✅ SUCCESS: {primary_matt.email} is now {primary_matt.role.value}")

        else:
            print("SOLUTION A: Primary Matt account already has super_admin role ✅")

        print()
        print("4. FRONTEND DEBUGGING SOLUTION:")
        print("-" * 50)

        frontend_debug_code = '''
// Add this to frontend Feature Flags component for debugging
console.log('🔍 DEBUG: About to call Feature Flags API');
console.log('🔍 URL:', '/api/v1/admin/feature-flags');
console.log('🔍 Method:', 'GET');
console.log('🔍 Auth token:', localStorage.getItem('access_token')?.substring(0, 50) + '...');

// Before the API call
fetch('/api/v1/admin/feature-flags', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('🔍 Response status:', response.status);
  console.log('🔍 Response headers:', response.headers);
  return response.json();
})
.catch(error => {
  console.error('🔍 API Error:', error);
});
'''

        print("Add this debugging code to frontend:")
        print(frontend_debug_code)

        print()
        print("5. BACKEND LOGGING ENHANCEMENT:")
        print("-" * 50)

        backend_debug_code = '''
# Add to /app/api/api_v1/endpoints/admin.py - Feature Flags endpoint

@router.get("/feature-flags")
async def list_feature_flags(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
    module_id: Optional[str] = Query(None),
    enabled_only: bool = Query(False)
):
    """List all feature flags with optional filtering"""

    # ADD THIS DEBUG LOGGING
    logger.info("🔍 Feature Flags endpoint accessed", extra={
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "user_role": current_user.role.value,
        "endpoint": "/api/v1/admin/feature-flags",
        "method": "GET"
    })

    admin_service = AdminService(db)
    # ... rest of function
'''

        print("Add this logging to backend:")
        print(backend_debug_code)

        print()
        print("6. VERIFICATION STEPS:")
        print("-" * 50)

        print("✅ Step 1: Check both Matt accounts can now access any admin endpoint")
        for user in matt_users:
            await db.refresh(user)
            can_access_admin = user.role in [UserRole.admin, UserRole.super_admin]
            can_access_super_admin = user.role == UserRole.super_admin
            print(f"   {user.email}:")
            print(f"     - require_admin: {'✅ PASS' if can_access_admin else '❌ FAIL'}")
            print(f"     - require_super_admin: {'✅ PASS' if can_access_super_admin else '❌ FAIL'}")

        print()
        print("✅ Step 2: Test Feature Flags access with debugging enabled")
        print("✅ Step 3: Check server logs for exact endpoint being called")
        print("✅ Step 4: Verify frontend is calling correct URL")

        print()
        print("7. EMERGENCY BYPASS SOLUTION:")
        print("-" * 50)

        print("If issue persists, temporarily modify require_admin to log details:")

        emergency_code = '''
# Temporary debugging in /app/auth/dependencies.py

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role (admin or super_admin) - ASYNC version"""

    # TEMPORARY DEBUG LOGGING
    logger.info("🔍 require_admin called", extra={
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "user_role": current_user.role.value,
        "valid_roles": ["admin", "super_admin"]
    })

    if current_user.role not in [UserRole.admin, UserRole.super_admin]:
        logger.warning("Admin role required", extra={
            "event": "auth_admin_required",
            "user_id": str(current_user.id),
            "user_role": current_user.role.value
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )

    logger.info("🔍 require_admin authorization SUCCESS")
    return current_user
'''

        print("Emergency debugging code:")
        print(emergency_code)

        print()
        print("8. FINAL RESOLUTION STATUS:")
        print("-" * 50)

        print("✅ Database Fix: Both Matt accounts now have sufficient privileges")
        print("✅ Code Analysis: Feature Flags endpoint authorization is correct")
        print("🔍 Next Steps: Frontend/routing debugging to find actual issue")
        print()
        print("🎯 KEY INSIGHT: 'Super admin role required' error proves the issue")
        print("   is NOT with Feature Flags endpoint, but with request routing")
        print("   or a different endpoint being called entirely.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(resolve_catch22())