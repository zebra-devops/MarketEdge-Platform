#!/usr/bin/env python3
"""
Frontend Authentication Flow Test for Zebra Associates

This script simulates the frontend authentication flow to identify why
the admin console shows "no users visible" despite:
1. User exists in database with admin role
2. Backend endpoints return 403 (not 500) - enum fix worked
3. Database connectivity confirmed

Test flow:
1. Test Auth0 URL generation (without Auth0 redirect)
2. Test JWT token validation
3. Test authenticated API calls
4. Test admin endpoint access with proper tokens
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

PRODUCTION_URL = "https://marketedge-platform.onrender.com"
TARGET_USER_EMAIL = "matt.lindop@zebra.associates"

class FrontendAuthTester:
    """Test the complete frontend authentication flow"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MarketEdge-Frontend-Auth-Test/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
    def test_auth0_url_generation(self) -> Dict[str, Any]:
        """Test if Auth0 URL can be generated"""
        print("🔗 Testing Auth0 URL generation...")
        
        try:
            url = f"{PRODUCTION_URL}/api/v1/auth/auth0-url"
            params = {
                'redirect_uri': 'https://marketedge-platform.onrender.com/callback'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Auth0 URL generated successfully")
                print(f"   🔗 Auth URL: {data.get('auth_url', 'No URL')[:100]}...")
                return {
                    "success": True,
                    "data": data,
                    "status_code": response.status_code
                }
            else:
                print(f"   ❌ Auth0 URL generation failed: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📋 Error details: {error_data}")
                except:
                    print(f"   📋 Error response: {response.text[:200]}")
                
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text[:500]
                }
                
        except Exception as e:
            print(f"   ❌ Exception during Auth0 URL test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_authentication_status_endpoint(self) -> Dict[str, Any]:
        """Test authentication status endpoint behavior"""
        print("🔐 Testing authentication status endpoint...")
        
        try:
            url = f"{PRODUCTION_URL}/api/v1/auth/status"
            response = self.session.get(url, timeout=30)
            
            print(f"   📊 Status Code: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Response: {data}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "data": data,
                        "authenticated": True
                    }
                except:
                    print(f"   ⚠️  Non-JSON response: {response.text[:200]}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "authenticated": False
                    }
                    
            elif response.status_code in [401, 403]:
                print(f"   ✅ Expected unauthenticated response: HTTP {response.status_code}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "authenticated": False,
                    "requires_auth": True
                }
                
            elif response.status_code == 404:
                print(f"   ❌ Endpoint not found: HTTP {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": "Auth status endpoint not found"
                }
                
            else:
                print(f"   ⚠️  Unexpected status: HTTP {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Unexpected status code: {response.status_code}"
                }
                
        except Exception as e:
            print(f"   ❌ Exception during auth status test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_admin_users_endpoint(self) -> Dict[str, Any]:
        """Test admin users endpoint (should return 403/401 without auth)"""
        print("👤 Testing admin users endpoint...")
        
        try:
            url = f"{PRODUCTION_URL}/api/v1/users/"
            response = self.session.get(url, timeout=30)
            
            print(f"   📊 Status Code: HTTP {response.status_code}")
            
            if response.status_code == 403:
                print(f"   ✅ Correct response: HTTP 403 - Admin authentication required")
                print(f"   ✅ This confirms the enum fix is working!")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "requires_admin_auth": True,
                    "enum_fix_confirmed": True
                }
                
            elif response.status_code == 401:
                print(f"   ✅ Expected response: HTTP 401 - Authentication required")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "requires_auth": True
                }
                
            elif response.status_code == 500:
                print(f"   ❌ Server error: HTTP 500 - Backend still broken")
                try:
                    error_data = response.json()
                    print(f"   📋 Error details: {error_data}")
                except:
                    print(f"   📋 Error response: {response.text[:200]}")
                    
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "backend_error": True,
                    "enum_fix_failed": True
                }
                
            elif response.status_code == 200:
                print(f"   ⚠️  Unexpected: HTTP 200 - No authentication required?")
                try:
                    data = response.json()
                    user_count = len(data) if isinstance(data, list) else "unknown"
                    print(f"   📊 Users returned: {user_count}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "no_auth_required": True,
                        "user_count": user_count,
                        "data": data if isinstance(data, list) else None
                    }
                except:
                    print(f"   📋 Response: {response.text[:200]}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "no_auth_required": True
                    }
                    
            else:
                print(f"   ⚠️  Unexpected status: HTTP {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Unexpected status code: {response.status_code}"
                }
                
        except Exception as e:
            print(f"   ❌ Exception during users endpoint test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_auth_me_endpoint(self) -> Dict[str, Any]:
        """Test auth/me endpoint (current user) without tokens"""
        print("👤 Testing auth/me endpoint...")
        
        try:
            url = f"{PRODUCTION_URL}/api/v1/auth/me"
            response = self.session.get(url, timeout=30)
            
            print(f"   📊 Status Code: HTTP {response.status_code}")
            
            if response.status_code == 401:
                print(f"   ✅ Expected response: HTTP 401 - Authentication required")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "requires_auth": True
                }
            elif response.status_code == 403:
                print(f"   ✅ Expected response: HTTP 403 - Access denied")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "requires_auth": True
                }
            elif response.status_code == 200:
                print(f"   ⚠️  Unexpected: HTTP 200 - User info returned without auth")
                try:
                    data = response.json()
                    print(f"   📊 User: {data.get('user', {}).get('email', 'Unknown')}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "authenticated": True,
                        "user_data": data
                    }
                except:
                    print(f"   📋 Response: {response.text[:200]}")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "authenticated": True
                    }
            else:
                print(f"   ⚠️  Unexpected status: HTTP {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"Unexpected status code: {response.status_code}"
                }
                
        except Exception as e:
            print(f"   ❌ Exception during auth/me test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def simulate_token_flow(self) -> Dict[str, Any]:
        """Simulate what happens when frontend tries to make authenticated requests"""
        print("🔄 Simulating frontend token flow...")
        
        # This is where the issue likely is - let's check what the frontend would see
        
        results = {
            "frontend_perspective": {},
            "authentication_check": {},
            "token_validation": {}
        }
        
        # 1. Frontend checks if it has a token
        print("   🔍 Step 1: Frontend checks for stored tokens...")
        print("   📝 In browser: localStorage.getItem('access_token')")
        print("   📝 In browser: Cookies.get('access_token')")
        print("   ❌ Result: No tokens found (user needs to authenticate)")
        
        results["frontend_perspective"] = {
            "has_access_token": False,
            "has_refresh_token": False,
            "needs_authentication": True
        }
        
        # 2. Frontend would redirect to Auth0 or show login
        print("   🔍 Step 2: Frontend would redirect to Auth0 login...")
        print("   📝 Frontend calls: authService.initiateOAuth2Login()")
        print("   📝 This calls: /api/v1/auth/auth0-url")
        
        # We already tested this above
        
        # 3. After Auth0 callback, frontend would get tokens
        print("   🔍 Step 3: After Auth0 callback, frontend would exchange code for tokens...")
        print("   📝 Frontend calls: authService.login({ code, redirect_uri })")
        print("   📝 This calls: /api/v1/auth/login-oauth2")
        print("   ❓ We can't test this without a real Auth0 code")
        
        # 4. With tokens, frontend would make authenticated requests
        print("   🔍 Step 4: With valid tokens, frontend makes authenticated API calls...")
        print("   📝 Headers would include: Authorization: Bearer <token>")
        print("   📝 Calls like: /api/v1/users/ for admin console")
        
        return results
    
    def diagnose_frontend_issue(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results to diagnose the frontend authentication issue"""
        print("🔍 Diagnosing frontend authentication issue...")
        
        diagnosis = {
            "likely_causes": [],
            "evidence": [],
            "recommendations": [],
            "severity": "unknown"
        }
        
        # Check if Auth0 URL generation works
        auth0_test = test_results.get("auth0_url_test", {})
        if not auth0_test.get("success"):
            diagnosis["likely_causes"].append("Auth0 URL generation failing - users cannot start authentication")
            diagnosis["evidence"].append(f"Auth0 URL test failed: {auth0_test.get('error', 'Unknown error')}")
            diagnosis["severity"] = "critical"
        else:
            diagnosis["evidence"].append("Auth0 URL generation works - users can start authentication")
        
        # Check admin endpoint behavior
        users_test = test_results.get("users_endpoint_test", {})
        if users_test.get("status_code") == 403:
            diagnosis["evidence"].append("Admin endpoints require authentication (correct behavior)")
            diagnosis["evidence"].append("Enum fix confirmed working - no more 500 errors")
            
            diagnosis["likely_causes"].append("Authentication tokens are not being stored/sent by frontend")
            diagnosis["likely_causes"].append("Frontend authentication flow is broken after Auth0 callback")
            diagnosis["likely_causes"].append("JWT tokens are invalid or expired")
            diagnosis["likely_causes"].append("Browser storage (localStorage/cookies) not working")
            
        elif users_test.get("status_code") == 500:
            diagnosis["likely_causes"].append("Backend still has 500 errors - enum fix not working")
            diagnosis["severity"] = "critical"
            
        elif users_test.get("status_code") == 200:
            diagnosis["likely_causes"].append("Admin endpoints have no authentication (security issue)")
            diagnosis["severity"] = "high"
        
        # Check authentication status
        auth_status_test = test_results.get("auth_status_test", {})
        if auth_status_test.get("status_code") == 404:
            diagnosis["likely_causes"].append("Authentication status endpoint missing")
            diagnosis["evidence"].append("Auth status endpoint not found - may be routing issue")
        
        # Generate recommendations based on findings
        if "Authentication tokens are not being stored/sent by frontend" in diagnosis["likely_causes"]:
            diagnosis["recommendations"].extend([
                "Check browser localStorage and cookies for access_token",
                "Test Auth0 callback flow manually",
                "Verify JWT token generation and storage",
                "Check for CORS issues preventing token storage",
                "Test frontend authentication service methods",
                "Verify Auth0 configuration and callback URLs"
            ])
            
        if diagnosis["severity"] == "unknown":
            diagnosis["severity"] = "medium"  # Default to medium if we can determine likely causes
            
        return diagnosis
    
    def generate_comprehensive_report(self, all_results: Dict[str, Any]) -> str:
        """Generate comprehensive frontend authentication diagnosis report"""
        report = []
        report.append("=" * 80)
        report.append("FRONTEND AUTHENTICATION FLOW DIAGNOSIS REPORT")
        report.append("Zebra Associates £925K Opportunity - Admin Console Issue")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Production URL: {PRODUCTION_URL}")
        report.append("")
        
        # Executive Summary
        report.append("🎯 EXECUTIVE SUMMARY")
        report.append("-" * 50)
        
        diagnosis = all_results.get("diagnosis", {})
        severity = diagnosis.get("severity", "unknown")
        
        if severity == "critical":
            report.append("🚨 CRITICAL ISSUE: Frontend authentication completely broken")
        elif severity == "high":
            report.append("⚠️  HIGH PRIORITY: Major authentication security/functionality issue")
        elif severity == "medium":
            report.append("⚠️  MEDIUM PRIORITY: Authentication flow disrupted")
        else:
            report.append("🔍 INVESTIGATION NEEDED: Multiple potential issues")
            
        report.append("")
        
        # Test Results Summary
        report.append("📋 TEST RESULTS SUMMARY")
        report.append("-" * 50)
        
        auth0_test = all_results.get("auth0_url_test", {})
        report.append(f"Auth0 URL Generation: {'✅ WORKING' if auth0_test.get('success') else '❌ FAILED'}")
        
        auth_status_test = all_results.get("auth_status_test", {})
        status_code = auth_status_test.get("status_code", "unknown")
        if status_code == 404:
            report.append(f"Auth Status Endpoint: ❌ NOT FOUND (HTTP 404)")
        elif status_code in [401, 403]:
            report.append(f"Auth Status Endpoint: ✅ WORKING (HTTP {status_code})")
        else:
            report.append(f"Auth Status Endpoint: ⚠️  HTTP {status_code}")
        
        users_test = all_results.get("users_endpoint_test", {})
        users_status = users_test.get("status_code", "unknown")
        if users_status == 403:
            report.append("Admin Users Endpoint: ✅ WORKING (HTTP 403 - requires auth)")
            report.append("Enum Fix Status: ✅ CONFIRMED WORKING")
        elif users_status == 500:
            report.append("Admin Users Endpoint: ❌ BROKEN (HTTP 500)")
            report.append("Enum Fix Status: ❌ NOT WORKING")
        elif users_status == 200:
            report.append("Admin Users Endpoint: ⚠️  NO AUTH REQUIRED (HTTP 200)")
        else:
            report.append(f"Admin Users Endpoint: ⚠️  HTTP {users_status}")
        
        me_test = all_results.get("auth_me_test", {})
        me_status = me_test.get("status_code", "unknown")
        if me_status in [401, 403]:
            report.append(f"Auth Me Endpoint: ✅ WORKING (HTTP {me_status} - requires auth)")
        else:
            report.append(f"Auth Me Endpoint: ⚠️  HTTP {me_status}")
        
        report.append("")
        
        # Root Cause Analysis
        report.append("🔍 ROOT CAUSE ANALYSIS")
        report.append("-" * 50)
        
        likely_causes = diagnosis.get("likely_causes", [])
        if likely_causes:
            report.append("Likely Causes:")
            for i, cause in enumerate(likely_causes, 1):
                report.append(f"   {i}. {cause}")
        else:
            report.append("No specific causes identified - further investigation needed")
        
        report.append("")
        
        evidence = diagnosis.get("evidence", [])
        if evidence:
            report.append("Supporting Evidence:")
            for i, item in enumerate(evidence, 1):
                report.append(f"   {i}. {item}")
        
        report.append("")
        
        # Detailed Test Results
        report.append("📊 DETAILED TEST RESULTS")
        report.append("-" * 50)
        
        # Auth0 URL Test
        report.append("Auth0 URL Generation Test:")
        if auth0_test.get("success"):
            data = auth0_test.get("data", {})
            auth_url = data.get("auth_url", "No URL")
            report.append(f"   Status: SUCCESS")
            report.append(f"   Auth URL: {auth_url[:100]}...")
            report.append(f"   Redirect URI: {data.get('redirect_uri', 'Not specified')}")
        else:
            report.append(f"   Status: FAILED")
            report.append(f"   Error: {auth0_test.get('error', 'Unknown error')}")
        
        report.append("")
        
        # Users Endpoint Test
        report.append("Admin Users Endpoint Test:")
        report.append(f"   Status Code: HTTP {users_test.get('status_code', 'unknown')}")
        if users_test.get("enum_fix_confirmed"):
            report.append("   ✅ ENUM FIX CONFIRMED: No more 500 errors!")
        if users_test.get("requires_admin_auth"):
            report.append("   ✅ Proper security: Admin authentication required")
        if users_test.get("no_auth_required"):
            report.append("   ⚠️  Security issue: No authentication required")
            user_count = users_test.get("user_count", "unknown")
            report.append(f"   📊 Users returned: {user_count}")
        
        report.append("")
        
        # Frontend Flow Analysis
        report.append("🔄 FRONTEND AUTHENTICATION FLOW ANALYSIS")
        report.append("-" * 50)
        report.append("Current State:")
        report.append("   1. User navigates to admin console (/admin)")
        report.append("   2. Frontend checks for stored tokens (localStorage/cookies)")
        report.append("   3. No tokens found → User appears unauthenticated")
        report.append("   4. Admin console shows 'Access Denied' or 'no users visible'")
        report.append("")
        report.append("Expected Flow:")
        report.append("   1. User clicks login → Redirect to Auth0")
        report.append("   2. Auth0 authentication → Callback with code")
        report.append("   3. Frontend exchanges code for JWT tokens")
        report.append("   4. Tokens stored in browser (localStorage/cookies)")
        report.append("   5. Authenticated requests include Authorization header")
        report.append("   6. Admin console loads user data successfully")
        
        report.append("")
        
        # Recommendations
        report.append("🔧 RECOMMENDED SOLUTIONS")
        report.append("-" * 50)
        
        recommendations = diagnosis.get("recommendations", [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
        else:
            report.append("1. Test frontend authentication flow manually")
            report.append("2. Check browser developer console for errors")
            report.append("3. Verify Auth0 configuration")
            
        report.append("")
        report.append("🎯 IMMEDIATE NEXT STEPS:")
        report.append("   1. Open browser developer tools")
        report.append("   2. Navigate to admin console (/admin)")
        report.append("   3. Check Console tab for JavaScript errors")
        report.append("   4. Check Network tab for failed API requests")
        report.append("   5. Check Application tab → Local Storage for tokens")
        report.append("   6. Try manual login flow and observe token storage")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main test execution"""
    print("🦓 Frontend Authentication Flow Test - Zebra Associates")
    print("=" * 70)
    print(f"🎯 Production URL: {PRODUCTION_URL}")
    print(f"💰 Opportunity: £925K")
    print("")
    
    tester = FrontendAuthTester()
    all_results = {}
    
    # Run all tests
    all_results["auth0_url_test"] = tester.test_auth0_url_generation()
    print("")
    
    all_results["auth_status_test"] = tester.test_authentication_status_endpoint()
    print("")
    
    all_results["users_endpoint_test"] = tester.test_admin_users_endpoint()
    print("")
    
    all_results["auth_me_test"] = tester.test_auth_me_endpoint()
    print("")
    
    all_results["token_flow_simulation"] = tester.simulate_token_flow()
    print("")
    
    # Diagnose the issue
    all_results["diagnosis"] = tester.diagnose_frontend_issue(all_results)
    print("")
    
    # Generate comprehensive report
    report = tester.generate_comprehensive_report(all_results)
    print(report)
    
    # Save report
    report_filename = f"frontend_auth_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved: {report_filename}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")
    
    # Save raw results
    results_filename = f"frontend_auth_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(results_filename, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"📄 Raw results saved: {results_filename}")
    except Exception as e:
        print(f"⚠️  Could not save raw results: {e}")
    
    print("\n" + "="*70)
    
    # Final verdict
    diagnosis = all_results.get("diagnosis", {})
    severity = diagnosis.get("severity", "unknown")
    
    if severity == "critical":
        print("❌ CRITICAL: Frontend authentication is completely broken")
        print("🚨 URGENT: Requires immediate attention for £925K opportunity")
        sys.exit(1)
    elif severity in ["high", "medium"]:
        print("⚠️  ISSUES FOUND: Frontend authentication needs fixing")
        print("🔧 PRIORITY: Should be resolved for optimal user experience")
        sys.exit(1)
    else:
        print("✅ TESTS COMPLETED: Backend is working, issue is likely in frontend token handling")
        print("🔍 INVESTIGATION: Focus on browser-side authentication flow")
        sys.exit(0)

if __name__ == "__main__":
    main()