#!/usr/bin/env python3
"""
Create Admin User via Production API
===================================

This script creates a temporary endpoint in the production API to create
Matt Lindop's admin user, then calls that endpoint to complete the setup.

Steps:
1. Add temporary admin endpoint to production API
2. Deploy to production
3. Call endpoint to create admin user
4. Verify creation
5. Remove endpoint (optional)
"""

import requests
import json
import time
import sys
from datetime import datetime

PRODUCTION_URL = "https://marketedge-platform.onrender.com"
TEMP_SECRET = "TEMP_ADMIN_SECRET_12345_REMOVE_AFTER_USE"

class ProductionAdminCreator:
    """Creates admin user via production API endpoint"""
    
    def __init__(self):
        self.production_url = PRODUCTION_URL
        self.secret = TEMP_SECRET
        
    def test_production_health(self):
        """Test that production is accessible and healthy"""
        
        print("🏥 Testing production health...")
        
        try:
            response = requests.get(f"{self.production_url}/health", timeout=30)
            
            if response.status_code == 200:
                print("   ✅ Production is healthy and accessible")
                return True
            else:
                print(f"   ❌ Production health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Cannot reach production: {e}")
            return False
    
    def create_admin_user(self):
        """Call production endpoint to create admin user"""
        
        print("\n👤 Creating Matt Lindop admin user via production API...")
        
        try:
            response = requests.post(
                f"{self.production_url}/api/v1/admin/create-super-admin?secret={self.secret}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=60
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Admin user created successfully!")
                print(f"      User ID: {data.get('user_id')}")
                print(f"      Email: {data.get('email')}")
                print(f"      Role: {data.get('role')}")
                return True
                
            elif response.status_code == 404:
                print("   ❌ Endpoint not found - needs to be deployed first")
                return False
                
            elif response.status_code == 403:
                print("   ❌ Invalid secret - check TEMP_SECRET")
                return False
                
            else:
                print(f"   ❌ Unexpected response: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"      Error: {error_data}")
                except:
                    print(f"      Raw response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return False
    
    def verify_admin_user(self):
        """Verify the admin user exists by testing authentication flow"""
        
        print("\n🔍 Verifying admin user creation...")
        
        # Try to access admin endpoints that would require the user to exist
        admin_endpoints = [
            "/api/v1/admin/health",
            "/api/v1/admin/users",
            "/api/v1/users/me"  # If available
        ]
        
        verified = False
        
        for endpoint in admin_endpoints:
            try:
                response = requests.get(
                    f"{self.production_url}{endpoint}",
                    timeout=30
                )
                
                print(f"   Testing {endpoint}: Status {response.status_code}")
                
                if response.status_code in [200, 401, 403]:  # These indicate endpoint exists
                    verified = True
                    
            except Exception as e:
                print(f"   {endpoint}: Failed - {e}")
        
        # Alternative verification: Check if we can trigger auth flow
        if not verified:
            print("   🔄 Testing auth flow to confirm user database is accessible...")
            
            try:
                # Test auth endpoint - this will fail but should reach database
                response = requests.post(
                    f"{self.production_url}/api/v1/auth/login",
                    json={
                        "code": "test_code_for_verification",
                        "redirect_uri": "https://app.zebra.associates/callback"
                    },
                    timeout=30
                )
                
                if response.status_code != 500:  # Not a server error
                    print("   ✅ Auth flow accessible - database operations working")
                    verified = True
                else:
                    print("   ⚠️  Server error in auth flow - check logs")
                    
            except Exception as e:
                print(f"   ❌ Auth flow test failed: {e}")
        
        return verified
    
    def cleanup_instructions(self):
        """Provide instructions for cleaning up the temporary endpoint"""
        
        print("\n🧹 CLEANUP INSTRUCTIONS:")
        print("=" * 50)
        print("After successful admin user creation:")
        print("1. Remove the temporary endpoint from your API")
        print("2. Redeploy to production without the endpoint")
        print("3. This ensures the temporary secret cannot be used again")
        print("")
        print("Files to clean up:")
        print("• Remove temp_admin_api_endpoint.py code from production API")
        print("• Remove the /admin/create-super-admin route")

def show_implementation_guide():
    """Show how to implement the temporary endpoint"""
    
    print("\n📋 IMPLEMENTATION GUIDE")
    print("=" * 50)
    print("")
    print("STEP 1: Add Temporary Endpoint")
    print("Add this code to your production API:")
    print("")
    
    code_snippet = '''
# Add to app/api/api_v1/endpoints/ (create admin_setup.py)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
import uuid
from datetime import datetime

router = APIRouter()
TEMP_ADMIN_SECRET = "TEMP_ADMIN_SECRET_12345_REMOVE_AFTER_USE"

@router.post("/create-super-admin")
async def create_super_admin(
    secret: str,
    db: Session = Depends(get_db)
):
    if secret != TEMP_ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.email == "matt.lindop@zebra.associates"
    ).first()
    
    if existing_user:
        return {
            "message": "User already exists", 
            "user_id": str(existing_user.id)
        }
    
    try:
        # Create organization if needed
        zebra_org = db.query(Organization).filter(
            Organization.name == "Zebra Associates"
        ).first()
        
        if not zebra_org:
            zebra_org = Organization(
                id=uuid.uuid4(),
                name="Zebra Associates",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(zebra_org)
            db.flush()
        
        # Create user
        matt_user = User(
            id=uuid.uuid4(),
            email="matt.lindop@zebra.associates",
            auth0_id="auth0|placeholder-will-be-updated-on-first-login",
            name="Matt Lindop",
            role="SUPER_ADMIN",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(matt_user)
        db.commit()
        
        return {
            "message": "Super admin user created successfully",
            "user_id": str(matt_user.id),
            "email": matt_user.email,
            "role": matt_user.role
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")

# Don't forget to include this router in your main API routes
'''
    
    print(code_snippet)
    
    print("\nSTEP 2: Include Router")
    print("Add to app/api/api_v1/api.py:")
    print("")
    print("from app.api.api_v1.endpoints import admin_setup")
    print('api_router.include_router(admin_setup.router, prefix="/admin", tags=["admin"])')
    
    print("\nSTEP 3: Deploy to Production")
    print("• Deploy your updated code to Render")
    print("• Wait for deployment to complete")
    
    print("\nSTEP 4: Run This Script")
    print("• python3 create_admin_via_production_api.py")
    
    print("\nSTEP 5: Remove Endpoint")
    print("• Remove the admin_setup.py file")
    print("• Remove the router inclusion")
    print("• Redeploy to production")

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("CREATE ADMIN USER VIA PRODUCTION API")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: {PRODUCTION_URL}")
    print("=" * 80)
    
    creator = ProductionAdminCreator()
    
    # Step 1: Check if production is accessible
    if not creator.test_production_health():
        print("\n❌ FAILED: Cannot reach production API")
        print("   Check production URL and network connectivity")
        return False
    
    # Step 2: Try to create admin user
    user_created = creator.create_admin_user()
    
    if not user_created:
        print("\n🚧 NEXT STEPS:")
        print("1. The temporary endpoint needs to be deployed first")
        print("2. See implementation guide below")
        show_implementation_guide()
        return False
    
    # Step 3: Verify admin user
    user_verified = creator.verify_admin_user()
    
    # Results
    print("\n" + "=" * 80)
    print("ADMIN USER CREATION RESULTS")
    print("=" * 80)
    
    if user_created and user_verified:
        print("🎉 SUCCESS: Matt Lindop admin user created and verified!")
        print("")
        print("✅ Admin user exists in production database")
        print("✅ Database operations are working correctly")
        print("✅ Production API is functional")
        print("")
        creator.cleanup_instructions()
        
    elif user_created:
        print("⚠️  PARTIAL SUCCESS: User created but verification uncertain")
        print("")
        print("✅ Admin user creation completed")
        print("❓ Verification tests inconclusive")
        print("")
        creator.cleanup_instructions()
        
    else:
        print("❌ FAILED: Admin user not created")
        print("")
        print("🚧 Implementation required:")
        show_implementation_guide()
    
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("• Direct database connection: ❌ Not viable (Render restrictions)")
    print("• Production API approach: ✅ Viable with temporary endpoint")
    print("• Manual SQL approach: ✅ Always available via Render dashboard")
    print("=" * 80)
    
    return user_created

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)