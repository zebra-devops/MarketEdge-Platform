#!/usr/bin/env python3
"""
Database User Creation Test Script
=================================

This script tests the database user creation process with realistic Auth0 user data
to identify the exact cause of the 500 "Database error occurred" responses.

FOCUS: Test the database operations that occur AFTER successful Auth0 token exchange
"""

import sys
import os
import traceback

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from backend.app.models.user import User, UserRole
from backend.app.models.organisation import Organisation, SubscriptionPlan
from backend.app.models.base import Base
from backend.app.core.rate_limit_config import Industry
import uuid


class DatabaseUserCreationTester:
    """Test database user creation with realistic Auth0 data"""
    
    def __init__(self):
        # Use the same database URL pattern as the application
        self.database_url = os.getenv(
            'DATABASE_URL', 
            'postgresql://postgres:password@localhost:5432/marketedge'
        )
        
        print(f"🔗 Database URL: {self.database_url}")
        
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            raise
    
    def test_database_connection(self) -> bool:
        """Test basic database connectivity"""
        print("\n🔍 Testing database connection...")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ Database connection successful")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False
    
    def check_existing_tables(self) -> bool:
        """Check if required tables exist"""
        print("\n🔍 Checking required tables...")
        
        try:
            with self.engine.connect() as conn:
                # Check users table
                users_result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'"))
                users_exists = users_result.scalar() > 0
                print(f"   Users table exists: {'✅' if users_exists else '❌'}")
                
                # Check organisations table  
                orgs_result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'organisations'"))
                orgs_exists = orgs_result.scalar() > 0
                print(f"   Organisations table exists: {'✅' if orgs_exists else '❌'}")
                
                if users_exists and orgs_exists:
                    # Check for existing users
                    user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                    org_count = conn.execute(text("SELECT COUNT(*) FROM organisations")).scalar()
                    print(f"   Existing users: {user_count}")
                    print(f"   Existing organisations: {org_count}")
                
                return users_exists and orgs_exists
                
        except Exception as e:
            print(f"❌ Table check failed: {str(e)}")
            return False
    
    def test_realistic_auth0_user_data(self) -> None:
        """Test user creation with realistic Auth0 user data patterns"""
        print("\n🧪 Testing realistic Auth0 user data patterns...")
        
        # Common Auth0 user data patterns that might cause issues
        test_users = [
            {
                "name": "Standard User",
                "email": "test.user@example.com",
                "given_name": "Test",
                "family_name": "User",
                "sub": "auth0|60f7b1b1b1b1b1b1b1b1b1b1"
            },
            {
                "name": "User with empty names",
                "email": "empty.names@example.com", 
                "given_name": "",
                "family_name": "",
                "sub": "auth0|60f7b1b1b1b1b1b1b1b1b1b2"
            },
            {
                "name": "User with None names",
                "email": "none.names@example.com",
                "given_name": None,
                "family_name": None, 
                "sub": "auth0|60f7b1b1b1b1b1b1b1b1b1b3"
            },
            {
                "name": "User with long names",
                "email": "long.names@example.com",
                "given_name": "Very" * 30,  # 120 chars - exceeds 100 char limit
                "family_name": "Long" * 30,  # 120 chars - exceeds 100 char limit  
                "sub": "auth0|60f7b1b1b1b1b1b1b1b1b1b4"
            },
            {
                "name": "User with special characters",
                "email": "special@example.com",
                "given_name": "José",
                "family_name": "González",
                "sub": "auth0|60f7b1b1b1b1b1b1b1b1b1b5"
            }
        ]
        
        for test_user in test_users:
            print(f"\n   Testing: {test_user['name']}")
            self.test_single_user_creation(test_user)
    
    def test_single_user_creation(self, auth0_user_data: dict) -> bool:
        """Test creating a single user with specific Auth0 data"""
        db: Session = self.SessionLocal()
        
        try:
            # Simulate the sanitization process from auth endpoint
            email = auth0_user_data.get('email', '').strip()
            given_name = auth0_user_data.get('given_name') or ''
            family_name = auth0_user_data.get('family_name') or ''
            
            # Apply length limits like the real endpoint
            if len(email) > 254:
                email = email[:254]
            if len(given_name) > 100:
                given_name = given_name[:100] 
            if len(family_name) > 100:
                family_name = family_name[:100]
                
            print(f"      Email: '{email}'")
            print(f"      Given Name: '{given_name}' (len: {len(given_name)})")
            print(f"      Family Name: '{family_name}' (len: {len(family_name)})")
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print(f"      ℹ️ User already exists with ID: {existing_user.id}")
                return True
                
            # Get or create default organization
            default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
            if not default_org:
                print(f"      Creating default organization...")
                default_org = Organisation(
                    name="Default",
                    industry="Technology", 
                    industry_type=Industry.DEFAULT,
                    subscription_plan=SubscriptionPlan.basic
                )
                db.add(default_org)
                db.commit()
                db.refresh(default_org)
                print(f"      ✅ Default org created: {default_org.id}")
            
            # Create user
            print(f"      Creating user...")
            user = User(
                email=email,
                first_name=given_name,
                last_name=family_name,
                organisation_id=default_org.id,
                role=UserRole.viewer
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"      ✅ User created successfully: {user.id}")
            return True
            
        except SQLAlchemyError as e:
            print(f"      ❌ SQLAlchemy Error: {type(e).__name__}")
            print(f"         Message: {str(e)}")
            print(f"         Details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
            db.rollback()
            return False
            
        except Exception as e:
            print(f"      ❌ Unexpected Error: {type(e).__name__}: {str(e)}")
            print(f"         Traceback: {traceback.format_exc()}")
            db.rollback()
            return False
            
        finally:
            db.close()
    
    def test_duplicate_email_constraint(self) -> None:
        """Test duplicate email constraint handling"""
        print("\n🔍 Testing duplicate email constraint...")
        
        test_email = "duplicate.test@example.com"
        
        # Create first user
        success1 = self.test_single_user_creation({
            "email": test_email,
            "given_name": "First",
            "family_name": "User"
        })
        
        # Try to create second user with same email
        success2 = self.test_single_user_creation({
            "email": test_email, 
            "given_name": "Second",
            "family_name": "User"
        })
        
        if success1 and success2:
            print("      ✅ Duplicate handling working correctly")
        else:
            print("      ❌ Issue with duplicate email handling")
    
    def cleanup_test_data(self) -> None:
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        db: Session = self.SessionLocal()
        try:
            # Delete test users
            test_emails = [
                "test.user@example.com",
                "empty.names@example.com", 
                "none.names@example.com",
                "long.names@example.com",
                "special@example.com",
                "duplicate.test@example.com"
            ]
            
            for email in test_emails:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    db.delete(user)
                    print(f"      Deleted user: {email}")
            
            db.commit()
            print("      ✅ Test data cleaned up")
            
        except Exception as e:
            print(f"      ⚠️ Cleanup error: {str(e)}")
            db.rollback()
        finally:
            db.close()


def main():
    """Main test function"""
    print("🚀 DATABASE USER CREATION TESTING")
    print("=" * 50)
    
    try:
        tester = DatabaseUserCreationTester()
        
        # Test 1: Basic connectivity
        if not tester.test_database_connection():
            print("❌ Database connection failed - cannot continue")
            return
            
        # Test 2: Check tables exist
        if not tester.check_existing_tables():
            print("❌ Required tables missing - cannot continue")
            return
            
        # Test 3: Test realistic Auth0 user data
        tester.test_realistic_auth0_user_data()
        
        # Test 4: Test duplicate constraint
        tester.test_duplicate_email_constraint()
        
        # Cleanup
        tester.cleanup_test_data()
        
        print("\n📊 TESTING COMPLETE")
        print("Check output above for specific error details")
        
    except Exception as e:
        print(f"\n❌ TESTING FAILED: {type(e).__name__}: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()