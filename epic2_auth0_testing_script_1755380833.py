#!/usr/bin/env python3
'''
Epic 2 Auth0 Configuration Testing Script
Validates Auth0 integration with Render backend
'''

import asyncio
import httpx
import json
from urllib.parse import urlparse, parse_qs

async def test_auth0_integration():
    '''Test Auth0 integration with new Render backend'''
    
    backend_url = "https://marketedge-platform.onrender.com"
    frontend_url = "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
    auth0_domain = "dev-g8trhgbfdq2sk2m8.us.auth0.com"
    
    results = {
        "timestamp": "2025-08-16 21:47:13 UTC",
        "tests": [],
        "success": False
    }
    
    print("🔐 Testing Auth0 Integration with Render Backend")
    print(f"Backend: {backend_url}")
    print(f"Frontend: {frontend_url}")
    print(f"Auth0: {auth0_domain}")
    print("-" * 60)
    
    # Test 1: Auth0 URL Generation
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{backend_url}/api/v1/auth/auth0-url",
                params={
                    "redirect_uri": f"{frontend_url}/callback",
                    "state": "test_state_123"
                },
                headers={"Origin": frontend_url}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                auth_url = auth_data.get("auth_url", "")
                
                # Validate Auth0 URL structure
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                validations = {
                    "correct_domain": parsed_url.netloc == auth0_domain,
                    "has_client_id": "client_id" in query_params,
                    "has_redirect_uri": "redirect_uri" in query_params,
                    "has_state": "state" in query_params,
                    "correct_response_type": query_params.get("response_type", [""])[0] == "code"
                }
                
                all_valid = all(validations.values())
                
                results["tests"].append({
                    "name": "Auth0 URL Generation",
                    "status": "PASS" if all_valid else "FAIL",
                    "details": {
                        "auth_url": auth_url,
                        "validations": validations,
                        "has_cors": "access-control-allow-origin" in response.headers
                    }
                })
                
                if all_valid:
                    print("✅ Auth0 URL Generation: PASS")
                else:
                    print("❌ Auth0 URL Generation: FAIL")
                    print(f"   Validations: {validations}")
            else:
                results["tests"].append({
                    "name": "Auth0 URL Generation",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}"
                })
                print(f"❌ Auth0 URL Generation: FAIL (HTTP {response.status_code})")
                
    except Exception as e:
        results["tests"].append({
            "name": "Auth0 URL Generation",
            "status": "FAIL",
            "error": str(e)
        })
        print(f"❌ Auth0 URL Generation: FAIL ({str(e)})")
    
    # Test 2: Auth0 OpenID Configuration
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"https://{auth0_domain}/.well-known/openid_configuration")
            
            if response.status_code == 200:
                config = response.json()
                issuer = config.get("issuer", "")
                
                if issuer == f"https://{auth0_domain}/":
                    results["tests"].append({
                        "name": "Auth0 OpenID Configuration",
                        "status": "PASS",
                        "details": {
                            "issuer": issuer,
                            "authorization_endpoint": config.get("authorization_endpoint"),
                            "token_endpoint": config.get("token_endpoint")
                        }
                    })
                    print("✅ Auth0 OpenID Configuration: PASS")
                else:
                    results["tests"].append({
                        "name": "Auth0 OpenID Configuration",
                        "status": "FAIL",
                        "error": f"Invalid issuer: {issuer}"
                    })
                    print(f"❌ Auth0 OpenID Configuration: FAIL (Invalid issuer)")
            else:
                results["tests"].append({
                    "name": "Auth0 OpenID Configuration",
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}"
                })
                print(f"❌ Auth0 OpenID Configuration: FAIL (HTTP {response.status_code})")
                
    except Exception as e:
        results["tests"].append({
            "name": "Auth0 OpenID Configuration",
            "status": "FAIL",
            "error": str(e)
        })
        print(f"❌ Auth0 OpenID Configuration: FAIL ({str(e)})")
    
    # Test 3: Callback Endpoint CORS
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.options(
                f"{backend_url}/api/v1/auth/callback",
                headers={
                    "Origin": frontend_url,
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            cors_origin = response.headers.get("access-control-allow-origin")
            has_valid_cors = cors_origin and (cors_origin == frontend_url or cors_origin == "*")
            
            if response.status_code in [200, 204] and has_valid_cors:
                results["tests"].append({
                    "name": "Callback Endpoint CORS",
                    "status": "PASS",
                    "details": {
                        "cors_origin": cors_origin,
                        "status_code": response.status_code
                    }
                })
                print("✅ Callback Endpoint CORS: PASS")
            else:
                results["tests"].append({
                    "name": "Callback Endpoint CORS",
                    "status": "FAIL",
                    "details": {
                        "cors_origin": cors_origin,
                        "status_code": response.status_code,
                        "error": "Invalid CORS configuration"
                    }
                })
                print(f"❌ Callback Endpoint CORS: FAIL")
                
    except Exception as e:
        results["tests"].append({
            "name": "Callback Endpoint CORS",
            "status": "FAIL",
            "error": str(e)
        })
        print(f"❌ Callback Endpoint CORS: FAIL ({str(e)})")
    
    # Calculate overall success
    passed_tests = len([t for t in results["tests"] if t["status"] == "PASS"])
    total_tests = len(results["tests"])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    results["success"] = success_rate >= 100  # All tests must pass
    results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": success_rate
    }
    
    print("-" * 60)
    print(f"📊 Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if results["success"]:
        print("🎉 Auth0 Integration: READY FOR PRODUCTION")
    else:
        print("🚨 Auth0 Integration: ISSUES DETECTED")
    
    # Save results
    with open("auth0_integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    asyncio.run(test_auth0_integration())
