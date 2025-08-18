#!/usr/bin/env python3
"""
Direct database test to diagnose enum type issues in organisation creation
"""

import requests
import json

BASE_URL = "https://marketedge-platform.onrender.com"

def test_enum_diagnosis():
    """Test specific enum issues that might be preventing auth"""
    
    print("=" * 60)
    print("DATABASE ENUM DIAGNOSIS")
    print("=" * 60)
    
    # Test 1: Check what enum values exist in database
    print("\n1. CHECKING POSTGRESQL ENUM TYPES...")
    try:
        # Create a test endpoint to get enum values
        response = requests.post(f"{BASE_URL}/api/v1/database/emergency-fix")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Organisation columns: {json.dumps(data.get('organisation_columns', {}), indent=2)}")
        else:
            print(f"✗ Emergency fix check failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error checking database: {e}")
    
    # Test 2: Try to create a basic organisation with different enum values
    print("\n2. TESTING ORGANISATION CREATION WITH ENUM VALUES...")
    
    test_cases = [
        {
            "name": "Test Org Default",
            "industry_type": "default",
            "subscription_plan": "basic"
        },
        {
            "name": "Test Org Cinema", 
            "industry_type": "cinema",
            "subscription_plan": "basic"
        },
        {
            "name": "Test Org String Values",
            "industry_type": "DEFAULT",  # Try uppercase
            "subscription_plan": "BASIC"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n  Test {i+1}: {test_case['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/organisations/",
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            print(f"    Status: {response.status_code}")
            if response.status_code != 200:
                print(f"    Error: {response.text}")
            else:
                print(f"    Success: {response.json()}")
        except Exception as e:
            print(f"    Exception: {e}")
    
    # Test 3: Direct auth flow test with minimal data
    print("\n3. TESTING AUTH FLOW WITH MINIMAL TOKEN...")
    
    # Create a simple test token payload
    test_token = "test_token_for_enum_diagnosis"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"access_token": test_token},
            headers={"Content-Type": "application/json"}
        )
        print(f"    Auth Status: {response.status_code}")
        print(f"    Auth Response: {response.text}")
    except Exception as e:
        print(f"    Auth Exception: {e}")

def check_sic_codes_table():
    """Check if sic_codes table exists and has data"""
    print("\n4. CHECKING SIC_CODES TABLE...")
    
    # Since there's no direct endpoint, we'll try to create an org with a sic_code
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/organisations/",
            json={
                "name": "Test SIC Code Org",
                "industry_type": "default",
                "subscription_plan": "basic",
                "sic_code": "59140"  # Cinema SIC code
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"    SIC Code Test Status: {response.status_code}")
        if response.status_code != 200:
            print(f"    SIC Code Error: {response.text}")
            if "foreign key" in response.text.lower() or "constraint" in response.text.lower():
                print("    ✗ SIC_CODES table missing or constraint issue")
        else:
            print(f"    ✓ SIC Code creation successful: {response.json()}")
    except Exception as e:
        print(f"    SIC Code Exception: {e}")

if __name__ == "__main__":
    test_enum_diagnosis()
    check_sic_codes_table()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)