#!/usr/bin/env python3
"""
Debug Frontend Feature Flag API Call Issue

Since CORS and backend are working correctly, the issue must be in how
the frontend is making the API call to /admin/feature-flags.

This script simulates the frontend API call exactly.
"""

import requests
import json
from datetime import datetime

def simulate_frontend_api_call():
    """Simulate exactly how frontend makes the API call"""

    base_url = "https://marketedge-platform.onrender.com/api/v1"

    # Simulate different scenarios of how frontend might be calling the API
    scenarios = [
        {
            "name": "Direct apiService.get() call",
            "url": f"{base_url}/admin/feature-flags",
            "method": "GET",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-token",  # This would be from token retrieval
                "Origin": "https://app.zebra.associates"
            }
        },
        {
            "name": "AdminFeatureFlagService.getFeatureFlags()",
            "url": f"{base_url}/admin/feature-flags",
            "method": "GET",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-token",
                "Origin": "https://app.zebra.associates"
            }
        },
        {
            "name": "FeatureFlagManager fetch call",
            "url": f"{base_url}/admin/feature-flags",
            "method": "GET",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer dummy-token",
                "Origin": "https://app.zebra.associates"
            }
        },
        {
            "name": "Call without Authorization (like frontend issue)",
            "url": f"{base_url}/admin/feature-flags",
            "method": "GET",
            "headers": {
                "Content-Type": "application/json",
                "Origin": "https://app.zebra.associates"
                # No Authorization header
            }
        }
    ]

    print("🔍 FRONTEND API CALL SIMULATION")
    print("=" * 50)
    print(f"Time: {datetime.now().isoformat()}")
    print()

    for scenario in scenarios:
        print(f"📍 Scenario: {scenario['name']}")
        print(f"   URL: {scenario['url']}")
        print(f"   Headers: {list(scenario['headers'].keys())}")

        try:
            response = requests.request(
                scenario['method'],
                scenario['url'],
                headers=scenario['headers'],
                timeout=10
            )

            print(f"   Status: {response.status_code}")

            response_text = response.text
            if "No credentials provided" in response_text:
                print("   ❌ Backend: 'No credentials provided' - Matches frontend issue!")
            elif "Could not validate credentials" in response_text:
                print("   ✅ Backend: Header received, token validation attempted")
            elif response.status_code == 200:
                print("   ✅ Success response")
            else:
                print(f"   ❓ Response: {response_text[:100]}...")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        print()

    print("🎯 ANALYSIS")
    print("=" * 20)
    print("If scenario 4 matches the frontend behavior (No credentials provided),")
    print("then the issue is in frontend token retrieval/inclusion for this endpoint.")
    print()
    print("The frontend is making requests WITHOUT Authorization headers.")
    print("This suggests:")
    print("1. Token retrieval is failing in the frontend")
    print("2. API service interceptor is not adding Authorization header")
    print("3. Environment/context issue preventing token access")

if __name__ == "__main__":
    simulate_frontend_api_call()