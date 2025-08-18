#!/usr/bin/env python3
"""
Fix enum constraint issue by temporarily disabling enum validation
Production Database Enum Constraint Fix
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

def fix_enum_constraint():
    """Fix enum constraint issue by recreating records properly"""
    
    print("🔧 PRODUCTION DATABASE ENUM CONSTRAINT FIX")
    print("=========================================")
    print("Target: Fix enum constraint validation issue")
    print()
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            print("🔍 Checking current problematic records...")
            
            # Check current records
            result = conn.execute(text("""
                SELECT id, name, industry_type 
                FROM organisations 
                WHERE name = 'Default' OR industry_type = 'default'
            """))
            
            records = list(result.fetchall())
            print(f"Found {len(records)} records with enum issues:")
            
            for record in records:
                print(f"  - ID: {record.id}, Name: {record.name}, Industry: {record.industry_type}")
            
            if records:
                print()
                print("🛠️  Method 1: Trying direct update...")
                
                try:
                    # Try updating with the same value (this should work if enum is properly defined)
                    update_result = conn.execute(text("""
                        UPDATE organisations 
                        SET industry_type = 'default'
                        WHERE industry_type = 'default'
                    """))
                    
                    print(f"✅ Direct update successful: {update_result.rowcount} records")
                    
                except Exception as e:
                    print(f"❌ Direct update failed: {e}")
                    print()
                    print("🛠️  Method 2: Recreating problematic records...")
                    
                    # Get the problematic record details
                    default_org = conn.execute(text("""
                        SELECT id, name, industry, subscription_plan, is_active, 
                               rate_limit_per_hour, burst_limit, rate_limit_enabled, sic_code
                        FROM organisations 
                        WHERE name = 'Default'
                    """)).fetchone()
                    
                    if default_org:
                        print(f"Found Default organization: {default_org.id}")
                        
                        # Delete the problematic record
                        conn.execute(text("""
                            DELETE FROM organisations WHERE id = :id
                        """), {"id": default_org.id})
                        
                        print("🗑️  Deleted problematic record")
                        
                        # Create a new record with proper enum value
                        conn.execute(text("""
                            INSERT INTO organisations (
                                id, name, industry, industry_type, subscription_plan, is_active,
                                rate_limit_per_hour, burst_limit, rate_limit_enabled, sic_code
                            ) VALUES (
                                :id, :name, :industry, 'default', :subscription_plan, :is_active,
                                :rate_limit_per_hour, :burst_limit, :rate_limit_enabled, :sic_code
                            )
                        """), {
                            "id": default_org.id,
                            "name": default_org.name,
                            "industry": default_org.industry,
                            "subscription_plan": default_org.subscription_plan,
                            "is_active": default_org.is_active,
                            "rate_limit_per_hour": default_org.rate_limit_per_hour,
                            "burst_limit": default_org.burst_limit,
                            "rate_limit_enabled": default_org.rate_limit_enabled,
                            "sic_code": default_org.sic_code
                        })
                        
                        print("✅ Recreated Default organization with proper enum value")
                
                # Clean up test records
                print()
                print("🧹 Cleaning up test records...")
                cleanup_result = conn.execute(text("""
                    DELETE FROM organisations 
                    WHERE name IN ('Test Direct Value', 'Test Values Callable')
                    AND industry_type = 'default'
                """))
                
                print(f"✅ Cleaned up {cleanup_result.rowcount} test records")
                
                # Commit the transaction
                trans.commit()
                print()
                print("💾 Changes committed to database")
                
            else:
                print("✅ No problematic records found")
                trans.rollback()
                
    except Exception as e:
        print(f"❌ Error fixing enum constraint: {e}")
        return False
    
    print()
    print("🎉 DATABASE ENUM CONSTRAINT FIX COMPLETE")
    print("The Default organization should now work with enum validation")
    print("Auth0 login should now work without 500 errors")
    return True

if __name__ == "__main__":
    success = fix_enum_constraint()
    sys.exit(0 if success else 1)