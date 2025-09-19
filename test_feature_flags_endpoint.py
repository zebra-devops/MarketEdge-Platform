#!/usr/bin/env python3
"""
Test Feature Flags endpoint with Matt.Lindop's Auth0 token
"""

import aiohttp
import asyncio
import json

async def test_feature_flags_endpoint():
    """Test Feature Flags endpoint directly"""

    print("=== TESTING FEATURE FLAGS ENDPOINT ===")
    print()

    # Production backend URL
    base_url = "https://marketedge-platform.onrender.com"

    # Feature Flags endpoint
    endpoint = f"{base_url}/api/v1/admin/feature-flags"

    print(f"Testing endpoint: {endpoint}")
    print()

    # Test without auth first
    print("1. TESTING WITHOUT AUTHENTICATION:")
    print("-" * 50)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(endpoint) as response:
                status = response.status
                text = await response.text()

                print(f"Status: {status}")
                print(f"Response: {text[:200]}...")

                if status == 401:
                    print("✅ Expected: 401 Unauthorized without auth token")
                else:
                    print(f"❓ Unexpected status: {status}")

        except Exception as e:
            print(f"❌ Request failed: {e}")

    print()
    print("2. CHECKING HEALTH ENDPOINT:")
    print("-" * 50)

    health_endpoint = f"{base_url}/health"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(health_endpoint) as response:
                status = response.status
                text = await response.text()

                print(f"Health endpoint status: {status}")
                print(f"Health response: {text}")

                if status == 200:
                    print("✅ Backend is healthy")
                else:
                    print("❌ Backend health check failed")

        except Exception as e:
            print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_feature_flags_endpoint())
