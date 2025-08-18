#!/usr/bin/env python3
"""
Production Auth Endpoint Test
============================

This script tests the production authentication endpoint directly with real Auth0 tokens
to capture the exact error that occurs with real user data.

USAGE:
1. Get a fresh Auth0 authorization code or access token
2. Run this script with the token
3. Analyze the detailed error response
"""

import asyncio
import httpx
import json
import os
from urllib.parse import urlencode


class ProductionAuthTester:
    """Test production authentication endpoint with real Auth0 tokens"""
    
    def __init__(self):
        # Production endpoint (adjust as needed)
        self.base_url = os.getenv('BACKEND_URL', 'https://marketedge-platform-backend.onrender.com')
        self.auth_endpoint = f"{self.base_url}/api/v1/auth/login"
        
        print(f"🎯 Testing endpoint: {self.auth_endpoint}")
    
    async def test_auth_endpoint_with_code(self, auth_code: str, redirect_uri: str, state: str = None) -> Dict:
        """Test authentication endpoint with Auth0 authorization code"""
        print(f"\n🔍 Testing with Auth0 authorization code...")
        
        payload = {
            "code": auth_code,
            "redirect_uri": redirect_uri
        }
        
        if state:
            payload["state"] = state
        
        print(f"   Code: {auth_code[:20]}...")
        print(f"   Redirect URI: {redirect_uri}")
        print(f"   State: {state if state else 'None'}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    self.auth_endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                print(f"\n📊 Response Analysis:")
                print(f"   Status Code: {response.status_code}")
                print(f"   Headers: {dict(response.headers)}")
                
                try:
                    response_data = response.json()
                    print(f"   JSON Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   Raw Response: {response.text}")
                
                return {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_data": response_data if 'response_data' in locals() else response.text,
                    "headers": dict(response.headers)
                }
                
            except Exception as e:
                print(f"❌ Request failed: {type(e).__name__}: {str(e)}")
                return {
                    "status_code": 0,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
    
    async def test_auth_endpoint_with_fake_code(self) -> Dict:
        """Test with fake code to confirm 400 response"""
        print(f"\n🔍 Testing with fake code (should get 400)...")
        
        fake_payload = {
            "code": "fake_test_code_12345",
            "redirect_uri": "https://marketedge-platform.onrender.com/callback"
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    self.auth_endpoint,
                    json=fake_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                print(f"   Status Code: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   Raw Response: {response.text}")
                
                return {
                    "status_code": response.status_code,
                    "fake_code_test": True,
                    "expected_400": response.status_code == 400
                }
                
            except Exception as e:
                print(f"❌ Fake code test failed: {str(e)}")
                return {"error": str(e)}
    
    def analyze_error_pattern(self, real_result: Dict, fake_result: Dict):
        """Analyze the error pattern difference"""
        print(f"\n🔬 ERROR PATTERN ANALYSIS")
        print("=" * 40)
        
        print(f"Real Auth0 Code:")
        print(f"   Status: {real_result.get('status_code', 'Unknown')}")
        print(f"   Success: {real_result.get('success', False)}")
        
        print(f"\nFake Test Code:")
        print(f"   Status: {fake_result.get('status_code', 'Unknown')}")
        print(f"   Expected 400: {fake_result.get('expected_400', False)}")
        
        # Determine the failure pattern
        if real_result.get('status_code') == 500:
            print(f"\n🎯 CONFIRMED: Real Auth0 code reaches database operations")
            print(f"   - Real tokens pass Auth0 exchange")
            print(f"   - Failure occurs during user creation/lookup")
            print(f"   - Check detailed error in response for SQLAlchemy issues")
            
        elif real_result.get('status_code') == 400:
            print(f"\n🤔 UNEXPECTED: Real Auth0 code also getting 400")
            print(f"   - This suggests Auth0 exchange is failing")  
            print(f"   - Check Auth0 configuration and token validity")
            
        else:
            print(f"\n❓ UNKNOWN PATTERN: Unexpected status code")
            print(f"   - Review response details for clues")


async def main():
    """Main testing function"""
    print("🚀 PRODUCTION AUTH ENDPOINT TESTING")
    print("=" * 50)
    
    print("\n📝 INSTRUCTIONS:")
    print("1. Get a fresh Auth0 authorization code")
    print("2. Go to your Auth0 application and authenticate")
    print("3. Copy the 'code' parameter from the callback URL")
    print("4. Paste it below")
    
    # Get Auth0 code from user
    auth_code = input("\n🔐 Enter Auth0 authorization code: ").strip()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return
    
    # Get redirect URI
    redirect_uri = input("🔗 Enter redirect URI (or press Enter for default): ").strip()
    if not redirect_uri:
        redirect_uri = "https://marketedge-platform.onrender.com/callback"
    
    # Optional state parameter
    state = input("📝 Enter state parameter (optional): ").strip() or None
    
    tester = ProductionAuthTester()
    
    # Test with real Auth0 code
    print(f"\n" + "=" * 60)
    real_result = await tester.test_auth_endpoint_with_code(auth_code, redirect_uri, state)
    
    # Test with fake code for comparison
    print(f"\n" + "=" * 60)
    fake_result = await tester.test_auth_endpoint_with_fake_code()
    
    # Analyze the pattern
    print(f"\n" + "=" * 60)
    tester.analyze_error_pattern(real_result, fake_result)
    
    # Final recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if real_result.get('status_code') == 500:
        print("   1. Check production logs for detailed SQLAlchemy error")
        print("   2. Review database schema and constraints") 
        print("   3. Test user creation with real Auth0 user data locally")
        print("   4. Apply the enhanced logging patches for more detail")
    elif real_result.get('status_code') == 400:
        print("   1. Verify Auth0 configuration matches production")
        print("   2. Check if authorization code has expired")
        print("   3. Confirm redirect URI matches Auth0 settings")
    else:
        print("   1. Review the detailed response for error clues")
        print("   2. Check network connectivity and endpoint availability")


if __name__ == "__main__":
    asyncio.run(main())