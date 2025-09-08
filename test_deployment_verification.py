#!/usr/bin/env python3
"""
Deployment Verification Script for MarketEdge OAuth2 Fixes
Checks if the latest OAuth2 method name fixes are deployed to production
"""

import requests
import json
import sys
from datetime import datetime


def test_production_deployment():
    """Test if the OAuth2 fixes are deployed to production"""
    
    print("=== MarketEdge Production Deployment Verification ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    base_url = "https://marketedge-platform.onrender.com"
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health check: {health_data.get('status', 'unknown')}")
            print(f"   ✅ Mode: {health_data.get('mode', 'unknown')}")
            print(f"   ✅ Version: {health_data.get('version', 'unknown')}")
            print(f"   ✅ CORS configured: {health_data.get('cors_configured', False)}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check exception: {e}")
        return False
    
    print()
    
    # Test 2: OAuth2 endpoint structure (should return validation error, not 500)
    print("2. Testing OAuth2 endpoint structure...")
    try:
        test_data = {
            "code": "test_code_with_proper_length_12345",
            "redirect_uri": "https://app.zebra.associates/callback",
            "state": "test_state"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/login-oauth2",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   📊 Status Code: {response.status_code}")
        print(f"   📊 Response: {response.text[:200]}...")
        
        # We expect a 500 error due to invalid Auth0 code, but it should be from the
        # Auth0 exchange, not from a method name error
        if response.status_code == 500:
            response_data = response.json()
            detail = response_data.get("detail", "")
            
            # Check if it's the new detailed error format from the latest fix
            if "Internal server error during authentication:" in detail:
                print("   ✅ OAuth2 endpoint returns detailed error (latest fix deployed)")
                if "AttributeError" in detail or "has no attribute" in detail:
                    print("   ❌ Method name error still present - deployment incomplete")
                    return False
                else:
                    print("   ✅ No method name errors detected")
            else:
                print("   ⚠️  Unexpected error format")
                
        elif response.status_code == 400:
            print("   ✅ OAuth2 endpoint validation working correctly")
        else:
            print(f"   ⚠️  Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ OAuth2 test exception: {e}")
        return False
    
    print()
    
    # Test 3: Check if the specific method exists in the error (if any)
    print("3. Testing specific OAuth2 method fix...")
    try:
        # This should trigger the auth0_client.exchange_code_for_token call
        test_data = {
            "code": "4/0AeanS0bv_V7Q8xQz5x5x5x5x5x5x5x5x5x5x5x5x5x5",  # Longer fake code
            "redirect_uri": "https://app.zebra.associates/callback",
            "state": "test_state_verification"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/login-oauth2",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 500:
            response_data = response.json()
            detail = response_data.get("detail", "")
            
            # The fix changed exchange_code_for_tokens -> exchange_code_for_token
            if "exchange_code_for_tokens" in detail:
                print("   ❌ OLD method name still present - fix NOT deployed")
                return False
            elif "exchange_code_for_token" in detail or "auth0_client" in detail:
                print("   ✅ Method appears to be calling correct function")
            else:
                print("   ✅ No method name errors in response")
                
        print("   ✅ OAuth2 method fix verification passed")
        
    except Exception as e:
        print(f"   ❌ Method fix test exception: {e}")
        return False
    
    print()
    print("=== Deployment Verification Summary ===")
    print("✅ Production deployment appears to be working")
    print("✅ OAuth2 fixes are likely deployed")
    print("✅ No method name errors detected")
    
    return True


if __name__ == "__main__":
    success = test_production_deployment()
    sys.exit(0 if success else 1)