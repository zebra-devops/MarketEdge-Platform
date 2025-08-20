#!/usr/bin/env python3
"""
Direct Database Enum Test

This script tests the database enum issue directly by simulating the exact query
that fails in the auth endpoint.
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError

async def test_enum_query_async():
    """Test the problematic enum query asynchronously"""
    print("=== TESTING ENUM QUERY DIRECTLY ===")
    
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("This test requires a direct database connection")
        return False
    
    # Convert to async URL if needed
    if database_url.startswith('postgresql://'):
        async_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
    else:
        async_url = database_url
    
    try:
        engine = create_async_engine(async_url, echo=False)
        
        async with engine.begin() as conn:
            # Test 1: Check current enum values
            print("\n1. Checking current enum values in database:")
            result = await conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'industry')
                ORDER BY enumlabel;
            """))
            enum_values = [row[0] for row in result.fetchall()]
            print(f"   Enum values: {enum_values}")
            
            # Test 2: Check Default organisation record
            print("\n2. Checking Default organisation:")
            result = await conn.execute(text("""
                SELECT id, name, industry, industry_type::text
                FROM organisations 
                WHERE name = 'Default'
                LIMIT 1;
            """))
            default_org = result.fetchone()
            
            if default_org:
                print(f"   Found Default org: ID={default_org[0]}, Industry={default_org[2]}, Industry_Type='{default_org[3]}'")
                
                # Test 3: Try to query it (this is what fails in auth.py)
                print("\n3. Testing the exact auth.py query:")
                try:
                    result = await conn.execute(text("""
                        SELECT id, name, industry_type 
                        FROM organisations 
                        WHERE name = 'Default';
                    """))
                    org = result.fetchone()
                    print(f"   ✅ Query successful: ID={org[0]}, Industry_Type={org[2]}")
                    
                    # Test 4: Check if we can access the enum value
                    print("\n4. Testing enum value access:")
                    print(f"   Industry_Type value: '{org[2]}'")
                    print(f"   Type: {type(org[2])}")
                    
                    return True
                    
                except SQLAlchemyError as e:
                    print(f"   ❌ Query failed with SQLAlchemy error: {e}")
                    if "'default' is not among the defined enum values" in str(e):
                        print("   🎯 CONFIRMED: This is the enum case mismatch issue!")
                    return False
                    
            else:
                print("   ❌ No Default organisation found")
                return False
            
    except Exception as e:
        print(f"❌ Connection or query failed: {e}")
        return False
    finally:
        await engine.dispose()

def test_enum_query_sync():
    """Test the problematic enum query synchronously"""
    print("=== TESTING ENUM QUERY DIRECTLY (SYNC) ===")
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("Testing with local database approach...")
        
        # Try common local database URLs
        test_urls = [
            "postgresql://postgres:password@localhost:5432/marketedge",
            "postgresql://user:password@localhost:5432/marketedge_dev",
            "sqlite:///./test.db"
        ]
        
        for url in test_urls:
            print(f"Trying: {url}")
            try:
                engine = create_engine(url, echo=False)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    database_url = url
                    print(f"✅ Connected to: {url}")
                    break
            except:
                continue
        
        if not database_url:
            print("❌ No database connection available")
            return False
    
    try:
        engine = create_engine(database_url, echo=False)
        
        with engine.connect() as conn:
            # Test the exact problematic scenario
            print("\n1. Testing Default organisation query:")
            
            try:
                result = conn.execute(text("""
                    SELECT id, name, industry, industry_type::text
                    FROM organisations 
                    WHERE name = 'Default'
                    LIMIT 1;
                """))
                
                default_org = result.fetchone()
                
                if default_org:
                    print(f"   Found: ID={default_org[0]}, Name='{default_org[1]}'")
                    print(f"   Industry: '{default_org[2]}'")
                    print(f"   Industry_Type: '{default_org[3]}'")
                    
                    # Check if the enum value is problematic
                    if default_org[3] and default_org[3].lower() == 'default':
                        if default_org[3] != 'DEFAULT':
                            print(f"   🎯 FOUND THE ISSUE: enum value is '{default_org[3]}' but should be 'DEFAULT'")
                            return "enum_case_mismatch"
                        else:
                            print(f"   ✅ Enum value is correct: '{default_org[3]}'")
                            return True
                    else:
                        print(f"   ✅ Enum value seems OK: '{default_org[3]}'")
                        return True
                else:
                    print("   ❌ No Default organisation found")
                    return "no_default_org"
                    
            except SQLAlchemyError as e:
                print(f"   ❌ Query failed: {e}")
                if "'default' is not among the defined enum values" in str(e):
                    print("   🎯 CONFIRMED: Enum case mismatch causing the error!")
                    return "enum_case_mismatch"
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        engine.dispose()

def main():
    """Main execution"""
    print("Direct Database Enum Issue Test")
    print("=" * 50)
    
    # Test with sync approach first (more reliable)
    sync_result = test_enum_query_sync()
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS:")
    
    if sync_result == "enum_case_mismatch":
        print("🎯 CONFIRMED: Database contains lowercase 'default' but enum expects 'DEFAULT'")
        print("\nRESOLUTION STEPS:")
        print("1. The enum values in the database need to be updated")
        print("2. Run: python3 emergency_enum_fix.py --apply")
        print("3. This will update lowercase 'default' to uppercase 'DEFAULT'")
        
    elif sync_result == "no_default_org":
        print("❌ No Default organisation found - this is a different issue")
        print("The auth endpoint expects a Default organisation to exist")
        
    elif sync_result == True:
        print("✅ Database enum values appear to be correct")
        print("The 500 error might be caused by a different issue")
        
    else:
        print("❓ Unable to diagnose the issue - database connection problems")
    
    print("=" * 50)

if __name__ == "__main__":
    main()