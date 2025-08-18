#!/usr/bin/env python3
"""
Test SQLAlchemy model import fix

This script tests if the UserApplicationAccess import issue is resolved.
"""

import sys
import os
import traceback

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_model_imports():
    """Test that all models can be imported without SQLAlchemy mapper errors"""
    print("🔧 Testing model imports...")
    try:
        from app.models import (
            User, Organisation, UserApplicationAccess, UserInvitation,
            ApplicationType, InvitationStatus
        )
        print("✅ All models imported successfully")
        print(f"   - User: {User}")
        print(f"   - Organisation: {Organisation}")
        print(f"   - UserApplicationAccess: {UserApplicationAccess}")
        print(f"   - UserInvitation: {UserInvitation}")
        return True
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        traceback.print_exc()
        return False

def test_model_creation():
    """Test creating model instances (without database)"""
    print("\n🔧 Testing model instance creation...")
    try:
        from app.models import User, Organisation, UserRole
        from app.core.rate_limit_config import Industry
        from app.models.organisation import SubscriptionPlan
        
        # Create organisation instance (without saving)
        org = Organisation(
            name="Test Org",
            industry="Technology", 
            industry_type=Industry.DEFAULT.value,
            subscription_plan=SubscriptionPlan.basic.value
        )
        print(f"✅ Organisation instance created: {org.name}")
        
        # Create user instance (without saving)
        import uuid
        user = User(
            email="test@example.com",
            first_name="Test",
            last_name="User", 
            organisation_id=uuid.uuid4(),
            role=UserRole.viewer
        )
        print(f"✅ User instance created: {user.email}")
        
        return True
    except Exception as e:
        print(f"❌ Model instance creation failed: {e}")
        traceback.print_exc()
        return False

def test_enum_values():
    """Test enum values work correctly"""
    print("\n🔧 Testing enum values...")
    try:
        from app.core.rate_limit_config import Industry
        from app.models.organisation import SubscriptionPlan
        from app.models.user import UserRole
        
        print(f"Industry.DEFAULT.value = {Industry.DEFAULT.value}")
        print(f"SubscriptionPlan.basic.value = {SubscriptionPlan.basic.value}")
        print(f"UserRole.viewer = {UserRole.viewer}")
        print("✅ Enum values work correctly")
        return True
    except Exception as e:
        print(f"❌ Enum values failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing SQLAlchemy Model Import Fix")
    print("=" * 50)
    
    tests = [
        test_model_imports,
        test_model_creation,
        test_enum_values
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    total_passed = sum(results)
    total_tests = len(tests)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 SQLAlchemy model import fix successful!")
        print("The UserApplicationAccess import issue should be resolved.")
    else:
        print("❌ Model import issues still exist.")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)