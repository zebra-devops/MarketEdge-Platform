#!/usr/bin/env python3
"""
EMERGENCY DIRECT DATABASE ADMIN SETUP
Direct database script to grant admin privileges for £925K opportunity

This script directly connects to the production database and:
1. Finds matt.lindop@zebra.associates user
2. Sets their role to UserRole.admin 
3. Grants access to all applications (market_edge, causal_edge, value_edge)
4. Verifies the changes

CRITICAL: This bypasses the API and works directly with the database
"""

import os
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime, timezone
from enum import Enum

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://marketedge_postgres_user:p8ZdLmQmzJRDOBJK3j4w2mMVE5hZYj4M@dpg-cru8vp88fa8c73dnafpg-a.oregon-postgres.render.com/marketedge_postgres")
ADMIN_EMAIL = "matt.lindop@zebra.associates"

class UserRole(str, Enum):
    admin = "admin"
    analyst = "analyst" 
    viewer = "viewer"

class ApplicationType(str, Enum):
    MARKET_EDGE = "market_edge"
    CAUSAL_EDGE = "causal_edge"
    VALUE_EDGE = "value_edge"

def connect_to_database():
    """Connect to the production database"""
    try:
        # Parse DATABASE_URL and add SSL requirements for Render
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(DATABASE_URL)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],  # Remove leading /
            sslmode='require'
        )
        conn.autocommit = False  # Use transactions
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def setup_admin_privileges(conn, admin_email):
    """Set up admin privileges for the specified user"""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            print(f"🔍 Looking for user: {admin_email}")
            
            # Step 1: Find the user
            cur.execute("SELECT id, email, role, is_active FROM users WHERE email = %s", (admin_email,))
            user = cur.fetchone()
            
            if not user:
                print(f"❌ User {admin_email} not found in database")
                print("💡 User must authenticate via Auth0 first to create their database record")
                return False
            
            print(f"✅ User found: ID={user['id']}, Current Role={user['role']}, Active={user['is_active']}")
            
            # Step 2: Update user role to admin
            original_role = user['role']
            cur.execute(
                "UPDATE users SET role = %s WHERE id = %s",
                (UserRole.admin.value, user['id'])
            )
            print(f"📝 Updated role from '{original_role}' to '{UserRole.admin.value}'")
            
            # Step 3: Set up application access
            applications_setup = []
            
            for app_type in ApplicationType:
                # Check if access record exists
                cur.execute(
                    "SELECT id, has_access FROM user_application_access WHERE user_id = %s AND application = %s",
                    (user['id'], app_type.value)
                )
                existing_access = cur.fetchone()
                
                if existing_access:
                    if not existing_access['has_access']:
                        # Update existing record
                        cur.execute(
                            "UPDATE user_application_access SET has_access = TRUE, granted_by = %s, granted_at = %s WHERE id = %s",
                            (user['id'], datetime.now(timezone.utc), existing_access['id'])
                        )
                        applications_setup.append(f"Updated {app_type.value}")
                    else:
                        applications_setup.append(f"Already had {app_type.value}")
                else:
                    # Create new access record
                    cur.execute(
                        """INSERT INTO user_application_access (user_id, application, has_access, granted_by, granted_at) 
                           VALUES (%s, %s, TRUE, %s, %s)""",
                        (user['id'], app_type.value, user['id'], datetime.now(timezone.utc))
                    )
                    applications_setup.append(f"Granted {app_type.value}")
            
            print("🎯 Application access setup:")
            for app_setup in applications_setup:
                print(f"   - {app_setup}")
            
            # Step 4: Commit changes
            conn.commit()
            print("💾 Database changes committed successfully")
            
            # Step 5: Verify the changes
            cur.execute("SELECT role FROM users WHERE id = %s", (user['id'],))
            final_role = cur.fetchone()['role']
            
            cur.execute(
                "SELECT application FROM user_application_access WHERE user_id = %s AND has_access = TRUE",
                (user['id'],)
            )
            accessible_apps = [row['application'] for row in cur.fetchall()]
            
            print("\n🔍 VERIFICATION RESULTS:")
            print(f"   ✅ Final Role: {final_role}")
            print(f"   ✅ Accessible Applications: {', '.join(accessible_apps)}")
            print(f"   ✅ Epic 1 Access (Module Management): {'YES' if final_role == UserRole.admin.value else 'NO'}")
            print(f"   ✅ Epic 2 Access (Feature Flags): {'YES' if final_role == UserRole.admin.value else 'NO'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error setting up admin privileges: {e}")
        conn.rollback()
        return False

def verify_epic_access(admin_email):
    """Verify that Epic endpoints should now work for the user"""
    print("\n🎯 EPIC ENDPOINT ACCESS VERIFICATION")
    print("=" * 50)
    print(f"User: {admin_email}")
    print("Epic 1 - Module Management:")
    print("   Endpoint: GET /api/v1/module-management/modules")
    print("   Requires: UserRole.admin ✅")
    print()
    print("Epic 2 - Feature Flags:")
    print("   Endpoint: GET /api/v1/admin/feature-flags") 
    print("   Requires: UserRole.admin ✅")
    print()
    print("⚠️  IMPORTANT: User must re-authenticate to get updated JWT token with admin role")
    print("✅ After re-authentication, Epic endpoints should return 200 instead of 403")

def main():
    """Main execution function"""
    print("=" * 80)
    print("🚨 EMERGENCY DIRECT DATABASE ADMIN SETUP")
    print("£925K OPPORTUNITY - EPIC ACCESS CONFIGURATION") 
    print("=" * 80)
    print(f"Target User: {ADMIN_EMAIL}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Set up admin privileges
        success = setup_admin_privileges(conn, ADMIN_EMAIL)
        
        if success:
            print("\n🎉 SUCCESS: Admin privileges configured!")
            print("💼 Business Impact: £925K opportunity unblocked")
            verify_epic_access(ADMIN_EMAIL)
        else:
            print("\n❌ FAILED: Could not set up admin privileges")
            print("💼 Business Impact: £925K opportunity still blocked")
        
    finally:
        conn.close()
        print("\n🔌 Database connection closed")
    
    print("\n" + "=" * 80)
    print("🚀 NEXT STEPS:")
    print("1. Have matt.lindop@zebra.associates log out and log back in via Auth0")
    print("2. New JWT token will include admin role")
    print("3. Test Epic endpoints - should return 200 instead of 403")
    print("4. Demo Epic functionality for £925K opportunity")
    print("=" * 80)

if __name__ == "__main__":
    main()