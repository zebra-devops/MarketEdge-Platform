#!/usr/bin/env python3
"""
Quick Production Database Enum Check

This script quickly checks the production database to confirm the enum issue.
"""

import os
import asyncio
import httpx
import json

async def test_production_auth():
    """Test production auth endpoint with a test code"""
    print("=== TESTING PRODUCTION AUTH ENDPOINT ===")
    
    # Test with the actual production URL
    url = "https://marketedge-platform.onrender.com/api/v1/auth/login"
    
    # Use a fake but properly formatted auth code for testing
    # This will trigger the database query that's failing
    test_data = {
        "code": "test_code_for_enum_debugging_12345",
        "redirect_uri": "https://marketedge-platform.onrender.com/auth/callback",
        "state": "test_state"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=test_data, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
            
            # Check if this is the enum error we're looking for
            if response.status_code == 500:
                if "default" in response.text.lower() and "enum" in response.text.lower():
                    print("\n❌ CONFIRMED: This is the enum case mismatch issue!")
                    print("The database contains lowercase 'default' but enum expects uppercase 'DEFAULT'")
                    return True
                else:
                    print("\n❓ 500 error but not the enum issue we expected")
                    return False
            else:
                print(f"\n✅ No 500 error (got {response.status_code})")
                return False
                
    except Exception as e:
        print(f"Request failed: {e}")
        return False

async def check_health_endpoint():
    """Check if the app is running"""
    print("=== CHECKING HEALTH ENDPOINT ===")
    
    url = "https://marketedge-platform.onrender.com/health"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            print(f"Health Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Application is running")
                return True
            else:
                print("❌ Application health check failed")
                return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

async def main():
    """Main execution"""
    print("Quick Production Enum Issue Check\n")
    
    # First check if app is running
    if not await check_health_endpoint():
        print("Cannot proceed - application is not responding")
        return
    
    print()
    
    # Test the auth endpoint to confirm the enum issue
    is_enum_issue = await test_production_auth()
    
    print("\n" + "="*60)
    if is_enum_issue:
        print("DIAGNOSIS: ENUM CASE MISMATCH CONFIRMED")
        print("- Database has lowercase 'default' enum values")
        print("- Code expects uppercase 'DEFAULT' enum values")
        print("- This is preventing user authentication")
        print("\nRECOMMENDED ACTION:")
        print("1. Run the emergency_enum_fix.py script to investigate")
        print("2. Apply the enum case fix to update 'default' -> 'DEFAULT'")
        print("3. Test authentication again")
    else:
        print("DIAGNOSIS: May not be the enum issue")
        print("Need further investigation of the 500 error")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())