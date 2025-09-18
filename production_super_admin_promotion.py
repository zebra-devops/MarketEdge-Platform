#!/usr/bin/env python
"""
Production Database Update Script - Matt Lindop Super Admin Promotion
Critical for £925K Zebra Associates Opportunity

This script connects to the production database and promotes Matt Lindop
to super_admin role to enable Feature Flags access.
"""

import os
import psycopg2
from psycopg2 import sql
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_production_db_url():
    """Get production database URL from environment or prompt"""
    db_url = os.getenv('PRODUCTION_DATABASE_URL')
    if not db_url:
        print("\n⚠️  PRODUCTION DATABASE CONNECTION REQUIRED")
        print("=" * 60)
        print("Please provide the production database URL from Render dashboard:")
        print("1. Go to https://dashboard.render.com")
        print("2. Select 'marketedge-platform' service")
        print("3. Go to Environment tab")
        print("4. Copy the DATABASE_URL value")
        print("=" * 60)
        db_url = input("\nPRODUCTION DATABASE_URL: ").strip()
    return db_url

def connect_to_production_db(db_url):
    """Establish connection to production database"""
    try:
        conn = psycopg2.connect(db_url)
        print("✅ Connected to production database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to production database: {e}")
        return None

def check_current_role(conn):
    """Check Matt Lindop's current role in production"""
    try:
        cur = conn.cursor()

        # Check both possible email addresses
        check_query = """
        SELECT id, email, role, full_name, organization_id, created_at
        FROM users
        WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com')
        ORDER BY created_at DESC;
        """

        cur.execute(check_query)
        results = cur.fetchall()

        print("\n📊 CURRENT PRODUCTION STATUS:")
        print("=" * 80)

        if not results:
            print("❌ No users found with Matt Lindop email addresses")
            return None

        for row in results:
            user_id, email, role, full_name, org_id, created = row
            print(f"\n  User ID: {user_id}")
            print(f"  Email: {email}")
            print(f"  Current Role: {role} {'⚠️ NEEDS UPDATE' if role != 'super_admin' else '✅'}")
            print(f"  Full Name: {full_name}")
            print(f"  Organization ID: {org_id}")
            print(f"  Created: {created}")

        print("=" * 80)
        return results

    except Exception as e:
        print(f"❌ Error checking current role: {e}")
        return None
    finally:
        cur.close()

def update_to_super_admin(conn):
    """Update Matt Lindop's role to super_admin in production"""
    try:
        cur = conn.cursor()

        # Update role for both possible email addresses
        update_query = """
        UPDATE users
        SET role = 'super_admin',
            updated_at = CURRENT_TIMESTAMP
        WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com')
        AND role != 'super_admin'
        RETURNING id, email, role;
        """

        print("\n🔄 EXECUTING PRODUCTION UPDATE:")
        print("=" * 80)
        print("Query:", update_query)

        cur.execute(update_query)
        updated_rows = cur.fetchall()

        if updated_rows:
            print(f"\n✅ Successfully updated {len(updated_rows)} user(s):")
            for row in updated_rows:
                user_id, email, new_role = row
                print(f"  - {email} -> role: {new_role}")

            # Commit the transaction
            conn.commit()
            print("\n✅ Changes committed to production database")
        else:
            print("\n✅ No updates needed - user(s) already have super_admin role")

        return True

    except Exception as e:
        print(f"\n❌ Error updating role: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()

def verify_update(conn):
    """Verify the role update was successful"""
    try:
        cur = conn.cursor()

        verify_query = """
        SELECT id, email, role, updated_at
        FROM users
        WHERE email IN ('matt.lindop@zebra.associates', 'matt.lindop@marketedge.com')
        ORDER BY updated_at DESC;
        """

        cur.execute(verify_query)
        results = cur.fetchall()

        print("\n✅ VERIFICATION - FINAL PRODUCTION STATE:")
        print("=" * 80)

        all_super_admin = True
        for row in results:
            user_id, email, role, updated = row
            status = "✅" if role == 'super_admin' else "❌"
            print(f"{status} {email}: role = {role} (updated: {updated})")
            if role != 'super_admin':
                all_super_admin = False

        print("=" * 80)

        if all_super_admin:
            print("\n🎉 SUCCESS! Matt Lindop now has super_admin access in production!")
            print("Feature Flags should now be accessible without 500 errors.")
        else:
            print("\n⚠️  WARNING: Some accounts still don't have super_admin role")

        return all_super_admin

    except Exception as e:
        print(f"❌ Error verifying update: {e}")
        return False
    finally:
        cur.close()

def save_results(results):
    """Save operation results to file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"production_super_admin_promotion_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Results saved to: {filename}")
    return filename

def main():
    """Main execution"""
    print("\n🚀 PRODUCTION SUPER ADMIN PROMOTION SCRIPT")
    print("=" * 80)
    print("Purpose: Update Matt Lindop to super_admin role in production")
    print("Impact: Unblocks £925K Zebra Associates opportunity")
    print("=" * 80)

    results = {
        'timestamp': datetime.now().isoformat(),
        'purpose': 'Promote Matt Lindop to super_admin in production',
        'business_impact': '£925K Zebra Associates opportunity',
        'steps': []
    }

    # Get production database URL
    db_url = get_production_db_url()
    if not db_url:
        print("❌ No database URL provided. Exiting.")
        return

    # Connect to production
    conn = connect_to_production_db(db_url)
    if not conn:
        print("❌ Failed to connect to production database. Exiting.")
        return

    try:
        # Step 1: Check current role
        print("\n📋 Step 1: Checking current production role...")
        current_state = check_current_role(conn)
        results['steps'].append({
            'step': 'check_current_role',
            'success': current_state is not None,
            'data': str(current_state)
        })

        if not current_state:
            print("❌ Could not verify current state. Aborting.")
            return

        # Check if update is needed
        needs_update = any(row[2] != 'super_admin' for row in current_state)

        if needs_update:
            # Step 2: Update to super_admin
            print("\n📋 Step 2: Updating role to super_admin...")
            update_success = update_to_super_admin(conn)
            results['steps'].append({
                'step': 'update_to_super_admin',
                'success': update_success
            })

            if not update_success:
                print("❌ Update failed. Please check database logs.")
                return
        else:
            print("\n✅ User(s) already have super_admin role. No update needed.")
            results['steps'].append({
                'step': 'update_to_super_admin',
                'success': True,
                'note': 'Already super_admin, no update needed'
            })

        # Step 3: Verify update
        print("\n📋 Step 3: Verifying production update...")
        verify_success = verify_update(conn)
        results['steps'].append({
            'step': 'verify_update',
            'success': verify_success
        })

        # Final status
        results['final_status'] = 'SUCCESS' if verify_success else 'FAILED'

        # Save results
        save_results(results)

        if verify_success:
            print("\n" + "=" * 80)
            print("🎉 PRODUCTION UPDATE COMPLETE!")
            print("=" * 80)
            print("\n✅ Matt Lindop now has super_admin access in production")
            print("✅ Feature Flags endpoint should now return data (not 500 error)")
            print("✅ £925K Zebra Associates opportunity is UNBLOCKED")
            print("\nNext steps:")
            print("1. Have Matt Lindop log out and log back in to refresh token")
            print("2. Test Feature Flags access at /admin/feature-flags")
            print("3. Confirm full admin dashboard functionality")

    finally:
        conn.close()
        print("\n🔒 Production database connection closed")

if __name__ == "__main__":
    main()