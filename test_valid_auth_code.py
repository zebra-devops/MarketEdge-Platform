#!/usr/bin/env python3
"""
Test script to reproduce the 500 error using a valid Auth0 authorization code.

This addresses the user's critical point: we need to test with REAL Auth0 codes,
not fake ones that only test the 400 error path.

Usage:
1. Manually get a valid Auth0 code from browser network tab during failed login
2. Run: python test_valid_auth_code.py <auth_code>
3. This will reproduce the exact 500 error the frontend experiences
"""

import asyncio
import httpx
import sys
import json
import os
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:8000"
AUTH_ENDPOINT = f"{BACKEND_URL}/api/v1/auth/login"
REDIRECT_URI = "http://localhost:3000/callback"

async def test_valid_auth_code(auth_code: str):
    """Test with a valid Auth0 authorization code to reproduce the 500 error"""
    
    print(f"🔍 Testing Valid Auth0 Code: {auth_code[:20]}...")
    print(f"⏰ Test started at: {datetime.now().isoformat()}")
    print(f"🎯 Target endpoint: {AUTH_ENDPOINT}")
    print("-" * 60)
    
    # Prepare the request data (same as frontend)
    auth_data = {
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "state": "test_state"  # Optional
    }
    
    print("📝 Request data:")
    print(f"   Code: {auth_code[:20]}... (truncated)")
    print(f"   Redirect URI: {REDIRECT_URI}")
    print(f"   State: test_state")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("🚀 Sending POST request to backend...")
            
            # Make the same request the frontend makes
            response = await client.post(
                AUTH_ENDPOINT,
                json=auth_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "ValidCodeTester/1.0"
                }
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            print()
            
            if response.status_code == 500:
                print("💥 REPRODUCED: 500 Internal Server Error!")
                print("🎯 This confirms the user's assessment is correct.")
                print("🔍 The backend crashes with valid codes, not invalid ones.")
                print()
                print("📄 Response body:")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text[:1000])  # Truncate long responses
                    
            elif response.status_code == 200:
                print("✅ SUCCESS: Authentication worked!")
                print("📄 Response body:")
                try:
                    success_data = response.json()
                    # Mask sensitive data for logging
                    if "access_token" in success_data:
                        success_data["access_token"] = success_data["access_token"][:20] + "..."
                    if "refresh_token" in success_data:
                        success_data["refresh_token"] = success_data["refresh_token"][:20] + "..."
                    print(json.dumps(success_data, indent=2))
                except:
                    print(response.text[:1000])
                    
            elif response.status_code == 400:
                print("⚠️  400 Error: This means the Auth0 code was invalid/expired")
                print("🔄 You may need a fresher code from the browser network tab")
                print("📄 Response body:")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except:
                    print(response.text[:500])
                    
            else:
                print(f"❓ Unexpected response: {response.status_code}")
                print("📄 Response body:")
                print(response.text[:1000])
                
        except httpx.TimeoutException:
            print("⏰ Request timed out - backend might be crashed/hanging")
            print("🔍 This could indicate the 500 error is a hang/crash")
            
        except httpx.ConnectError:
            print("🚫 Connection failed - is the backend running on port 8000?")
            print("💡 Start backend with: cd backend && python -m uvicorn app.main:app --reload")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            print(f"🔍 Error type: {type(e).__name__}")

def print_instructions():
    """Print instructions for getting a valid Auth0 code"""
    print("📚 HOW TO GET A VALID AUTH0 CODE:")
    print()
    print("1. 🌐 Open browser and go to your frontend app")
    print("2. 🔧 Open Developer Tools (F12)")
    print("3. 📡 Go to Network tab")
    print("4. 🔑 Try to log in (it will fail with 500)")
    print("5. 🕵️  Look for the POST request to /api/v1/auth/login")
    print("6. 👀 In the request payload, copy the 'code' value")
    print("7. ⚡ Run this script immediately (codes expire in ~10 minutes)")
    print()
    print("Example:")
    print(f"   python {sys.argv[0]} <paste_auth0_code_here>")
    print()

def main():
    if len(sys.argv) != 2:
        print("❌ Missing Auth0 authorization code")
        print()
        print_instructions()
        sys.exit(1)
        
    auth_code = sys.argv[1].strip()
    
    if not auth_code or len(auth_code) < 10:
        print("❌ Invalid Auth0 code format")
        print("💡 Auth0 codes are typically 50+ characters long")
        print()
        print_instructions()
        sys.exit(1)
    
    print("🧪 VALID AUTH0 CODE TEST")
    print("=" * 60)
    print("🎯 Purpose: Reproduce the 500 error with a real Auth0 code")
    print("🔍 This tests the SUCCESS path where token exchange works")
    print("   but something else crashes, causing the 500 error.")
    print()
    
    # Run the test
    asyncio.run(test_valid_auth_code(auth_code))
    
    print()
    print("=" * 60)
    print("📋 NEXT STEPS:")
    print("1. 🔍 Check backend server logs for detailed stack trace")
    print("2. 🐛 Look for the exact line where the crash occurs")
    print("3. 🔧 Fix the root cause (likely database/JWT/user creation)")
    print("4. 🧪 Retest with the same valid code")

if __name__ == "__main__":
    main()