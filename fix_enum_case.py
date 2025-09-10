#!/usr/bin/env python3
import os
import psycopg2
from urllib.parse import urlparse

# Get database URL from Railway/Render production environment
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('RAILWAY_DATABASE_URL') or os.getenv('RENDER_DATABASE_URL')

if not DATABASE_URL:
    print("❌ No production database URL found in environment")
    print("Available env vars:", [k for k in os.environ.keys() if 'DATABASE' in k.upper() or 'DB' in k.upper()])
    exit(1)

print(f"🔗 Connecting to production database...")

try:
    # Parse the database URL
    parsed = urlparse(DATABASE_URL)
    
    # Connect to the database
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password
    )
    
    cursor = conn.cursor()
    
    print("✅ Connected to production database")
    
    # First, check current enum values
    print("\n🔍 Checking current ApplicationType enum values...")
    cursor.execute("""
        SELECT enumlabel 
        FROM pg_enum 
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid 
        WHERE pg_type.typname = 'applicationtype'
        ORDER BY enumlabel;
    """)
    
    current_values = [row[0] for row in cursor.fetchall()]
    print(f"Current enum values: {current_values}")
    
    # Check user_application_access table for problematic values
    print("\n🔍 Checking user_application_access table...")
    cursor.execute("""
        SELECT DISTINCT application_type, COUNT(*) 
        FROM user_application_access 
        GROUP BY application_type;
    """)
    
    access_data = cursor.fetchall()
    print(f"Current application_type values in user_application_access:")
    for app_type, count in access_data:
        print(f"  - {app_type}: {count} records")
    
    # Fix the enum case mismatch by updating records
    print("\n🔧 Fixing enum case mismatch...")
    
    # Update lowercase values to uppercase
    updates = [
        ("market_edge", "MARKET_EDGE"),
        ("causal_edge", "CAUSAL_EDGE"), 
        ("value_edge", "VALUE_EDGE")
    ]
    
    total_fixed = 0
    for old_val, new_val in updates:
        cursor.execute("""
            UPDATE user_application_access 
            SET application_type = %s 
            WHERE application_type = %s;
        """, (new_val, old_val))
        
        fixed_count = cursor.rowcount
        if fixed_count > 0:
            print(f"  ✅ Updated {fixed_count} records from '{old_val}' to '{new_val}'")
            total_fixed += fixed_count
    
    # Commit the changes
    conn.commit()
    
    print(f"\n🎉 Successfully fixed {total_fixed} database records")
    
    # Verify the fix
    print("\n✅ Verifying fix - checking user_application_access again...")
    cursor.execute("""
        SELECT DISTINCT application_type, COUNT(*) 
        FROM user_application_access 
        GROUP BY application_type;
    """)
    
    final_data = cursor.fetchall()
    print("Final application_type values:")
    for app_type, count in final_data:
        print(f"  - {app_type}: {count} records")
    
    cursor.close()
    conn.close()
    
    print("\n🎯 Database enum case fix completed successfully!")
    
except Exception as e:
    print(f"❌ Database fix failed: {e}")
    exit(1)