#!/usr/bin/env python3
"""
Test script to validate the health endpoint works correctly.
This can be run locally or in Railway environment.
"""

import asyncio
import aiohttp
import os
import sys
import time
from typing import Dict, Any

async def test_health_endpoint(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Test the /health endpoint functionality."""
    results = {
        "success": False,
        "status_code": None,
        "response_data": None,
        "response_time_ms": None,
        "error": None
    }
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{base_url}/health") as response:
                results["status_code"] = response.status
                results["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
                
                if response.status == 200:
                    data = await response.json()
                    results["response_data"] = data
                    
                    # Check required fields
                    required_fields = ["status", "version", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        results["error"] = f"Missing required fields: {missing_fields}"
                    elif data.get("status") == "healthy":
                        results["success"] = True
                    else:
                        results["error"] = f"Health status is not 'healthy': {data.get('status')}"
                else:
                    results["error"] = f"HTTP {response.status}"
                    try:
                        error_data = await response.text()
                        results["response_data"] = error_data
                    except:
                        pass
                        
    except asyncio.TimeoutError:
        results["error"] = "Request timeout (>10s)"
        results["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    except Exception as e:
        results["error"] = str(e)
        results["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    return results

async def main():
    """Run health endpoint tests."""
    print("Testing Health Endpoint")
    print("=" * 50)
    
    # Test with different URLs
    test_urls = [
        "http://localhost:8000",
        f"http://localhost:{os.getenv('PORT', '8000')}",
    ]
    
    # Add Railway URL if available
    railway_url = os.getenv('RAILWAY_STATIC_URL')
    if railway_url:
        test_urls.append(f"https://{railway_url}")
    
    all_passed = True
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        print("-" * 30)
        
        result = await test_health_endpoint(url)
        
        if result["success"]:
            print(f"✅ SUCCESS - {result['response_time_ms']}ms")
            print(f"   Status: {result['response_data']['status']}")
            print(f"   Version: {result['response_data']['version']}")
        else:
            print(f"❌ FAILED - {result['error']}")
            print(f"   Status Code: {result['status_code']}")
            print(f"   Response Time: {result['response_time_ms']}ms")
            if result["response_data"]:
                print(f"   Response: {result['response_data']}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())