#!/usr/bin/env python3
"""
Test script to verify the auth endpoint enum issue is resolved
"""
import requests
import json

def test_auth_endpoint():
    """Test the auth endpoint with a simulated Auth0 token scenario"""
    
    base_url = "https://marketedge-platform.onrender.com"
    
    print("🔍 Testing Auth Endpoint Enum Issue Fix")
    print("=" * 50)
    
    # Test 1: Check database schema
    print("1. Checking database schema...")
    response = requests.get(f"{base_url}/api/v1/database/schema-check")
    print(f"   Schema check: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Tables: {list(data['tables'].keys())}")
    
    # Test 2: Verify enum fix worked
    print("\n2. Checking enum fix results...")
    response = requests.post(f"{base_url}/api/v1/database/fix-enum-case-issue")
    print(f"   Enum fix: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('fixes', {}).get('enum_test', {}).get('success'):
            print("   ✅ Enum values working correctly")
            org = data['fixes']['enum_test']['org']
            print(f"   Created org with: industry_type='{org['industry_type']}', subscription_plan='{org['subscription_plan']}'")
        else:
            print("   ❌ Enum test failed")
    
    # Test 3: Test auth endpoint with fake code
    print("\n3. Testing auth endpoint...")
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://frontend-2q61uheqm-zebraassociates-projects.vercel.app'
    }
    data = {
        'code': 'test_enum_check',
        'redirect_uri': 'https://frontend-2q61uheqm-zebraassociates-projects.vercel.app/callback'
    }
    
    response = requests.post(f"{base_url}/api/v1/auth/login", headers=headers, data=data)
    print(f"   Auth endpoint: {response.status_code}")
    
    if response.status_code == 400:
        result = response.json()
        if result.get('detail') == 'Failed to exchange authorization code':
            print("   ✅ Auth endpoint working correctly (400 for invalid code)")
        else:
            print(f"   ⚠️  Unexpected 400 response: {result}")
    elif response.status_code == 500:
        result = response.json()
        print(f"   ❌ Still getting 500 error: {result}")
        if result.get('detail') == 'Database error occurred':
            print("   🚨 Database enum issue NOT resolved")
        else:
            print("   🚨 Different 500 error")
    else:
        print(f"   ❓ Unexpected status: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_auth_enum_fix()