#!/usr/bin/env python3
"""
Fix existing database record with invalid enum value
Production Database Enum Fix Script
Author: DevOps Engineer
Date: 2025-08-18
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.models.organisation import Organisation
from app.models.base import Base

def fix_database_enum_values():
    """Fix existing database records with invalid enum values"""
    
    print("🔧 PRODUCTION DATABASE ENUM FIX")
    print("==============================")
    print("Target: Fix existing 'Default' organization with invalid enum value")
    print()
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            print("🔍 Checking for organizations with invalid enum values...")
            
            # Use raw SQL to check current values
            result = db.execute(text("""
                SELECT id, name, industry_type 
                FROM organisations 
                WHERE name = 'Default' OR industry_type = 'default'
            """))
            
            records = result.fetchall()
            print(f"Found {len(records)} records to fix:")
            
            for record in records:
                print(f"  - ID: {record.id}, Name: {record.name}, Industry: {record.industry_type}")
            
            if records:
                print()
                print("🛠️  Fixing invalid enum values...")
                
                # Update the invalid enum values
                update_result = db.execute(text("""
                    UPDATE organisations 
                    SET industry_type = 'DEFAULT'
                    WHERE industry_type = 'default' OR name = 'Default'
                """))
                
                db.commit()
                
                print(f"✅ Updated {update_result.rowcount} records")
                print("   Changed: industry_type='default' → industry_type='DEFAULT'")
                
                # Verify the fix
                print()
                print("🔍 Verifying fix...")
                verify_result = db.execute(text("""
                    SELECT id, name, industry_type 
                    FROM organisations 
                    WHERE name = 'Default'
                """))
                
                fixed_records = verify_result.fetchall()
                for record in fixed_records:
                    print(f"  ✅ ID: {record.id}, Name: {record.name}, Industry: {record.industry_type}")
                
            else:
                print("✅ No records found with invalid enum values")
                
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False
    
    print()
    print("🎉 DATABASE ENUM FIX COMPLETE")
    print("The 'Default' organization now has proper enum value: 'DEFAULT'")
    print("Auth0 login should now work without 500 errors")
    return True

if __name__ == "__main__":
    success = fix_database_enum_values()
    sys.exit(0 if success else 1)