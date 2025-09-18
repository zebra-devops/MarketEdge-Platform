#!/usr/bin/env python3
"""
Matt.Lindop Feature Flags Access Test
Final validation script for Matt.Lindop to test Feature Flags access after analytics_modules fix.

This script provides Matt.Lindop with tools to:
1. Test Feature Flags endpoints with his authentication
2. Verify super_admin role functionality
3. Validate that 500 errors are resolved
4. Confirm Zebra Associates opportunity is unblocked

INSTRUCTIONS FOR MATT.LINDOP:
1. Login to the application to get a valid JWT token
2. Copy the Authorization header from browser dev tools
3. Run this script with your token to validate the fix
"""

import httpx
import json
import sys
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Production API configuration
PRODUCTION_API_URL = "https://marketedge-platform.onrender.com"

def get_matt_lindop_token():
    """Get Matt.Lindop's JWT token from command line or input"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    print("🔐 Matt.Lindop Feature Flags Access Test")
    print("=" * 50)
    print("\nTo get your JWT token:")
    print("1. Login to: https://marketedge-platform.onrender.com")
    print("2. Open browser Developer Tools (F12)")
    print("3. Go to Network tab")
    print("4. Navigate to Feature Flags page")
    print("5. Find any API request and copy the Authorization header value")
    print("6. The token starts with 'Bearer eyJ...'")
    print("\nExample: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    
    token = input("\nPaste your Authorization header value: ").strip()
    
    if not token.startswith('Bearer '):
        print("❌ Token should start with 'Bearer '. Adding it automatically...")
        token = f"Bearer {token}"
    
    return token

async def test_feature_flags_access(token):
    """Test Feature Flags endpoint access"""
    logger.info("🔍 Testing Feature Flags endpoint access...")
    
    headers = {"Authorization": token}
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "user": "matt.lindop@zebra.associates",
        "token_provided": bool(token),
        "endpoints": {},
        "overall_success": False
    }
    
    # Endpoints to test
    endpoints = [
        ("/api/v1/admin/feature-flags", "GET", "List feature flags"),
        ("/api/v1/admin/dashboard/stats", "GET", "Dashboard statistics"),
        ("/api/v1/auth/verify", "GET", "Token verification"),
        ("/api/v1/admin/users", "GET", "User management"),
    ]
    
    success_count = 0
    total_tests = len(endpoints)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint, method, description in endpoints:
            url = f"{PRODUCTION_API_URL}{endpoint}"
            
            try:
                logger.info(f"🔄 Testing {endpoint} - {description}")
                
                response = await client.request(method, url, headers=headers)
                
                # Determine success criteria
                if response.status_code == 200:
                    success = True
                    success_count += 1
                    status_icon = "✅"
                    logger.info(f"✅ SUCCESS: {endpoint} returned 200 OK")
                elif response.status_code == 401:
                    success = False
                    status_icon = "🔐"
                    logger.warning(f"🔐 AUTH REQUIRED: {endpoint} needs valid authentication")
                elif response.status_code == 403:
                    success = False
                    status_icon = "🚫"
                    logger.warning(f"🚫 FORBIDDEN: {endpoint} - insufficient permissions")
                elif response.status_code == 500:
                    success = False
                    status_icon = "❌"
                    logger.error(f"❌ CRITICAL: {endpoint} still returning 500 Internal Server Error!")
                else:
                    success = False
                    status_icon = "⚠️"
                    logger.warning(f"⚠️  UNEXPECTED: {endpoint} returned {response.status_code}")
                
                # Try to parse response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text[:200] if response.text else "No content"
                
                test_results["endpoints"][endpoint] = {
                    "method": method,
                    "description": description,
                    "status_code": response.status_code,
                    "success": success,
                    "response_size": len(response.content),
                    "response_preview": str(response_data)[:200],
                    "has_cors_headers": "access-control-allow-origin" in response.headers
                }
                
                # Special handling for feature flags endpoint
                if endpoint == "/api/v1/admin/feature-flags" and response.status_code == 200:
                    logger.info(f"🎉 FEATURE FLAGS ACCESS SUCCESSFUL!")
                    logger.info(f"📊 Response size: {len(response.content)} bytes")
                    
                    # Check if we got feature flags data
                    try:
                        flags_data = response.json()
                        if isinstance(flags_data, list):
                            logger.info(f"📋 Found {len(flags_data)} feature flags")
                        elif isinstance(flags_data, dict) and 'flags' in flags_data:
                            logger.info(f"📋 Found {len(flags_data['flags'])} feature flags")
                    except:
                        pass
                
            except Exception as e:
                logger.error(f"❌ Failed to test {endpoint}: {str(e)}")
                test_results["endpoints"][endpoint] = {
                    "method": method,
                    "description": description,
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
    
    # Calculate overall success
    test_results["overall_success"] = success_count > 0
    test_results["success_rate"] = f"{success_count}/{total_tests}"
    
    return test_results

def analyze_results(results):
    """Analyze test results and provide recommendations"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS ANALYSIS")
    logger.info("=" * 60)
    
    # Check feature flags specifically
    feature_flags_result = results["endpoints"].get("/api/v1/admin/feature-flags", {})
    feature_flags_status = feature_flags_result.get("status_code")
    
    if feature_flags_status == 200:
        logger.info("🎉 SUCCESS: Feature Flags endpoint is working!")
        logger.info("✅ Matt.Lindop can access Feature Flags")
        logger.info("✅ £925K Zebra Associates opportunity is UNBLOCKED")
        logger.info("✅ Analytics modules table issue is RESOLVED")
        
        business_impact = "CRITICAL_SUCCESS"
        
    elif feature_flags_status == 401:
        logger.warning("🔐 Authentication issue detected")
        logger.warning("🔧 Token may be expired or invalid")
        logger.warning("📋 Try logging in again to get a fresh token")
        
        business_impact = "AUTH_ISSUE"
        
    elif feature_flags_status == 403:
        logger.error("🚫 Permission issue detected")
        logger.error("❌ Matt.Lindop may not have super_admin role")
        logger.error("🔧 Verify super_admin role assignment")
        
        business_impact = "PERMISSION_ISSUE"
        
    elif feature_flags_status == 500:
        logger.error("❌ CRITICAL: Still getting 500 Internal Server Error!")
        logger.error("❌ Analytics modules table issue NOT resolved")
        logger.error("🔧 Database migration may not have been applied")
        
        business_impact = "STILL_BROKEN"
        
    else:
        logger.warning(f"⚠️  Unexpected response: {feature_flags_status}")
        business_impact = "UNEXPECTED"
    
    # Check for any 500 errors
    has_500_errors = any(
        result.get("status_code") == 500 
        for result in results["endpoints"].values()
    )
    
    if has_500_errors:
        logger.error("❌ Some endpoints still returning 500 errors")
        logger.error("🔧 Additional database migration work may be needed")
    else:
        logger.info("✅ No 500 errors detected - database issue appears resolved")
    
    # Summary
    logger.info(f"\n📊 Summary: {results['success_rate']} endpoints successful")
    logger.info(f"🎯 Business Impact: {business_impact}")
    
    if business_impact == "CRITICAL_SUCCESS":
        logger.info("\n🏆 ZEBRA ASSOCIATES OPPORTUNITY STATUS:")
        logger.info("✅ Matt.Lindop Feature Flags access: WORKING")
        logger.info("✅ Admin dashboard functionality: RESTORED")
        logger.info("✅ £925K opportunity: UNBLOCKED")
        logger.info("✅ Technical issue: RESOLVED")
    
    return business_impact

async def main():
    """Main execution function"""
    print("🔐 Matt.Lindop Feature Flags Access Test")
    print("=" * 50)
    print("🎯 Testing £925K Zebra Associates opportunity fix")
    print("🎯 Validating analytics_modules table resolution")
    print("=" * 50)
    
    # Get authentication token
    token = get_matt_lindop_token()
    
    if not token or len(token.split()) < 2:
        print("❌ Invalid token provided. Exiting...")
        return
    
    print(f"\n✅ Token received: {token[:50]}...")
    
    # Run tests
    logger.info("\n🚀 Starting Feature Flags access tests...")
    results = await test_feature_flags_access(token)
    
    # Analyze results
    business_impact = analyze_results(results)
    
    # Save results
    output_file = f"matt_lindop_feature_flags_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: {output_file}")
    
    # Final instructions
    if business_impact == "CRITICAL_SUCCESS":
        print("\n🎉 SUCCESS! You can now proceed with the Zebra Associates demonstration.")
    elif business_impact == "AUTH_ISSUE":
        print("\n🔧 Please login again and retry with a fresh token.")
    elif business_impact == "PERMISSION_ISSUE":
        print("\n🔧 Contact support to verify your super_admin role assignment.")
    else:
        print("\n🔧 Technical issue detected. Contact development team.")

if __name__ == "__main__":
    asyncio.run(main())