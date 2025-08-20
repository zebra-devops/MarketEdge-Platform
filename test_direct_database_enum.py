#!/usr/bin/env python3
"""
Direct Database Enum Test

This script directly tests the organisation creation and enum handling
to identify if the enum case issue still exists.
"""

import asyncio
import sys
import os

# Add the app directory to the path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_enum_issue_directly():
    """Test if we can reproduce the enum issue directly"""
    print("=== DIRECT DATABASE ENUM TEST ===")
    
    try:
        # Import the models and database connection
        from app.core.database import get_db
        from app.models.organisation import Organisation, SubscriptionPlan
        from app.core.rate_limit_config import Industry
        from sqlalchemy.orm import Session
        from sqlalchemy.exc import SQLAlchemyError
        
        print("✅ Imports successful")
        
        # Get a database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        print("✅ Database session created")
        
        # Test 1: Check if we can query existing organisations
        print("\n1. Testing existing organisation query:")
        try:
            orgs = db.query(Organisation).limit(5).all()
            print(f"   Found {len(orgs)} organisations")
            
            for org in orgs:
                print(f"   - {org.name}: industry_type='{org.industry_type}' (type: {type(org.industry_type)})")
                
                # Check if we can access the enum value
                try:
                    enum_value = org.industry_type.value if hasattr(org.industry_type, 'value') else str(org.industry_type)
                    print(f"     Enum value: '{enum_value}'")
                except Exception as e:
                    print(f"     ❌ Error accessing enum value: {e}")
                    
        except SQLAlchemyError as e:
            print(f"   ❌ Query failed: {e}")
            if "'default' is not among the defined enum values" in str(e):
                print("   🎯 CONFIRMED: Enum case mismatch issue found!")
                return "enum_issue_confirmed"
        
        # Test 2: Check Default organisation specifically
        print("\n2. Testing Default organisation query:")
        try:
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            
            if default_org:
                print(f"   Found Default org: ID={default_org.id}")
                print(f"   Industry: '{default_org.industry}'")
                print(f"   Industry_Type: '{default_org.industry_type}'")
                
                # Try to access the enum value
                try:
                    enum_val = default_org.industry_type.value
                    print(f"   Enum value: '{enum_val}'")
                except Exception as e:
                    print(f"   ❌ Error accessing enum: {e}")
                    return "enum_access_error"
                    
            else:
                print("   ❌ No Default organisation found")
                return "no_default_org"
                
        except SQLAlchemyError as e:
            print(f"   ❌ Default org query failed: {e}")
            if "'default' is not among the defined enum values" in str(e):
                print("   🎯 CONFIRMED: Default org has enum case mismatch!")
                return "default_org_enum_issue"
        
        # Test 3: Try creating a new organisation with DEFAULT enum
        print("\n3. Testing new organisation creation:")
        try:
            test_org = Organisation(
                name="Test_Enum_Org_12345",
                industry="Test Industry",
                industry_type=Industry.DEFAULT,
                subscription_plan=SubscriptionPlan.basic
            )
            
            db.add(test_org)
            db.flush()  # Don't commit, just flush to test
            
            print(f"   ✅ Organisation created successfully")
            print(f"   Industry_Type: '{test_org.industry_type}'")
            print(f"   Enum value: '{test_org.industry_type.value}'")
            
            # Clean up
            db.rollback()
            
        except SQLAlchemyError as e:
            print(f"   ❌ Organisation creation failed: {e}")
            if "enum" in str(e).lower():
                print("   🎯 ENUM ERROR during creation!")
                return "creation_enum_error"
                
        # Test 4: Check the current Industry enum values
        print("\n4. Checking Industry enum values:")
        try:
            from app.core.rate_limit_config import Industry
            print(f"   Available enum values:")
            for industry in Industry:
                print(f"   - {industry.name} = '{industry.value}'")
                
            print(f"   DEFAULT enum: Industry.DEFAULT = '{Industry.DEFAULT.value}'")
            
        except Exception as e:
            print(f"   ❌ Error checking enum values: {e}")
        
        print("\n✅ All tests completed successfully - no enum issues detected")
        return "no_issues"
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Cannot test database directly - missing dependencies")
        return "import_error"
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return "unexpected_error"
    
    finally:
        # Close database session
        try:
            db.close()
        except:
            pass

def run_enum_diagnosis():
    """Run the enum diagnosis"""
    print("Direct Database Enum Issue Diagnosis")
    print("=" * 50)
    
    # Try to run the async test
    try:
        result = asyncio.run(test_enum_issue_directly())
    except Exception as e:
        print(f"Failed to run async test: {e}")
        result = "test_failed"
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS RESULT:")
    
    if result == "enum_issue_confirmed":
        print("🎯 ENUM CASE MISMATCH CONFIRMED")
        print("Database contains lowercase enum values but code expects uppercase")
        
    elif result == "default_org_enum_issue":
        print("🎯 DEFAULT ORGANISATION ENUM ISSUE")
        print("The Default organisation has a case-sensitive enum mismatch")
        
    elif result == "no_default_org":
        print("❌ NO DEFAULT ORGANISATION")
        print("The system expects a Default organisation but none exists")
        
    elif result == "creation_enum_error":
        print("🎯 ENUM ERROR DURING CREATION")
        print("Cannot create organisations due to enum constraint issues")
        
    elif result == "no_issues":
        print("✅ NO ENUM ISSUES DETECTED")
        print("The enum system appears to be working correctly")
        
    elif result == "import_error":
        print("❓ CANNOT TEST LOCALLY")
        print("Missing database connection or dependencies")
        
    else:
        print("❓ DIAGNOSIS INCONCLUSIVE")
        print(f"Result: {result}")
    
    print("=" * 50)

if __name__ == "__main__":
    run_enum_diagnosis()