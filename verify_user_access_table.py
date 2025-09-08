#!/usr/bin/env python3
"""
Direct database check to verify if user_application_access table exists
"""
import os
import sys
import psycopg2
from urllib.parse import urlparse

def check_table_exists():
    """Check if user_application_access table exists in production database"""
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            print("Please set DATABASE_URL environment variable")
            return False
            
        # Parse database URL  
        parsed = urlparse(database_url)
        
        # Connect directly with psycopg2
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        # Check if user_application_access table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'user_application_access'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        # Check if user_invitations table exists  
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'user_invitations'
            )
        """)
        invitations_table_exists = cur.fetchone()[0]
        
        # Check if required enums exist
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'applicationtype'
            )
        """)
        app_type_enum_exists = cur.fetchone()[0]
        
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type 
                WHERE typname = 'invitationstatus'
            )
        """)
        invitation_status_enum_exists = cur.fetchone()[0]
        
        # Get table structure if it exists
        if table_exists:
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'user_application_access'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            cur.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_name = 'user_application_access'
            """)
            constraints = cur.fetchall()
            
        cur.close()
        conn.close()
        
        # Print results
        print("🔍 Production Database Schema Check")
        print("=" * 50)
        
        print(f"✅ user_application_access table: {'EXISTS' if table_exists else 'MISSING'}")
        print(f"✅ user_invitations table: {'EXISTS' if invitations_table_exists else 'MISSING'}")
        print(f"✅ applicationtype enum: {'EXISTS' if app_type_enum_exists else 'MISSING'}")
        print(f"✅ invitationstatus enum: {'EXISTS' if invitation_status_enum_exists else 'MISSING'}")
        
        if table_exists:
            print("\n📋 user_application_access table structure:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'} {col[3] or ''}")
            
            print(f"\n🔒 Constraints:")
            for constraint in constraints:
                print(f"  - {constraint[0]}: {constraint[1]}")
        
        if table_exists and invitations_table_exists and app_type_enum_exists and invitation_status_enum_exists:
            print("\n✅ ALL REQUIRED TABLES AND ENUMS EXIST")
            print("✅ Authentication system should work correctly")
            return True
        else:
            print("\n❌ MISSING REQUIRED DATABASE OBJECTS")
            print("❌ Authentication system will fail")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--render":
        # Use Render database URL format
        database_url = "postgresql://marketedge_user:DPPY3MXG4oj92kVCEm8zD0VwTkLInxo5@dpg-cs8nqv52ng1s73aebqeg-a.oregon-postgres.render.com/marketedge_postgres"
        os.environ['DATABASE_URL'] = database_url
        print("Using Render database connection...")
    
    success = check_table_exists()
    sys.exit(0 if success else 1)