#!/usr/bin/env python3
"""
Auth Database Flow Test

This script simulates the exact database operations that happen during Auth0 authentication
to identify where the 500 error occurs.
"""

import asyncio
import httpx
import json

async def test_auth_with_real_pattern():
    """Test the auth endpoint with a pattern that would trigger the database enum issue"""
    print("=== TESTING AUTH ENDPOINT FOR ENUM ISSUE ===")
    
    # Test with various scenarios that could trigger the enum issue
    test_cases = [
        {
            "name": "Valid Auth0 Code Pattern",
            "data": {
                "code": "valid_looking_auth0_code_12345678901234567890",
                "redirect_uri": "https://marketedge-platform.onrender.com/auth/callback",
                "state": "test_state_123"
            }
        },
        {
            "name": "Short Code Pattern", 
            "data": {
                "code": "abc123",
                "redirect_uri": "https://marketedge-platform.onrender.com/auth/callback"
            }
        },
        {
            "name": "Real Auth0 Code Format",
            "data": {
                "code": "CcklIsb7okABC123DEF456GHI789JKL012MNO345PQR678STU901VWX234YZ567",
                "redirect_uri": "https://marketedge-platform.onrender.com/auth/callback",
                "state": "production_test"
            }
        }
    ]
    
    url = "https://marketedge-platform.onrender.com/api/v1/auth/login"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=test_case['data'], headers=headers)
                
                print(f"Status: {response.status_code}")
                
                # Look for specific error patterns
                response_text = response.text
                
                if response.status_code == 500:
                    print("🚨 500 ERROR FOUND!")
                    
                    # Check for enum-related errors
                    if "enum" in response_text.lower():
                        print("🎯 ENUM ERROR DETECTED!")
                        if "default" in response_text.lower():
                            print("🎯 DEFAULT ENUM VALUE ISSUE!")
                        
                    # Print error details
                    try:
                        error_data = response.json()
                        print(f"Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"Error text: {response_text[:500]}...")
                        
                elif response.status_code == 400:
                    print("✅ 400 error (expected for invalid codes)")
                    try:
                        error_data = response.json()
                        print(f"Details: {error_data.get('detail', 'No detail')}")
                    except:
                        pass
                        
                else:
                    print(f"✅ Unexpected status: {response.status_code}")
                    
                # Add delay between requests
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

async def test_health_and_info():
    """Test health endpoint and get deployment info"""
    print("=== CHECKING DEPLOYMENT STATUS ===")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Health check
            health_response = await client.get("https://marketedge-platform.onrender.com/health")
            print(f"Health: {health_response.status_code}")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"Service: {health_data.get('service_type', 'unknown')}")
                print(f"Version: {health_data.get('version', 'unknown')}")
                print(f"Emergency Mode: {health_data.get('emergency_mode', 'none')}")
                
                # Look for any indicators about the enum fix
                if 'enum' in str(health_data).lower():
                    print("🔍 Enum-related info found in health check")
                    
            # Try to get any debug endpoint if it exists
            try:
                debug_response = await client.get("https://marketedge-platform.onrender.com/debug/status")
                if debug_response.status_code == 200:
                    print("Debug endpoint available")
            except:
                pass
                
    except Exception as e:
        print(f"Health check failed: {e}")

async def simulate_user_creation_scenario():
    """Simulate the scenario that would trigger user creation with Default org"""
    print("=== SIMULATING USER CREATION SCENARIO ===")
    
    # This is the scenario that typically triggers the enum issue:
    # 1. New user tries to authenticate
    # 2. User doesn't exist in database
    # 3. System tries to create user with Default organization
    # 4. Default organization query fails due to enum mismatch
    
    # Create a test request that would likely trigger user creation
    test_data = {
        "code": "NEW_USER_AUTH_CODE_12345",  # Simulate new user auth code
        "redirect_uri": "https://marketedge-platform.onrender.com/auth/callback",
        "state": "new_user_signup"
    }
    
    url = "https://marketedge-platform.onrender.com/api/v1/auth/login"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "EnumTest/1.0 (New User Simulation)"
    }
    
    print("Simulating new user authentication that would trigger Default org lookup...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=test_data, headers=headers)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 500:
                print("🚨 500 ERROR - This might be our enum issue!")
                
                # Check response for enum-related errors
                response_text = response.text
                
                # Look for specific enum error patterns
                enum_indicators = [
                    "'default' is not among the defined enum values",
                    "enum name: industry",
                    "not among the defined enum values",
                    "Enum name: industry"
                ]
                
                found_enum_error = False
                for indicator in enum_indicators:
                    if indicator.lower() in response_text.lower():
                        print(f"🎯 ENUM ERROR CONFIRMED: Found '{indicator}'")
                        found_enum_error = True
                        break
                
                if found_enum_error:
                    print("\n🔥 DIAGNOSIS: Enum case mismatch issue confirmed!")
                    print("The database has lowercase 'default' but enum expects 'DEFAULT'")
                else:
                    print("❓ 500 error but not the enum issue we're looking for")
                
                # Print full error for analysis
                try:
                    error_json = response.json()
                    print(f"\nFull error: {json.dumps(error_json, indent=2)}")
                except:
                    print(f"\nError text: {response_text}")
                    
            else:
                print(f"No 500 error (got {response.status_code}) - enum might be fixed")
                
    except Exception as e:
        print(f"Request failed: {e}")

async def main():
    """Main test execution"""
    print("Auth Database Flow Test - Enum Issue Detection")
    print("=" * 60)
    
    # Step 1: Check deployment status
    await test_health_and_info()
    
    print("\n" + "=" * 60)
    
    # Step 2: Test various auth scenarios
    await test_auth_with_real_pattern()
    
    print("\n" + "=" * 60)
    
    # Step 3: Specifically test the user creation scenario
    await simulate_user_creation_scenario()
    
    print("\n" + "=" * 60)
    print("Test completed. Check for 🎯 ENUM ERROR CONFIRMED messages above.")

if __name__ == "__main__":
    asyncio.run(main())