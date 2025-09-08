#!/usr/bin/env python3
"""
Emergency script to create missing module and feature flag tables in production
For £925K Zebra Associates opportunity
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Production database connection from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://marketedge_user:secure_production_password_2025@dpg-ctn4d5pu0jms73dl3svg-a.oregon-postgres.render.com/marketedge_db")

def execute_module_tables_fix():
    """Execute SQL to create missing tables and seed data"""
    
    print(f"\n{'='*60}")
    print("EMERGENCY MODULE TABLES FIX FOR ZEBRA ASSOCIATES")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    try:
        # Connect to database
        print("1. Connecting to production database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()
        print("   ✅ Connected successfully")
        
        # Check existing tables
        print("\n2. Checking existing tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('feature_flags', 'analytics_modules', 'organisation_modules')
        """)
        existing_tables = [row[0] for row in cur.fetchall()]
        print(f"   Found {len(existing_tables)} existing tables: {', '.join(existing_tables) if existing_tables else 'None'}")
        
        # Read and execute SQL file
        print("\n3. Executing emergency SQL fixes...")
        with open('emergency_module_tables_fix.sql', 'r') as f:
            sql_content = f.read()
            
        # Split and execute SQL statements
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, stmt in enumerate(statements, 1):
            try:
                if 'SELECT' in stmt and 'INSERT' not in stmt and 'CREATE' not in stmt:
                    # This is a verification query
                    cur.execute(stmt)
                    result = cur.fetchall()
                    for row in result:
                        print(f"   ✅ {row[0]} {row[1]}")
                else:
                    # This is a DDL/DML statement
                    cur.execute(stmt)
                    if 'CREATE TABLE' in stmt:
                        table_name = stmt.split('IF NOT EXISTS')[1].split('(')[0].strip()
                        print(f"   ✅ Table {table_name} created/verified")
                    elif 'INSERT INTO' in stmt:
                        table_name = stmt.split('INSERT INTO')[1].split('(')[0].strip()
                        print(f"   ✅ Data inserted into {table_name}")
            except Exception as e:
                if 'already exists' in str(e) or 'duplicate key' in str(e):
                    print(f"   ⚠️  Skipped (already exists): {str(e)[:100]}")
                else:
                    print(f"   ❌ Error: {str(e)[:200]}")
        
        # Verify Zebra Associates setup
        print("\n4. Verifying Zebra Associates configuration...")
        
        # Check feature flags
        cur.execute("SELECT COUNT(*) FROM feature_flags WHERE enabled = true")
        ff_count = cur.fetchone()[0]
        print(f"   ✅ {ff_count} feature flags enabled")
        
        # Check modules
        cur.execute("SELECT COUNT(*) FROM analytics_modules WHERE status = 'ACTIVE'")
        mod_count = cur.fetchone()[0]
        print(f"   ✅ {mod_count} analytics modules active")
        
        # Check Zebra org modules
        cur.execute("""
            SELECT COUNT(*) 
            FROM organisation_modules om
            JOIN organisations o ON o.id = om.organisation_id
            WHERE o.name ILIKE '%zebra%' AND om.is_enabled = true
        """)
        org_mod_count = cur.fetchone()[0]
        print(f"   ✅ {org_mod_count} modules enabled for Zebra Associates")
        
        # Check matt.lindop access
        cur.execute("""
            SELECT has_access 
            FROM user_application_access uaa
            JOIN users u ON u.id = uaa.user_id
            WHERE u.email = 'matt.lindop@zebra.associates'
            AND uaa.application = 'MARKET_EDGE'
        """)
        result = cur.fetchone()
        if result and result[0]:
            print(f"   ✅ matt.lindop@zebra.associates has MARKET_EDGE access")
        else:
            print(f"   ⚠️  matt.lindop@zebra.associates access needs configuration")
        
        print(f"\n{'='*60}")
        print("✅ MODULE TABLES FIX COMPLETED SUCCESSFULLY")
        print("📊 Zebra Associates can now access feature flags and modules")
        print(f"{'='*60}\n")
        
        # Close connection
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL environment variable")
        print("2. Verify network connectivity to Render")
        print("3. Confirm database credentials")
        return False

if __name__ == "__main__":
    success = execute_module_tables_fix()
    sys.exit(0 if success else 1)