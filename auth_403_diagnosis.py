#!/usr/bin/env python3
"""
Comprehensive diagnosis of 403 Forbidden errors in MarketEdge production.
This script tests the exact authentication flow to identify where the issue lies.
"""

import requests
import json
import time
from typing import Dict, Any, Optional


class MarketEdgeAuthDiagnosis:
    def __init__(self, base_url: str = "https://marketedge-platform.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_endpoint_without_auth(self, endpoint: str) -> Dict[str, Any]:
        """Test endpoint without any authentication"""
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def test_endpoint_with_invalid_token(self, endpoint: str) -> Dict[str, Any]:
        """Test endpoint with invalid JWT token"""
        try:
            headers = {"Authorization": "Bearer invalid.jwt.token"}
            response = self.session.get(f"{self.base_url}{endpoint}", headers=headers, timeout=10)
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": False
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def test_jwt_debug_endpoint(self) -> Dict[str, Any]:
        """Test JWT debug endpoint to check configuration"""
        try:
            response = self.session.get(f"{self.base_url}/jwt-debug", timeout=10)
            return {
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def test_health_endpoints(self) -> Dict[str, Any]:
        """Test basic health endpoints"""
        results = {}
        
        for endpoint in ["/health", "/cors-debug"]:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
                    "success": response.status_code == 200
                }
            except Exception as e:
                results[endpoint] = {
                    "error": str(e),
                    "success": False
                }
                
        return results
    
    def run_comprehensive_diagnosis(self) -> Dict[str, Any]:
        """Run comprehensive authentication diagnosis"""
        print("🔍 Starting MarketEdge 403 Authentication Diagnosis")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        results = {
            "timestamp": time.time(),
            "base_url": self.base_url,
            "tests": {}
        }
        
        # Test health endpoints first
        print("\n📊 Testing Health Endpoints...")
        results["tests"]["health"] = self.test_health_endpoints()
        for endpoint, result in results["tests"]["health"].items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {endpoint}: {result.get('status_code', 'ERROR')}")
        
        # Test JWT debug endpoint
        print("\n🔐 Testing JWT Debug Endpoint...")
        results["tests"]["jwt_debug"] = self.test_jwt_debug_endpoint()
        jwt_result = results["tests"]["jwt_debug"]
        status = "✅" if jwt_result["success"] else "❌"
        print(f"  {status} /jwt-debug: {jwt_result.get('status_code', 'ERROR')}")
        if jwt_result["success"]:
            jwt_config = jwt_result["response"]
            print(f"    • JWT Secret Set: {jwt_config.get('jwt_secret_key_set', 'Unknown')}")
            print(f"    • JWT Algorithm: {jwt_config.get('jwt_algorithm', 'Unknown')}")
            print(f"    • Environment: {jwt_config.get('environment', 'Unknown')}")
        
        # Test problematic endpoints without authentication
        print("\n🚫 Testing Endpoints WITHOUT Authentication (Expected 403)...")
        problem_endpoints = [
            "/api/v1/organisations/current",
            "/api/v1/organisations/accessible", 
            "/api/v1/organisations/industries",
            "/api/v1/tools/"
        ]
        
        results["tests"]["no_auth"] = {}
        for endpoint in problem_endpoints:
            result = self.test_endpoint_without_auth(endpoint)
            results["tests"]["no_auth"][endpoint] = result
            
            status_code = result.get("status_code")
            detail = result.get("response", {}).get("detail", "No detail") if isinstance(result.get("response"), dict) else "No detail"
            
            if status_code == 403:
                print(f"  ✅ {endpoint}: 403 (Correct - Not authenticated)")
            else:
                print(f"  ❌ {endpoint}: {status_code} (Unexpected)")
            
            print(f"    Detail: {detail}")
        
        # Test with invalid JWT tokens
        print("\n🔓 Testing Endpoints WITH Invalid JWT Token (Expected 401)...")
        results["tests"]["invalid_token"] = {}
        for endpoint in problem_endpoints:
            result = self.test_endpoint_with_invalid_token(endpoint)
            results["tests"]["invalid_token"][endpoint] = result
            
            status_code = result.get("status_code")
            detail = result.get("response", {}).get("detail", "No detail") if isinstance(result.get("response"), dict) else "No detail"
            
            if status_code == 401:
                print(f"  ✅ {endpoint}: 401 (Correct - Could not validate credentials)")
            else:
                print(f"  ❌ {endpoint}: {status_code} (Unexpected)")
            
            print(f"    Detail: {detail}")
        
        return results
    
    def print_diagnosis_summary(self, results: Dict[str, Any]):
        """Print diagnosis summary and recommendations"""
        print("\n" + "=" * 80)
        print("🎯 DIAGNOSIS SUMMARY")
        print("=" * 80)
        
        jwt_debug = results["tests"].get("jwt_debug", {})
        if jwt_debug.get("success"):
            jwt_config = jwt_debug["response"]
            print("✅ JWT Configuration Status:")
            print(f"   • Secret Key Loaded: {jwt_config.get('jwt_secret_key_set', False)}")
            print(f"   • Algorithm: {jwt_config.get('jwt_algorithm', 'Unknown')}")
            print(f"   • Environment: {jwt_config.get('environment', 'Unknown')}")
            print(f"   • Secret Key Length: {jwt_config.get('jwt_secret_key_length', 0)} chars")
        else:
            print("❌ JWT Debug endpoint not accessible")
        
        # Check authentication behavior
        no_auth_403_count = 0
        invalid_token_401_count = 0
        total_endpoints = len(results["tests"].get("no_auth", {}))
        
        for endpoint, result in results["tests"].get("no_auth", {}).items():
            if result.get("status_code") == 403:
                no_auth_403_count += 1
        
        for endpoint, result in results["tests"].get("invalid_token", {}).items():
            if result.get("status_code") == 401:
                invalid_token_401_count += 1
        
        print(f"\n🔍 Authentication Behavior Analysis:")
        print(f"   • No auth → 403 responses: {no_auth_403_count}/{total_endpoints}")
        print(f"   • Invalid token → 401 responses: {invalid_token_401_count}/{total_endpoints}")
        
        if no_auth_403_count == total_endpoints and invalid_token_401_count == total_endpoints:
            print("\n✅ AUTHENTICATION IS WORKING CORRECTLY!")
            print("   The JWT configuration is properly loaded and functioning.")
            print("   403 errors occur when NO token is sent (expected)")
            print("   401 errors occur when INVALID token is sent (expected)")
            print("\n🎯 ROOT CAUSE: Frontend is not sending Authorization headers!")
            print("\n🔧 SOLUTION STEPS:")
            print("   1. Check frontend authentication flow")
            print("   2. Verify JWT tokens are being stored after login")
            print("   3. Ensure Authorization headers are included in API requests")
            print("   4. Check for Auth0 integration issues in frontend")
        else:
            print("\n❌ AUTHENTICATION CONFIGURATION ISSUES DETECTED")
            print("   JWT configuration may not be working correctly")
            print("\n🔧 NEXT STEPS:")
            print("   1. Verify environment variables are set in Render")
            print("   2. Check application logs for JWT errors")
            print("   3. Restart the application after environment changes")


def main():
    """Main diagnosis function"""
    diagnosis = MarketEdgeAuthDiagnosis()
    results = diagnosis.run_comprehensive_diagnosis()
    diagnosis.print_diagnosis_summary(results)
    
    # Save results to file
    with open(f"auth_diagnosis_results_{int(time.time())}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: auth_diagnosis_results_{int(time.time())}.json")


if __name__ == "__main__":
    main()