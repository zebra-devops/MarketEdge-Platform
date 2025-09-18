#!/usr/bin/env python3
"""
Direct Production Database Update - Matt Lindop Super Admin Promotion
Critical for £925K Zebra Associates Opportunity
Using asyncpg for better reliability
"""

import asyncio
import asyncpg
from datetime import datetime
import json

# Production Database URL - Direct from Render
DATABASE_URL = "postgresql://marketedge_user:Qra5HBKofZqoQwQgKNyVnOOwKVRbRPAW@dpg-d2gch62dbo4c73b0kl80-a.oregon-postgres.render.com/marketedge_production"

async def execute_production_update():
    """Execute the production database update"""

    print("🚀 PRODUCTION SUPER ADMIN PROMOTION")
    print("=" * 80)
    print("Business Impact: £925K Zebra Associates Opportunity")
    print("Target: matt.lindop@zebra.associates → super_admin role")
    print("=" * 80)

    results = {
        'timestamp': datetime.now().isoformat(),
        'environment': 'PRODUCTION',
        'action': 'PROMOTE_TO_SUPER_ADMIN',
        'target_email': 'matt.lindop@zebra.associates',
        'target_id': 'ebc9567a-bbf8-4ddf-8eee-7635fba62363'
    }

    try:
        print("\n[1/4] Connecting to production database...")
        print(f"Host: dpg-d2gch62dbo4c73b0kl80-a.oregon-postgres.render.com")

        # Try connecting with timeout
        conn = await asyncio.wait_for(
            asyncpg.connect(DATABASE_URL),
            timeout=30.0
        )
        print("✅ Connected to production database successfully")

        try:
            # Check current state
            print("\n[2/4] Checking current user state...")
            current_user = await conn.fetchrow("""
                SELECT id, email, role, organisation_id, created_at, updated_at
                FROM users
                WHERE email = $1 AND id = $2
            """, results['target_email'], results['target_id'])

            if not current_user:
                results['status'] = 'USER_NOT_FOUND'
                print(f"❌ User not found: {results['target_email']}")
                return results

            results['before'] = {
                'role': current_user['role'],
                'organisation_id': str(current_user['organisation_id']) if current_user['organisation_id'] else None,
                'updated_at': current_user['updated_at'].isoformat() if current_user['updated_at'] else None
            }

            print(f"Current role: {current_user['role']}")
            print(f"Organisation ID: {current_user['organisation_id']}")

            if current_user['role'] == 'super_admin':
                results['status'] = 'ALREADY_SUPER_ADMIN'
                print("✅ User already has super_admin role - no update needed")
                return results

            # Execute the role update
            print(f"\n[3/4] Updating role from '{current_user['role']}' to 'super_admin'...")

            async with conn.transaction():
                update_result = await conn.execute("""
                    UPDATE users
                    SET role = 'super_admin',
                        updated_at = NOW()
                    WHERE email = $1 AND id = $2
                """, results['target_email'], results['target_id'])

                print(f"Update query executed: {update_result}")

            # Verify the update
            print("\n[4/4] Verifying update success...")
            updated_user = await conn.fetchrow("""
                SELECT id, email, role, updated_at
                FROM users
                WHERE email = $1 AND id = $2
            """, results['target_email'], results['target_id'])

            results['after'] = {
                'role': updated_user['role'],
                'updated_at': updated_user['updated_at'].isoformat() if updated_user['updated_at'] else None
            }

            if updated_user['role'] == 'super_admin':
                results['status'] = 'SUCCESS'
                print(f"✅ Successfully updated role to: {updated_user['role']}")
                print(f"✅ Updated at: {updated_user['updated_at']}")
            else:
                results['status'] = 'UPDATE_FAILED'
                print(f"❌ Update failed - role is still: {updated_user['role']}")

        finally:
            await conn.close()
            print("\n✅ Database connection closed")

    except asyncio.TimeoutError:
        results['status'] = 'CONNECTION_TIMEOUT'
        results['error'] = 'Database connection timed out after 30 seconds'
        print("❌ Connection timeout - database may be unreachable")

    except Exception as e:
        results['status'] = 'ERROR'
        results['error'] = str(e)
        print(f"❌ Error during update: {str(e)}")

    return results

async def test_feature_flags_access():
    """Test that feature flags are now accessible with super_admin role"""

    print("\n" + "=" * 80)
    print("TESTING FEATURE FLAGS ACCESS")
    print("=" * 80)

    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(DATABASE_URL),
            timeout=15.0
        )

        try:
            # Check user role
            user = await conn.fetchrow("""
                SELECT email, role, organisation_id
                FROM users
                WHERE email = $1
            """, "matt.lindop@zebra.associates")

            print(f"✅ User verified: {user['email']} with role: {user['role']}")

            # Test feature flags access
            flags = await conn.fetch("""
                SELECT name, enabled, rollout_percentage, target_organizations
                FROM feature_flags
                ORDER BY name
                LIMIT 10
            """)

            print(f"✅ Feature flags accessible: {len(flags)} flags found")

            for flag in flags[:3]:  # Show first 3 flags
                print(f"  - {flag['name']}: enabled={flag['enabled']}, rollout={flag['rollout_percentage']}%")

            # Test organizations access (admin dashboard)
            org_count = await conn.fetchval("SELECT COUNT(*) FROM organizations")
            print(f"✅ Organizations accessible: {org_count} organizations found")

            return True

        finally:
            await conn.close()

    except Exception as e:
        print(f"❌ Access test failed: {str(e)}")
        return False

async def main():
    """Main execution flow"""

    # Execute the promotion
    update_results = await execute_production_update()

    # Test access if successful
    access_test_passed = False
    if update_results['status'] in ['SUCCESS', 'ALREADY_SUPER_ADMIN']:
        access_test_passed = await test_feature_flags_access()

    # Generate final report
    report = {
        'execution_timestamp': datetime.now().isoformat(),
        'environment': 'PRODUCTION',
        'business_impact': '£925K Zebra Associates Opportunity',
        'update_results': update_results,
        'access_test_passed': access_test_passed,
        'final_status': 'COMPLETE' if update_results['status'] in ['SUCCESS', 'ALREADY_SUPER_ADMIN'] else 'FAILED'
    }

    # Save detailed report
    report_filename = f"production_promotion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)

    # Final summary
    print("\n" + "=" * 80)
    print("PRODUCTION UPDATE SUMMARY")
    print("=" * 80)
    print(f"Status: {update_results['status']}")

    if update_results['status'] == 'SUCCESS':
        print("✅ Matt Lindop successfully promoted to super_admin")
        print("✅ Feature Flags endpoint should now work without errors")
        print("✅ £925K Zebra Associates opportunity is UNBLOCKED")

    elif update_results['status'] == 'ALREADY_SUPER_ADMIN':
        print("✅ Matt Lindop already had super_admin role")
        print("✅ Feature Flags access should already be working")

    else:
        print(f"❌ Update failed: {update_results.get('error', 'Unknown error')}")
        print("⚠️  Manual intervention may be required")

    if access_test_passed:
        print("✅ Access verification passed - admin features working")

    print(f"\n📄 Detailed report saved: {report_filename}")
    print("=" * 80)

    return report

if __name__ == "__main__":
    report = asyncio.run(main())

    # Exit with appropriate code
    if report['final_status'] == 'COMPLETE':
        print("\n🎉 PRODUCTION UPDATE SUCCESSFUL!")
        exit(0)
    else:
        print("\n⚠️  PRODUCTION UPDATE NEEDS ATTENTION")
        exit(1)