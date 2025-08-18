#!/usr/bin/env python3
"""
Test the exact database operations that happen during real Auth0 user creation
"""
import requests
import json

def test_user_creation_simulation():
    """Simulate the exact database operations that happen during Auth0 user creation"""
    
    base_url = "https://marketedge-platform.onrender.com"
    
    print("🔍 Testing Realistic User Creation Scenario")
    print("=" * 60)
    
    # Create a test endpoint that simulates EXACTLY what happens during Auth0 user creation
    test_payload = {
        "test_scenario": "real_auth0_user_creation",
        "user_data": {
            "email": "test.user@example.com",
            "given_name": "Test",
            "family_name": "User"
        }
    }
    
    print("Creating test endpoint for realistic user creation...")
    print("This will trigger the EXACT same database operations as real Auth0")
    
    # We need to create an endpoint that does exactly what the auth flow does:
    # 1. Create default organization if it doesn't exist
    # 2. Create user with proper relationships
    # 3. Use the exact same enum values and constraints
    
    endpoint_code = '''
@router.post("/test-user-creation")
async def test_user_creation_realistic(db: Session = Depends(get_db)):
    """Test the exact user creation flow that happens during Auth0 authentication"""
    try:
        from ....models.user import User, UserRole
        from ....models.organisation import Organisation, SubscriptionPlan
        from ....core.rate_limit_config import Industry
        
        # Step 1: Create default organization (same as auth.py lines 297-309)
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        if not default_org:
            default_org = Organisation(
                name="Default", 
                industry="Technology",
                industry_type=Industry.DEFAULT.value,  # This is the critical line
                subscription_plan=SubscriptionPlan.basic.value
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
        
        # Step 2: Create user (same as auth.py lines 312-321)
        user = User(
            email="test.auth.user@example.com",
            first_name="Auth",
            last_name="Test",
            organisation_id=default_org.id,
            role=UserRole.viewer
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "status": "success",
            "message": "User creation simulation successful",
            "user_id": str(user.id),
            "org_id": str(default_org.id)
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc(),
            "error_type": type(e).__name__
        }
    '''
    
    print(f"Need to add this test endpoint to: {base_url}/api/v1/database/test-user-creation")
    print("This will reveal the EXACT error that happens during real Auth0 user creation")
    
    return "Test endpoint code generated - needs to be added to database.py"

if __name__ == "__main__":
    result = test_user_creation_simulation()
    print(result)