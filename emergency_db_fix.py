#!/usr/bin/env python3
"""Emergency database schema fix for production authentication issue"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def main():
    # Get database URL from environment or command line
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Expected format: postgresql://user:password@host:port/database")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        print("Connected successfully. Checking current schema...")
        
        # Check if columns exist
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('department', 'location', 'phone')
        """)
        
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        columns_to_add = []
        if 'department' not in existing_columns:
            columns_to_add.append('department VARCHAR(100)')
        if 'location' not in existing_columns:
            columns_to_add.append('location VARCHAR(100)')
        if 'phone' not in existing_columns:
            columns_to_add.append('phone VARCHAR(20)')
            
        if columns_to_add:
            print(f"Adding columns: {columns_to_add}")
            
            for column_def in columns_to_add:
                sql = f"ALTER TABLE users ADD COLUMN {column_def}"
                print(f"Executing: {sql}")
                cur.execute(sql)
            
            conn.commit()
            print("✓ Columns added successfully!")
        else:
            print("✓ All required columns already exist!")
        
        # Verify final schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print("\nFinal users table schema:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} ({'nullable' if row[2] == 'YES' else 'not null'})")
        
        cur.close()
        conn.close()
        
        print("\n✓ Database schema fix completed successfully!")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()