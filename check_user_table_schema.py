#!/usr/bin/env python3
"""
User Table Schema Inspector for Production Database

This script checks the actual schema of the users table in production
to understand what columns exist and their structure.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy import create_engine, text, inspect
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    sys.exit(1)

def check_users_table_schema():
    """Check the actual schema of the users table"""
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        try:
            from app.core.config import settings
            database_url = settings.DATABASE_URL
        except Exception as e:
            print(f"❌ Could not load database URL: {e}")
            sys.exit(1)
    
    print("🔍 Checking Users Table Schema in Production")
    print("=" * 50)
    
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            inspector = inspect(conn)
            
            # Check if users table exists
            if not inspector.has_table('users'):
                print("❌ Users table does not exist!")
                return
                
            print("✅ Users table exists")
            print()
            
            # Get all columns
            columns = inspector.get_columns('users')
            
            print("COLUMNS IN USERS TABLE:")
            print("-" * 30)
            for i, col in enumerate(columns, 1):
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                default = f" DEFAULT {col.get('default', 'None')}" if col.get('default') else ""
                print(f"{i:2d}. {col['name']:<20} {str(col['type']):<20} {nullable}{default}")
            
            print()
            print(f"Total columns: {len(columns)}")
            
            # Get sample data
            print()
            print("SAMPLE DATA (first 3 users):")
            print("-" * 30)
            
            result = conn.execute(text("SELECT * FROM users LIMIT 3"))
            sample_users = result.fetchall()
            
            if sample_users:
                # Print column headers
                column_names = [col['name'] for col in columns]
                print("ID".ljust(10), end="")
                for name in column_names[1:6]:  # Show first few columns
                    print(name.ljust(20), end="")
                print("...")
                
                # Print sample rows
                for user in sample_users:
                    print(str(user[0]).ljust(10), end="")  # ID
                    for value in user[1:6]:  # First few values
                        display_value = str(value)[:18] if value is not None else "NULL"
                        print(display_value.ljust(20), end="")
                    print("...")
            else:
                print("No users found in table")
            
            # Check specifically for the target user
            print()
            print("CHECKING FOR TARGET USER:")
            print("-" * 30)
            
            result = conn.execute(text("SELECT * FROM users WHERE email = :email"), 
                                {"email": "matt.lindop@zebra.associates"})
            target_user = result.fetchone()
            
            if target_user:
                print("✅ TARGET USER FOUND!")
                print(f"   Email: {target_user[1] if len(target_user) > 1 else 'Unknown'}")
                print(f"   Role: {target_user[2] if len(target_user) > 2 else 'Unknown'}")  
            else:
                print("❌ TARGET USER NOT FOUND: matt.lindop@zebra.associates")
                
                # Show all users for comparison
                print()
                print("ALL USERS IN DATABASE:")
                print("-" * 30)
                result = conn.execute(text("SELECT id, email, role FROM users ORDER BY id"))
                all_users = result.fetchall()
                
                for user in all_users:
                    print(f"   ID: {user[0]}, Email: {user[1]}, Role: {user[2] if len(user) > 2 else 'Unknown'}")
            
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_users_table_schema()