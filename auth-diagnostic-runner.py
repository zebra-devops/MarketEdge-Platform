#!/usr/bin/env python3
"""
MarketEdge Authentication Diagnostic Runner

This script runs comprehensive diagnostics on the MarketEdge authentication system
to identify the root cause of persistent 500 "Database error occurred" messages.

Usage:
    python auth-diagnostic-runner.py

Features:
- Direct backend API testing
- Database operation validation  
- Enum constraint verification
- Network monitoring simulation
- Actionable recommendation generation
"""

import asyncio
import aiohttp
import json
import sys
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64
import uuid

# Configuration
BACKEND_URL = "https://marketedge-platform.onrender.com"
FRONTEND_URL = "https://frontend-cdir2vud8-zebraassociates-projects.vercel.app"
TIMEOUT = 30  # seconds

# Test data
MOCK_AUTH0_CODES = [
    {
        "name": "Standard Test Code",
        "code": "test_diagnostic_standard",
        "expected_status": 400
    },
    {
        "name": "Realistic Auth0 Code",
        "code": "AUTH0_" + base64.b64encode(f"test_{int(time.time())}".encode()).decode()[:32],
        "expected_status": 400
    },
    {
        "name": "JWT-like Code",
        "code": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjAwMDAwMDAwfQ.test",
        "expected_status": 400
    }
]

ENUM_TEST_COMBINATIONS = [
    {"industry_type": "default", "subscription_plan": "basic", "description": "Lowercase (likely correct)"},
    {"industry_type": "DEFAULT", "subscription_plan": "BASIC", "description": "Uppercase (might cause issues)"},
    {"industry_type": "Default", "subscription_plan": "Basic", "description": "Title case (might cause issues)"},
    {"industry_type": "technology", "subscription_plan": "professional", "description": "Alternative values"},
]

class AuthDiagnosticRunner:
    def __init__(self):
        self.session = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "frontend_url": FRONTEND_URL,
            "tests": [],
            "recommendations": [],
            "summary": {}
        }
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "CRITICAL": "🚨"
        }.get(level, "")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    async def test_backend_health(self) -> Dict[str, Any]:
        """Test backend health endpoint"""
        self.log("Testing backend health endpoint...")
        
        test_result = {
            "name": "Backend Health Check",
            "url": f"{BACKEND_URL}/health",
            "method": "GET"
        }
        
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                status = response.status
                text = await response.text()
                
                test_result.update({
                    "status": status,
                    "response_body": text,
                    "success": status == 200
                })
                
                if status == 200:
                    self.log("Backend health check passed", "SUCCESS")
                    try:
                        health_data = json.loads(text)
                        if "database" in health_data:
                            self.log(f"Database status: {health_data['database']}")
                    except json.JSONDecodeError:
                        pass
                else:
                    self.log(f"Backend health check failed: {status} {text}", "ERROR")
                    
        except Exception as e:
            self.log(f"Backend health check error: {e}", "ERROR")
            test_result.update({
                "status": "error",
                "error": str(e),
                "success": False
            })
        
        return test_result
    
    async def test_auth_endpoint_codes(self) -> List[Dict[str, Any]]:
        """Test auth endpoint with various code formats"""
        self.log("Testing authentication endpoint with various code formats...")
        
        test_results = []
        
        for i, code_test in enumerate(MOCK_AUTH0_CODES):
            self.log(f"  {i+1}. Testing {code_test['name']}...")
            
            test_result = {
                "name": f"Auth Endpoint - {code_test['name']}",
                "url": f"{BACKEND_URL}/api/v1/auth/login",
                "method": "POST",
                "code": code_test["code"][:50] + "..." if len(code_test["code"]) > 50 else code_test["code"]
            }
            
            payload = {
                "code": code_test["code"],
                "redirect_uri": "https://marketedge-platform.onrender.com/callback",
                "state": f"test_state_{int(time.time())}"
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/api/v1/auth/login",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    status = response.status
                    text = await response.text()
                    
                    test_result.update({
                        "status": status,
                        "response_body": text,
                        "expected_status": code_test["expected_status"],
                        "success": status == code_test["expected_status"]
                    })
                    
                    if status == 500:
                        self.log(f"    🚨 500 ERROR DETECTED", "CRITICAL")
                        
                        if "Database error occurred" in text:
                            self.log(f"    🚨 DATABASE ERROR CONFIRMED", "CRITICAL")
                            test_result["database_error"] = True
                        
                        if "enum" in text.lower():
                            self.log(f"    🚨 ENUM CONSTRAINT VIOLATION", "CRITICAL")
                            test_result["enum_error"] = True
                        
                        if "organisation" in text.lower():
                            self.log(f"    🚨 ORGANIZATION CREATION ERROR", "CRITICAL") 
                            test_result["org_creation_error"] = True
                        
                        self.log(f"    Error details: {text[:200]}...", "ERROR")
                        
                    elif status == 400:
                        self.log(f"    ✅ Expected 400 for test code", "SUCCESS")
                        
                    else:
                        self.log(f"    ℹ️  Unexpected status: {status}", "WARNING")
                
            except Exception as e:
                self.log(f"    ❌ Request failed: {e}", "ERROR")
                test_result.update({
                    "status": "error",
                    "error": str(e),
                    "success": False
                })
            
            test_results.append(test_result)
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        return test_results
    
    async def test_database_constraints(self) -> List[Dict[str, Any]]:
        """Test database constraint validation"""
        self.log("Testing database constraint validation...")
        
        test_results = []
        
        for i, enum_combo in enumerate(ENUM_TEST_COMBINATIONS):
            self.log(f"  {i+1}. Testing {enum_combo['description']}...")
            
            test_result = {
                "name": f"Database Constraints - {enum_combo['description']}",
                "url": f"{BACKEND_URL}/api/v1/organisations",
                "method": "POST",
                "enum_values": enum_combo
            }
            
            payload = {
                "name": f"Test Org Constraint {i+1}",
                "industry": "Technology",
                "industry_type": enum_combo["industry_type"],
                "subscription_plan": enum_combo["subscription_plan"]
            }
            
            try:
                async with self.session.post(
                    f"{BACKEND_URL}/api/v1/organisations",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    status = response.status
                    text = await response.text()
                    
                    test_result.update({
                        "status": status,
                        "response_body": text
                    })
                    
                    if status == 500:
                        self.log(f"    🚨 500 ERROR - Constraint violation", "CRITICAL")
                        
                        if "enum" in text.lower():
                            self.log(f"    🎯 ENUM CONSTRAINT VIOLATION CONFIRMED", "CRITICAL")
                            test_result["enum_constraint_violation"] = True
                            
                            if enum_combo["industry_type"] in text:
                                self.log(f"    🎯 INVALID industry_type: {enum_combo['industry_type']}", "CRITICAL")
                                test_result["invalid_industry_type"] = True
                            
                            if enum_combo["subscription_plan"] in text:
                                self.log(f"    🎯 INVALID subscription_plan: {enum_combo['subscription_plan']}", "CRITICAL")
                                test_result["invalid_subscription_plan"] = True
                    
                    elif status == 201:
                        self.log(f"    ✅ SUCCESS - Enum values accepted", "SUCCESS")
                        test_result["success"] = True
                        
                    else:
                        self.log(f"    ℹ️  Status {status}: {text[:100]}...", "INFO")
                
            except Exception as e:
                self.log(f"    ❌ Request failed: {e}", "ERROR")
                test_result.update({
                    "status": "error",
                    "error": str(e)
                })
            
            test_results.append(test_result)
            await asyncio.sleep(1)
        
        return test_results
    
    async def test_specific_auth_flow_operations(self) -> List[Dict[str, Any]]:
        """Test operations that occur during the auth flow"""
        self.log("Testing specific auth flow operations...")
        
        test_results = []
        
        # Test Auth0 URL generation
        self.log("  1. Testing Auth0 URL generation...")
        test_result = {
            "name": "Auth0 URL Generation",
            "url": f"{BACKEND_URL}/api/v1/auth/auth0-url",
            "method": "GET"
        }
        
        try:
            params = {"redirect_uri": "https://marketedge-platform.onrender.com/callback"}
            async with self.session.get(f"{BACKEND_URL}/api/v1/auth/auth0-url", params=params) as response:
                status = response.status
                text = await response.text()
                
                test_result.update({
                    "status": status,
                    "response_body": text,
                    "success": status == 200
                })
                
                if status == 200:
                    self.log("    ✅ Auth0 URL generation successful", "SUCCESS")
                else:
                    self.log(f"    ❌ Auth0 URL generation failed: {status}", "ERROR")
                    
        except Exception as e:
            self.log(f"    ❌ Auth0 URL test failed: {e}", "ERROR")
            test_result["error"] = str(e)
        
        test_results.append(test_result)
        
        return test_results
    
    def analyze_results(self):
        """Analyze test results and generate recommendations"""
        self.log("Analyzing test results and generating recommendations...")
        
        # Count different types of failures
        auth_500_errors = 0
        database_errors = 0
        enum_errors = 0
        org_creation_errors = 0
        working_validations = 0
        
        for test in self.results["tests"]:
            if isinstance(test, list):
                # Handle nested test results
                for subtest in test:
                    self._analyze_single_test(subtest)
            else:
                self._analyze_single_test(test)
        
        # Generate specific recommendations
        recommendations = []
        
        # Check for database enum constraint issues
        enum_constraint_tests = [t for t in self.results["tests"] if isinstance(t, list)]
        if enum_constraint_tests:
            for test_group in enum_constraint_tests:
                for test in test_group:
                    if test.get("enum_constraint_violation"):
                        recommendations.append({
                            "priority": "CRITICAL",
                            "area": "Database Constraints",
                            "issue": "Enum constraint violation confirmed",
                            "evidence": f"Status {test.get('status')} in {test.get('name')}",
                            "action_items": [
                                "Fix enum values in database schema or application code",
                                "Check Industry and SubscriptionPlan enum definitions",
                                "Verify case sensitivity of enum values",
                                "Update default organization creation logic"
                            ]
                        })
                        break
        
        # Check for auth endpoint database errors
        auth_tests = [t for t in self.results["tests"] if isinstance(t, list) and any("Auth Endpoint" in str(subtest.get("name", "")) for subtest in t)]
        if auth_tests:
            for test_group in auth_tests:
                for test in test_group:
                    if test.get("database_error"):
                        recommendations.append({
                            "priority": "CRITICAL",
                            "area": "Authentication Flow",
                            "issue": "Database error in authentication endpoint",
                            "evidence": f"500 error with 'Database error occurred' message",
                            "action_items": [
                                "Fix database operations in auth/login endpoint",
                                "Check user/organization creation logic",
                                "Verify database connection and constraints",
                                "Review enum value usage in authentication flow"
                            ]
                        })
                        break
        
        # Check backend health
        health_tests = [t for t in self.results["tests"] if isinstance(t, dict) and "Health Check" in t.get("name", "")]
        if health_tests and health_tests[0].get("success"):
            recommendations.append({
                "priority": "INFO",
                "area": "Infrastructure",
                "issue": "Backend and database connectivity working",
                "evidence": "Health check passed",
                "action_items": [
                    "Focus on application logic rather than infrastructure",
                    "Issue is in specific database operations, not connectivity"
                ]
            })
        
        # Generate summary
        summary = {
            "total_tests": len(self.results["tests"]),
            "critical_issues_found": len([r for r in recommendations if r["priority"] == "CRITICAL"]),
            "backend_healthy": any(t.get("success") for t in self.results["tests"] if isinstance(t, dict) and "Health" in t.get("name", "")),
            "database_errors_confirmed": any(self._has_database_error(t) for t in self.results["tests"]),
            "enum_constraint_issues": any(self._has_enum_error(t) for t in self.results["tests"])
        }
        
        self.results["recommendations"] = recommendations
        self.results["summary"] = summary
        
        return recommendations, summary
    
    def _analyze_single_test(self, test):
        """Analyze a single test result"""
        pass  # Analysis is done in analyze_results
    
    def _has_database_error(self, test_result):
        """Check if test result indicates database error"""
        if isinstance(test_result, list):
            return any(t.get("database_error") for t in test_result)
        return test_result.get("database_error", False)
    
    def _has_enum_error(self, test_result):
        """Check if test result indicates enum error"""
        if isinstance(test_result, list):
            return any(t.get("enum_constraint_violation") for t in test_result)
        return test_result.get("enum_constraint_violation", False)
    
    def print_recommendations(self, recommendations: List[Dict], summary: Dict):
        """Print actionable recommendations"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE AUTHENTICATION DIAGNOSTIC REPORT")
        print("=" * 80)
        
        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"   Backend Health: {'✅ Healthy' if summary['backend_healthy'] else '❌ Issues'}")
        print(f"   Database Errors: {'🚨 Confirmed' if summary['database_errors_confirmed'] else '✅ None detected'}")
        print(f"   Enum Constraint Issues: {'🚨 Confirmed' if summary['enum_constraint_issues'] else '✅ None detected'}")
        print(f"   Critical Issues: {summary['critical_issues_found']}")
        
        if not recommendations:
            print("\n✅ No specific issues identified - system appears healthy")
            return
        
        # Print recommendations by priority
        critical_recs = [r for r in recommendations if r["priority"] == "CRITICAL"]
        info_recs = [r for r in recommendations if r["priority"] == "INFO"]
        
        if critical_recs:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_recs)} found):")
            for i, rec in enumerate(critical_recs):
                print(f"\n   {i+1}. [{rec['area']}] {rec['issue']}")
                print(f"      Evidence: {rec['evidence']}")
                print(f"      Action Items:")
                for action in rec["action_items"]:
                    print(f"        • {action}")
        
        if info_recs:
            print(f"\n💡 INFORMATION ({len(info_recs)} items):")
            for i, rec in enumerate(info_recs):
                print(f"\n   {i+1}. [{rec['area']}] {rec['issue']}")
                print(f"      Evidence: {rec['evidence']}")
        
        # Primary recommendation
        print(f"\n🎯 PRIMARY RECOMMENDATION:")
        if summary['database_errors_confirmed'] and summary['enum_constraint_issues']:
            print("   Fix database enum constraint violations in the authentication flow")
            print("   This will resolve the 500 'Database error occurred' messages")
        elif summary['database_errors_confirmed']:
            print("   Investigate database operations in the authentication endpoint")
            print("   Check user/organization creation logic for constraint violations")
        else:
            print("   System appears to be working correctly")
            print("   Authentication would likely succeed with real Auth0 tokens")
    
    def save_report(self):
        """Save detailed report to file"""
        report_filename = f"auth_diagnostic_report_{int(time.time())}.json"
        
        try:
            with open(report_filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            self.log(f"Detailed report saved to: {report_filename}")
            return report_filename
        except Exception as e:
            self.log(f"Failed to save report: {e}", "ERROR")
            return None
    
    async def run_all_diagnostics(self):
        """Run complete diagnostic suite"""
        self.log("Starting comprehensive authentication diagnostics...", "INFO")
        
        # Run all diagnostic tests
        tests = []
        
        # 1. Backend health check
        health_result = await self.test_backend_health()
        tests.append(health_result)
        
        # 2. Auth endpoint testing
        auth_results = await self.test_auth_endpoint_codes()
        tests.append(auth_results)
        
        # 3. Database constraint testing
        constraint_results = await self.test_database_constraints()
        tests.append(constraint_results)
        
        # 4. Auth flow operations
        auth_flow_results = await self.test_specific_auth_flow_operations()
        tests.append(auth_flow_results)
        
        # Store results
        self.results["tests"] = tests
        
        # Analyze and generate recommendations
        recommendations, summary = self.analyze_results()
        
        # Print results
        self.print_recommendations(recommendations, summary)
        
        # Save detailed report
        report_file = self.save_report()
        
        return self.results

async def main():
    """Main function to run diagnostics"""
    print("MarketEdge Authentication Diagnostic Runner")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    try:
        async with AuthDiagnosticRunner() as runner:
            results = await runner.run_all_diagnostics()
            
            print("\n" + "=" * 80)
            print("DIAGNOSTIC COMPLETE")
            print("=" * 80)
            
            return results
            
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted by user")
        return None
    except Exception as e:
        print(f"\n\nDiagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher required")
        sys.exit(1)
    
    # Check required packages
    try:
        import aiohttp
    except ImportError:
        print("Error: aiohttp package required. Install with: pip install aiohttp")
        sys.exit(1)
    
    # Run diagnostics
    results = asyncio.run(main())
    
    if results:
        print("\n✅ Diagnostic completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Diagnostic failed")
        sys.exit(1)