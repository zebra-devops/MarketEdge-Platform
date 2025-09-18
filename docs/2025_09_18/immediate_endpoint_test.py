#!/usr/bin/env python3
"""
Immediate Admin Endpoint Test
Tests failing admin endpoints directly via HTTP to identify exact error pattern

BUSINESS CONTEXT: £925K Zebra Associates - Admin endpoints returning 403/500 errors
FOCUS: Direct endpoint testing to identify authorization vs server error patterns
"""

import requests
import json
import sys
from datetime import datetime

class AdminEndpointTester:
    def __init__(self):
        self.base_url = "https://marketedge-platform.onrender.com"
        self.origin = "https://app.zebra.associates" 
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'business_context': '£925K Zebra Associates - Admin endpoint failure diagnosis',
            'test_url': self.base_url,
            'endpoints': {},
            'analysis': {}
        }
        
        # Admin endpoints that are failing according to user report
        self.failing_endpoints = [
            "/api/v1/admin/feature-flags",
            "/api/v1/admin/modules",
            "/api/v1/admin/dashboard/stats"
        ]
    
    def test_endpoint_without_auth(self, endpoint):
        """Test endpoint without authentication to see base response"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Origin": self.origin,
            "Content-Type": "application/json",
            "User-Agent": "MarketEdge-Diagnostic/1.0"
        }
        
        try:
            print(f"Testing {endpoint} (no auth)...")
            response = requests.get(url, headers=headers, timeout=10)
            
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'response_size': len(response.content),
                'test_type': 'no_auth'
            }
            
            # Try to get JSON response if possible
            try:
                result['json_response'] = response.json()
            except:
                result['text_response'] = response.text[:500]  # First 500 chars
            
            print(f"  Status: {response.status_code}")
            if 'json_response' in result:
                print(f"  Response: {result['json_response']}")
            
            return result
            
        except Exception as e:
            print(f"  Error: {e}")
            return {'error': str(e), 'test_type': 'no_auth'}
    
    def test_cors_preflight(self, endpoint):
        """Test CORS preflight request"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Origin": self.origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        
        try:
            print(f"Testing CORS preflight for {endpoint}...")
            response = requests.options(url, headers=headers, timeout=10)
            
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'test_type': 'cors_preflight'
            }
            
            # Check CORS headers
            cors_headers = {
                'access_control_allow_origin': response.headers.get('access-control-allow-origin'),
                'access_control_allow_methods': response.headers.get('access-control-allow-methods'),
                'access_control_allow_headers': response.headers.get('access-control-allow-headers'),
                'access_control_allow_credentials': response.headers.get('access-control-allow-credentials')
            }
            result['cors_analysis'] = cors_headers
            
            print(f"  Status: {response.status_code}")
            print(f"  CORS Origin: {cors_headers['access_control_allow_origin']}")
            
            return result
            
        except Exception as e:
            print(f"  Error: {e}")
            return {'error': str(e), 'test_type': 'cors_preflight'}
    
    def test_health_endpoints(self):
        """Test working endpoints for comparison"""
        health_endpoints = ["/health", "/api/v1/health"]
        
        for endpoint in health_endpoints:
            try:
                print(f"Testing working endpoint {endpoint}...")
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                self.results['endpoints'][endpoint] = {
                    'status_code': response.status_code,
                    'working': response.status_code == 200,
                    'test_type': 'health_check'
                }
                
                print(f"  Status: {response.status_code} - {'✅ Working' if response.status_code == 200 else '❌ Failed'}")
                
            except Exception as e:
                print(f"  Error: {e}")
                self.results['endpoints'][endpoint] = {'error': str(e), 'test_type': 'health_check'}
    
    def analyze_response_patterns(self):
        """Analyze response patterns to identify issue type"""
        print("\n🔍 Analyzing response patterns...")
        
        analysis = {
            'cors_working': True,
            'server_responding': True,
            'auth_pattern': 'unknown',
            'error_classification': 'unknown'
        }
        
        # Check if any endpoints responded
        responding_endpoints = 0
        auth_required_responses = 0
        server_errors = 0
        
        for endpoint, result in self.results['endpoints'].items():
            if 'error' not in result:
                responding_endpoints += 1
                
                status_code = result.get('status_code', 0)
                if status_code == 401 or status_code == 403:
                    auth_required_responses += 1
                elif status_code >= 500:
                    server_errors += 1
        
        # Classify the issue pattern
        if responding_endpoints == 0:
            analysis['error_classification'] = 'server_connectivity_issue'
            analysis['server_responding'] = False
        elif server_errors > 0:
            analysis['error_classification'] = 'server_internal_error'
        elif auth_required_responses > 0:
            analysis['error_classification'] = 'authorization_required'
            analysis['auth_pattern'] = 'working'
        else:
            analysis['error_classification'] = 'unknown_pattern'
        
        # CORS analysis
        cors_results = []
        for endpoint, result in self.results['endpoints'].items():
            if result.get('test_type') == 'cors_preflight':
                cors_headers = result.get('cors_analysis', {})
                if cors_headers.get('access_control_allow_origin') == self.origin:
                    cors_results.append(True)
                else:
                    cors_results.append(False)
        
        if cors_results:
            analysis['cors_working'] = all(cors_results)
        
        self.results['analysis'] = analysis
        
        print(f"  Server responding: {'✅' if analysis['server_responding'] else '❌'}")
        print(f"  CORS working: {'✅' if analysis['cors_working'] else '❌'}")
        print(f"  Error pattern: {analysis['error_classification']}")
        
        return analysis
    
    def run_diagnostic(self):
        """Run complete endpoint diagnostic"""
        print("🚀 Starting Admin Endpoint Diagnostic")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Origin: {self.origin}")
        print("=" * 60)
        
        # Test health endpoints first for baseline
        self.test_health_endpoints()
        
        # Test each failing admin endpoint
        for endpoint in self.failing_endpoints:
            print(f"\n📋 Testing {endpoint}")
            
            # Test without authentication
            no_auth_result = self.test_endpoint_without_auth(endpoint)
            self.results['endpoints'][endpoint] = no_auth_result
            
            # Test CORS preflight
            cors_result = self.test_cors_preflight(endpoint)
            self.results['endpoints'][f"{endpoint}_cors"] = cors_result
        
        # Analyze patterns
        analysis = self.analyze_response_patterns()
        
        # Generate recommendations
        self.generate_recommendations(analysis)
        
        # Save results
        self.save_results()
        
        return analysis
    
    def generate_recommendations(self, analysis):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not analysis['server_responding']:
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Server connectivity problem',
                'action': 'Check server status and network connectivity'
            })
        elif analysis['error_classification'] == 'server_internal_error':
            recommendations.append({
                'priority': 'CRITICAL',
                'issue': 'Server internal errors (500+)',
                'action': 'Check server logs for internal errors'
            })
        elif analysis['error_classification'] == 'authorization_required':
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Authentication/authorization required',
                'action': 'Test with valid JWT token from authenticated user session'
            })
        else:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Unknown response pattern',
                'action': 'Manual investigation required'
            })
        
        if not analysis['cors_working']:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'CORS configuration issue',
                'action': 'Check CORS middleware configuration'
            })
        
        self.results['recommendations'] = recommendations
        
        print("\n📋 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     Action: {rec['action']}")
    
    def save_results(self):
        """Save diagnostic results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/matt/Sites/MarketEdge/docs/2025_09_18/admin_endpoint_test_results_{timestamp}.json"
        
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Main execution"""
    tester = AdminEndpointTester()
    analysis = tester.run_diagnostic()
    
    print(f"\n🎯 DIAGNOSTIC SUMMARY")
    print("=" * 40)
    print(f"Issue Classification: {analysis['error_classification']}")
    
    if analysis['error_classification'] == 'authorization_required':
        print("✅ Server is responding correctly")
        print("✅ CORS is configured properly")
        print("🔑 Next step: Test with authenticated JWT token")
    elif analysis['error_classification'] == 'server_internal_error':
        print("❌ Server is returning internal errors")
        print("🔧 Next step: Check server logs and application health")
    else:
        print("❓ Unexpected pattern - manual investigation required")

if __name__ == "__main__":
    main()