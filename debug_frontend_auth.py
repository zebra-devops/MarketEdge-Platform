#!/usr/bin/env python3
"""
Debug Frontend Authentication Issue

This script helps diagnose why the frontend is getting CORS/500 errors
when trying to create experiments in the Causal Edge application.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def debug_auth_flow():
    """Debug the authentication and feature flag issues"""

    print("=== MarketEdge Frontend Authentication Debug ===")
    print(f"Backend URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    async with httpx.AsyncClient() as client:

        # Test 1: Basic connectivity
        print("1. Testing basic connectivity...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   ✅ Health endpoint: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health endpoint failed: {e}")
            return

        # Test 2: CORS configuration
        print("\n2. Testing CORS configuration...")
        try:
            response = await client.options(
                f"{BASE_URL}/api/v1/causal-edge/experiments",
                headers={"Origin": "http://localhost:3000"}
            )
            print(f"   ✅ CORS preflight: {response.status_code}")
            print(f"   Access-Control-Allow-Origin: {response.headers.get('access-control-allow-origin', 'MISSING')}")
        except Exception as e:
            print(f"   ❌ CORS preflight failed: {e}")

        # Test 3: Causal Edge endpoint without auth
        print("\n3. Testing Causal Edge endpoint without auth...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/causal-edge/experiments",
                headers={
                    "Origin": "http://localhost:3000",
                    "Content-Type": "application/json"
                },
                json={
                    "name": "Test Experiment",
                    "experiment_type": "PRICING",
                    "hypothesis": "Testing hypothesis",
                    "success_metrics": ["revenue"]
                }
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            print(f"   CORS headers present: {'access-control-allow-origin' in response.headers}")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        # Test 4: Feature flags endpoint
        print("\n4. Testing feature flags endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/admin/feature-flags")
            print(f"   Status: {response.status_code}")
            if response.status_code == 401:
                print("   Expected: Feature flags require authentication")
            else:
                print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        # Test 5: Check diagnostic info
        print("\n5. Checking diagnostic information...")
        try:
            response = await client.get(f"{BASE_URL}/diagnostic")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API router imported: {data.get('api_router_imported')}")
                print(f"   Routes count: {data.get('routes_count')}")
                print(f"   Database configured: {data.get('database_url_configured')}")
        except Exception as e:
            print(f"   ❌ Diagnostic failed: {e}")

        # Test 6: Authentication requirements analysis
        print("\n6. Authentication Requirements Analysis:")
        print("   📋 Causal Edge endpoint requires:")
        print("      • Valid JWT access token")
        print("      • Application access to 'CAUSAL_EDGE'")
        print("      • Feature flag 'causal_edge_enabled' enabled")
        print("   📋 Frontend authentication status:")
        print("      • Token source: localStorage (dev) or cookies (prod)")
        print("      • Token validation: Auth0 + internal JWT")
        print("      • Current issue: Likely no valid token or missing permissions")

        print("\n=== DIAGNOSIS SUMMARY ===")
        print("❌ ROOT CAUSE: Frontend authentication failure")
        print("   The CORS error is a SYMPTOM of authentication/authorization failure.")
        print("   When backend returns 401/403/500, browser blocks response with CORS error.")
        print()
        print("🔧 SOLUTIONS:")
        print("   1. Ensure user is logged in and has valid token")
        print("   2. Grant user access to CAUSAL_EDGE application")
        print("   3. Enable 'causal_edge_enabled' feature flag")
        print("   4. Check browser DevTools Network tab for actual HTTP status")
        print()
        print("📝 NEXT STEPS:")
        print("   1. Check localStorage/cookies for access_token")
        print("   2. Verify user has CAUSAL_EDGE application access")
        print("   3. Enable causal_edge_enabled feature flag via admin panel")
        print("   4. Test with proper authentication headers")

if __name__ == "__main__":
    asyncio.run(debug_auth_flow())