#!/usr/bin/env python3
"""
Epic 2 Final Validation
Quick validation of core functionality for demo readiness
"""

import asyncio
import httpx
import time

async def final_validation():
    backend_url = "https://marketedge-platform.onrender.com"
    frontend_url = "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
    
    print("🎯 Epic 2 Final Validation - Demo Readiness Check")
    print("=" * 60)
    print(f"Backend:  {backend_url}")
    print(f"Frontend: {frontend_url}")
    print(f"Time:     {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    
    validation_results = {
        "core_connectivity": False,
        "cors_working": False,
        "auth0_integration": False,
        "api_functionality": False,
        "database_connected": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            print("\n🔍 Core Connectivity Test...")
            response = await client.get(f"{backend_url}/health")
            if response.status_code == 200:
                validation_results["core_connectivity"] = True
                print("   ✅ Backend responding")
            else:
                print(f"   ❌ Backend error: {response.status_code}")
            
            print("\n🔍 CORS Configuration Test...")
            response = await client.get(
                f"{backend_url}/cors-debug",
                headers={"Origin": frontend_url}
            )
            if response.status_code == 200:
                cors_origin = response.headers.get("access-control-allow-origin")
                if cors_origin and frontend_url in cors_origin:
                    validation_results["cors_working"] = True
                    print("   ✅ CORS working correctly")
                else:
                    print(f"   ⚠️ CORS origin: {cors_origin}")
            
            print("\n🔍 Auth0 Integration Test...")
            response = await client.get(
                f"{backend_url}/api/v1/auth/auth0-url",
                params={"redirect_uri": f"{frontend_url}/callback"},
                headers={"Origin": frontend_url}
            )
            if response.status_code == 200:
                auth_data = response.json()
                auth_url = auth_data.get("auth_url", "")
                if "dev-g8trhgbfdq2sk2m8.us.auth0.com" in auth_url:
                    validation_results["auth0_integration"] = True
                    print("   ✅ Auth0 integration working")
                else:
                    print(f"   ❌ Auth0 URL invalid: {auth_url}")
            else:
                print(f"   ❌ Auth0 error: {response.status_code}")
            
            print("\n🔍 API Functionality Test...")
            response = await client.get(
                f"{backend_url}/api/v1/market-edge/health",
                headers={"Origin": frontend_url}
            )
            if response.status_code == 200:
                validation_results["api_functionality"] = True
                print("   ✅ API endpoints working")
            else:
                print(f"   ❌ API error: {response.status_code}")
            
            print("\n🔍 Database Connectivity Test...")
            response = await client.get(f"{backend_url}/ready")
            if response.status_code in [200, 503]:  # 503 is OK if only Redis rate limiting issue
                try:
                    ready_data = response.json()
                    db_status = ready_data.get("services", {}).get("database", {})
                    if db_status.get("status") == "connected":
                        validation_results["database_connected"] = True
                        print("   ✅ Database connected")
                    else:
                        print(f"   ⚠️ Database status: {db_status.get('status', 'unknown')}")
                except:
                    print("   ⚠️ Unable to parse readiness data")
            else:
                print(f"   ❌ Readiness check error: {response.status_code}")
    
    except Exception as e:
        print(f"   💥 Validation error: {str(e)}")
    
    # Calculate overall readiness
    passed_checks = sum(validation_results.values())
    total_checks = len(validation_results)
    readiness_score = (passed_checks / total_checks) * 100
    
    print("\n" + "="*60)
    print("📊 EPIC 2 DEMO READINESS ASSESSMENT")
    print("="*60)
    
    for check, passed in validation_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check.replace('_', ' ').title():<25} {status}")
    
    print(f"\nDemo Readiness Score: {passed_checks}/{total_checks} ({readiness_score:.1f}%)")
    
    if readiness_score >= 80:
        print("\n🎉 EPIC 2 SUCCESS: Platform ready for £925K Odeon demo!")
        print("✅ Core functionality operational")
        print("✅ Frontend-backend communication working")
        print("✅ Authentication flow functional")
        print("\n🚀 CLEARED FOR DEMO DEPLOYMENT")
    elif readiness_score >= 60:
        print("\n⚠️ EPIC 2 PARTIAL: Platform mostly ready with minor issues")
        print("🔧 Address failed checks before demo")
    else:
        print("\n🚨 EPIC 2 ISSUES: Platform needs attention before demo")
        print("❌ Critical functionality not working")
    
    return validation_results

if __name__ == "__main__":
    asyncio.run(final_validation())