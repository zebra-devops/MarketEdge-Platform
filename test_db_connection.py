#!/usr/bin/env python3
"""
Database Connection Test Script
==============================

Simple script to test database connectivity before running the migration.
This helps verify that you have the correct DATABASE_URL and network access.

Usage:
    python test_db_connection.py
"""

import os
import sys
from sqlalchemy import create_engine, text

def test_database_connection():
    """Test the database connection and show basic information"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        database_url = os.getenv('POSTGRES_URL') or os.getenv('POSTGRESQL_URL')
    
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not found")
        print("   Set it with: export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    # Hide password in display
    display_url = database_url
    if '@' in display_url and ':' in display_url.split('@')[0]:
        parts = display_url.split('@')
        user_part = parts[0].split(':')[0] + ':****'
        display_url = user_part + '@' + parts[1]
    
    print(f"Testing connection to: {display_url}")
    
    try:
        # Create engine and test connection
        engine = create_engine(database_url, echo=False)
        
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT version()"))
            version_info = result.fetchone()[0]
            print(f"✅ Database connection successful!")
            print(f"   PostgreSQL version: {version_info.split(',')[0]}")
            
            # Check if required tables exist
            tables_to_check = ['users', 'organisations', 'organization_hierarchy', 'user_hierarchy_assignments']
            
            print(f"\nChecking required tables:")
            for table in tables_to_check:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.fetchone()[0]
                status = "✅" if exists else "❌"
                print(f"   {status} {table}")
            
            # Count existing users and organizations
            try:
                user_count = conn.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
                org_count = conn.execute(text("SELECT COUNT(*) FROM organisations")).fetchone()[0]
                print(f"\nCurrent data:")
                print(f"   Users: {user_count}")
                print(f"   Organizations: {org_count}")
                
                # Check if Matt Lindop already exists
                matt_exists = conn.execute(text(
                    "SELECT COUNT(*) FROM users WHERE email = 'matt.lindop@zebra.associates'"
                )).fetchone()[0]
                
                zebra_exists = conn.execute(text(
                    "SELECT COUNT(*) FROM organisations WHERE name = 'Zebra Associates'"
                )).fetchone()[0]
                
                print(f"   Matt Lindop exists: {'Yes' if matt_exists > 0 else 'No'}")
                print(f"   Zebra Associates exists: {'Yes' if zebra_exists > 0 else 'No'}")
                
            except Exception as e:
                print(f"   ⚠️  Could not query existing data: {e}")
            
            print(f"\n🎉 Database is ready for migration!")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"\nTroubleshooting:")
        print(f"   1. Check if DATABASE_URL is correct")
        print(f"   2. Verify network connectivity to database host")
        print(f"   3. Ensure database user has required permissions")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE CONNECTION TEST")
    print("=" * 50)
    
    success = test_database_connection()
    
    print("=" * 50)
    if success:
        print("✅ READY TO RUN MIGRATION")
        print("Run: python add_super_admin_migration.py")
    else:
        print("❌ FIX CONNECTION ISSUES FIRST")
    print("=" * 50)
    
    sys.exit(0 if success else 1)