#!/usr/bin/env python3
"""
Real Authentication Error Capture

This script helps capture the actual error occurring during real Auth0 authentication
by enhancing our error logging and testing with real authorization code formats.
"""

import requests
import json
import time

def test_with_real_auth_format():
    """Test with realistic Auth0 authorization code format"""
    print("🔍 Testing with Real Auth0 Authorization Code Format")
    print("=" * 60)
    
    # Real Auth0 codes are typically longer and have specific patterns
    realistic_codes = [
        # Typical Auth0 code format (longer, alphanumeric with special chars)
        "4/0AdQt8qh9kF7X8mYzJ3RqF8pA_jR2cN5fB3vD7wE1mL9qS6tA8hK2nX4rY7gU0bC5zV3-9P8fN2mW6xJ1qL4kH",
        # Another realistic format
        "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2NzAyNDM5MjMifQ.eyJpc3MiOiJodHRwczovL2Rldi1nOHRyaGdiZmRxMnNrMm04LnVzLmF1dGgwLmNvbS8iLCJhdWQiOiJtUUcwMVo0bE5oVFRONDEifQ",
        # Shorter but still realistic
        "gAAAAABhdDxKzP_8Qh9mN6fR2cL5vB3wX7jY1kT4sE9qA2hU0nP6gF8dK5xJ3mZ7rC4oV1iS"
    ]
    
    for i, code in enumerate(realistic_codes, 1):
        print(f"\n--- Test {i}: Real Format Code ({len(code)} chars) ---")
        
        try:
            response = requests.post(
                "https://marketedge-platform.onrender.com/api/v1/auth/login",
                json={
                    "code": code,
                    "redirect_uri": "https://app.zebra.associates/callback"
                },
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://app.zebra.associates",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Referer": "https://app.zebra.associates/",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "cross-site"
                },
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 500:
                print("🚨 FOUND THE 500 ERROR!")
                print(f"Headers: {dict(response.headers)}")
                try:
                    error_data = response.json()
                    if error_data.get('detail') == 'Internal server error':
                        print("This matches the user's error!")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        time.sleep(1)  # Be nice to the server

def test_edge_cases():
    """Test edge cases that might trigger 500 errors"""
    print("\n\n🔍 Testing Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        # Very long code
        {"name": "Very Long Code", "code": "a" * 1000},
        # Special characters
        {"name": "Special Characters", "code": "code_with_special_chars!@#$%^&*()+=[]{}|;:,.<>?"},
        # Empty strings
        {"name": "Empty Code", "code": ""},
        # None values (this will fail JSON encoding but let's see)
        {"name": "Null-like", "code": "null"},
        # Unicode characters
        {"name": "Unicode", "code": "code_with_üñíçødé_chars_测试"},
        # SQL injection attempt (should be handled safely)
        {"name": "SQL Injection", "code": "'; DROP TABLE users; --"},
        # XSS attempt
        {"name": "XSS Attempt", "code": "<script>alert('xss')</script>"},
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        
        try:
            response = requests.post(
                "https://marketedge-platform.onrender.com/api/v1/auth/login",
                json={
                    "code": case['code'],
                    "redirect_uri": "https://app.zebra.associates/callback"
                },
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://app.zebra.associates"
                },
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 500:
                print("🚨 FOUND A 500 ERROR!")
                print(f"Response: {response.text}")
            else:
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def main():
    print("🔍 Real Authentication Error Capture")
    print("Investigating the production 500 errors...")
    
    test_with_real_auth_format()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("🎯 INVESTIGATION COMPLETE")
    print("\nIf any test shows 500 'Internal server error', that reveals the trigger.")
    print("Next step: Fix the specific code path that's failing.")

if __name__ == "__main__":
    main()