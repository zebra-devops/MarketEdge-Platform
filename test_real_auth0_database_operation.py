#!/usr/bin/env python3
"""
Critical Database Operation Test for Real Auth0 Tokens

This script tests the exact database operations that occur when a real Auth0 token
is processed, to identify why test codes work but real tokens cause 500 errors.
"""

import sys
import os
import traceback
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import get_db, engine
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.core.rate_limit_config import Industry
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

def test_database_connection():
    """Test basic database connection"""
    print("🔧 Testing database connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_enum_values():
    """Test that enum values are correctly recognized"""
    print("\n🔧 Testing enum values...")
    try:
        # Test Industry enum
        print(f"Industry.DEFAULT = {Industry.DEFAULT}")
        print(f"Industry.DEFAULT.value = {Industry.DEFAULT.value}")
        
        # Test SubscriptionPlan enum
        print(f"SubscriptionPlan.basic = {SubscriptionPlan.basic}")
        print(f"SubscriptionPlan.basic.value = {SubscriptionPlan.basic.value}")
        
        print("✅ Enum values accessible")
        return True
    except Exception as e:
        print(f"❌ Enum values error: {e}")
        traceback.print_exc()
        return False

def test_default_organisation_creation():
    """Test creating a default organisation with the exact values used in auth"""
    print("\n🔧 Testing default organisation creation...")
    
    # Create a new session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if Default organization already exists
        existing_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if existing_org:
            print(f"✅ Default organisation already exists: {existing_org.id}")
            print(f"   - name: {existing_org.name}")
            print(f"   - industry: {existing_org.industry}")
            print(f"   - industry_type: {existing_org.industry_type}")
            print(f"   - subscription_plan: {existing_org.subscription_plan}")
            db.close()
            return True
        
        # Try to create the exact same organisation as in the auth flow
        print("Creating Default organisation with exact auth flow values...")
        default_org = Organisation(
            name="Default", 
            industry="Technology",
            industry_type=Industry.DEFAULT.value,  # This is the critical line from auth.py:304
            subscription_plan=SubscriptionPlan.basic.value  # This is from auth.py:305
        )
        
        print(f"Organisation object created:")
        print(f"   - name: {default_org.name}")
        print(f"   - industry: {default_org.industry}")
        print(f"   - industry_type: {default_org.industry_type}")
        print(f"   - subscription_plan: {default_org.subscription_plan}")
        
        db.add(default_org)
        print("Organisation added to session, attempting commit...")
        
        db.commit()
        print("✅ Commit successful")
        
        db.refresh(default_org)
        print(f"✅ Default organisation created successfully: {default_org.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Default organisation creation failed: {e}")
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def test_user_creation_with_real_data():
    """Test creating a user with realistic Auth0 data"""
    print("\n🔧 Testing user creation with realistic Auth0 data...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get the default organisation
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if not default_org:
            print("❌ No default organisation found, creating one first...")
            if not test_default_organisation_creation():
                return False
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        
        print(f"Using organisation: {default_org.id}")
        
        # Test with realistic Auth0 user data
        test_cases = [
            {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "description": "Standard user data"
            },
            {
                "email": "test.user+tag@domain.co.uk",
                "first_name": "Test",
                "last_name": "User",
                "description": "Complex email with plus and multiple domains"
            },
            {
                "email": "user@subdomain.example.org",
                "first_name": "",
                "last_name": "",
                "description": "Empty names (common in Auth0)"
            },
            {
                "email": "special.chars.email@test-domain.com",
                "first_name": "Special'Chars",
                "last_name": "Test-Name",
                "description": "Special characters in names"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n  Testing case {i+1}: {test_case['description']}")
            print(f"    Email: {test_case['email']}")
            print(f"    First name: '{test_case['first_name']}'")
            print(f"    Last name: '{test_case['last_name']}'")
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == test_case['email']).first()
            if existing_user:
                print(f"    ✅ User already exists: {existing_user.id}")
                continue
            
            try:
                # Create user exactly as in auth.py:312-321
                user = User(
                    email=test_case['email'],
                    first_name=test_case['first_name'],
                    last_name=test_case['last_name'],
                    organisation_id=default_org.id,
                    role=UserRole.viewer
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                print(f"    ✅ User created successfully: {user.id}")
                
            except Exception as e:
                print(f"    ❌ User creation failed: {e}")
                traceback.print_exc()
                db.rollback()
                return False
        
        print("✅ All user creation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def test_organisation_relationship_loading():
    """Test loading user with organisation relationship"""
    print("\n🔧 Testing organisation relationship loading...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find a user to test with
        user = db.query(User).first()
        if not user:
            print("❌ No users found for relationship testing")
            return False
        
        print(f"Testing with user: {user.email}")
        
        # Test loading relationship as done in auth.py:332
        if not user.organisation:
            print("Organisation not loaded, loading with joinedload...")
            user = db.query(User).options(joinedload(User.organisation)).filter(User.id == user.id).first()
        
        if user.organisation:
            print(f"✅ Organisation relationship loaded: {user.organisation.name}")
            print(f"   - Industry: {user.organisation.industry}")
            print(f"   - Industry type: {user.organisation.industry_type}")
            print(f"   - Subscription plan: {user.organisation.subscription_plan}")
            return True
        else:
            print("❌ Organisation relationship not loaded")
            return False
            
    except Exception as e:
        print(f"❌ Relationship loading failed: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_database_constraints():
    """Test database constraints that might be causing issues"""
    print("\n🔧 Testing database constraints...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test organisation constraints
        print("Testing organisation table constraints...")
        
        # Check if there are any unique constraint violations
        orgs = db.query(Organisation).all()
        org_names = [org.name for org in orgs]
        duplicate_names = [name for name in org_names if org_names.count(name) > 1]
        
        if duplicate_names:
            print(f"⚠️  Found duplicate organisation names: {duplicate_names}")
        else:
            print("✅ No duplicate organisation names")
        
        # Check if all organisations have required fields
        for org in orgs:
            if not org.industry_type:
                print(f"⚠️  Organisation {org.name} has no industry_type")
            if not org.subscription_plan:
                print(f"⚠️  Organisation {org.name} has no subscription_plan")
        
        # Test user constraints
        print("Testing user table constraints...")
        users = db.query(User).all()
        user_emails = [user.email for user in users]
        duplicate_emails = [email for email in user_emails if user_emails.count(email) > 1]
        
        if duplicate_emails:
            print(f"⚠️  Found duplicate user emails: {duplicate_emails}")
        else:
            print("✅ No duplicate user emails")
        
        # Check orphaned users
        orphaned_users = db.query(User).filter(User.organisation_id.is_(None)).all()
        if orphaned_users:
            print(f"⚠️  Found {len(orphaned_users)} users without organisations")
        else:
            print("✅ All users have organisations")
        
        return True
        
    except Exception as e:
        print(f"❌ Constraint testing failed: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """Run all database operation tests"""
    print("🚀 Starting Critical Database Operation Tests for Real Auth0 Tokens")
    print("=" * 70)
    
    tests = [
        test_database_connection,
        test_enum_values,
        test_default_organisation_creation,
        test_user_creation_with_real_data,
        test_organisation_relationship_loading,
        test_database_constraints
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
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    total_passed = sum(results)
    total_tests = len(tests)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All database operations work correctly!")
        print("The issue may be in the Auth0 token exchange or user info retrieval.")
    else:
        print("❌ Database operations have issues that could cause 500 errors.")
        print("These failures might explain why real Auth0 tokens fail.")
    
    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)