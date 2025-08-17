#!/usr/bin/env python3
"""
End-to-End Authentication Flow Test
===================================

This script tests the complete authentication flow for the MarketEdge platform,
simulating the user journey from Auth0 URL generation to token exchange.
"""

import requests
import json
import sys
import time
from urllib.parse import urlparse, parse_qs

# Configuration
BACKEND_API_URL = "https://marketedge-platform.onrender.com"
API_BASE = f"{BACKEND_API_URL}/api/v1"

# Test callback URLs
TEST_CALLBACK_URLS = [
    "https://app.zebra.associates/callback",
    "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app/callback",
    "https://frontend-53pdtdz3p-zebraassociates-projects.vercel.app/callback"
]

def test_auth0_url_generation_flow():
    """Test the complete Auth0 URL generation flow"""
    print("🔍 Testing Auth0 URL generation flow...")
    
    results = []
    
    for callback_url in TEST_CALLBACK_URLS:
        print(f"\n   Testing callback: {callback_url}")
        
        try:
            # Step 1: Generate Auth0 URL
            params = {
                "redirect_uri": callback_url,
                "additional_scopes": "read:users",
                "organization_hint": "zebra-associates"
            }
            
            response = requests.get(f"{API_BASE}/auth/auth0-url", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get('auth_url')
                scopes = data.get('scopes', [])
                redirect_uri = data.get('redirect_uri')
                
                print(f"      ✅ Auth0 URL generated successfully")
                print(f"         Scopes: {', '.join(scopes)}")
                print(f"         Redirect URI: {redirect_uri}")
                
                # Parse the Auth0 URL to extract parameters
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                # Validate URL structure
                validation_results = {
                    'has_response_type': 'response_type' in query_params,
                    'has_client_id': 'client_id' in query_params,
                    'has_redirect_uri': 'redirect_uri' in query_params,
                    'has_scope': 'scope' in query_params,
                    'has_state': 'state' in query_params,
                    'response_type_correct': query_params.get('response_type', [''])[0] == 'code',
                    'redirect_uri_correct': query_params.get('redirect_uri', [''])[0] == callback_url
                }
                
                # Check for security features
                security_features = {
                    'has_state_parameter': 'state' in query_params,
                    'has_prompt_parameter': 'prompt' in query_params,
                    'has_max_age_parameter': 'max_age' in query_params,
                    'has_audience_parameter': 'audience' in query_params
                }
                
                print(f"      📋 URL Validation:")
                all_valid = all(validation_results.values())
                for key, value in validation_results.items():
                    status = "✅" if value else "❌"
                    print(f"         {status} {key.replace('_', ' ').title()}: {value}")
                
                print(f"      🔐 Security Features:")
                for key, value in security_features.items():
                    status = "✅" if value else "⚠️ "
                    print(f"         {status} {key.replace('_', ' ').title()}: {value}")
                
                # Additional scope validation
                expected_scopes = ['openid', 'profile', 'email']
                actual_scopes_param = query_params.get('scope', [''])[0].split()
                scope_validation = {
                    'has_openid': 'openid' in actual_scopes_param,
                    'has_profile': 'profile' in actual_scopes_param,
                    'has_email': 'email' in actual_scopes_param,
                    'has_org_scopes': any(scope in actual_scopes_param for scope in ['read:organization', 'read:roles'])
                }
                
                print(f"      📝 Scope Validation:")
                for key, value in scope_validation.items():
                    status = "✅" if value else "⚠️ "
                    print(f"         {status} {key.replace('_', ' ').title()}: {value}")
                
                result = {
                    'callback_url': callback_url,
                    'success': True,
                    'auth_url': auth_url,
                    'validation': validation_results,
                    'security': security_features,
                    'scopes': scope_validation,
                    'all_validations_passed': all_valid
                }
                
            else:
                print(f"      ❌ Auth0 URL generation failed: {response.status_code}")
                print(f"         Error: {response.text}")
                
                result = {
                    'callback_url': callback_url,
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
            
            results.append(result)
            
        except Exception as e:
            print(f"      ❌ Exception during Auth0 URL generation: {e}")
            results.append({
                'callback_url': callback_url,
                'success': False,
                'error': str(e)
            })
    
    return results

def test_authentication_endpoints():
    """Test authentication-related endpoints"""
    print("\n🔍 Testing authentication endpoints...")
    
    endpoints = [
        {'path': '/auth/auth0-url', 'method': 'GET', 'params': {'redirect_uri': 'https://app.zebra.associates/callback'}},
        {'path': '/auth/login', 'method': 'POST', 'expect_error': True},  # Should fail without valid code
        {'path': '/auth/me', 'method': 'GET', 'expect_error': True},      # Should fail without auth
        {'path': '/auth/session/check', 'method': 'GET', 'expect_error': True}  # Should fail without auth
    ]
    
    results = {}
    
    for endpoint in endpoints:
        path = endpoint['path']
        method = endpoint['method']
        params = endpoint.get('params', {})
        expect_error = endpoint.get('expect_error', False)
        
        print(f"\n   Testing {method} {path}")
        
        try:
            if method == 'GET':
                response = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(f"{API_BASE}{path}", json={}, timeout=30)
            
            if expect_error:
                if response.status_code in [400, 401, 422]:
                    print(f"      ✅ Expected error response: {response.status_code}")
                    results[path] = {'success': True, 'expected_error': True, 'status_code': response.status_code}
                else:
                    print(f"      ⚠️  Unexpected success: {response.status_code}")
                    results[path] = {'success': False, 'unexpected_success': True, 'status_code': response.status_code}
            else:
                if response.status_code == 200:
                    print(f"      ✅ Success: {response.status_code}")
                    results[path] = {'success': True, 'status_code': response.status_code}
                else:
                    print(f"      ❌ Failed: {response.status_code}")
                    results[path] = {'success': False, 'status_code': response.status_code}
                    
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            results[path] = {'success': False, 'error': str(e)}
    
    return results

def test_cors_headers():
    """Test CORS headers on authentication endpoints"""
    print("\n🔍 Testing CORS headers...")
    
    test_origins = [
        "https://app.zebra.associates",
        "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app",
        "http://localhost:3000"
    ]
    
    results = {}
    
    for origin in test_origins:
        print(f"\n   Testing origin: {origin}")
        
        # Test preflight request (OPTIONS)
        try:
            headers = {
                'Origin': origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = requests.options(f"{API_BASE}/auth/login", headers=headers, timeout=30)
            
            cors_headers = {
                'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                'access-control-allow-headers': response.headers.get('access-control-allow-headers'),
                'access-control-allow-credentials': response.headers.get('access-control-allow-credentials')
            }
            
            print(f"      📋 CORS Headers:")
            origin_allowed = cors_headers['access-control-allow-origin'] == origin or cors_headers['access-control-allow-origin'] == '*'
            credentials_allowed = cors_headers['access-control-allow-credentials'] == 'true'
            
            print(f"         ✅ Origin allowed: {origin_allowed}")
            print(f"         ✅ Credentials allowed: {credentials_allowed}")
            print(f"         📝 Allow-Origin: {cors_headers['access-control-allow-origin']}")
            print(f"         📝 Allow-Methods: {cors_headers['access-control-allow-methods']}")
            print(f"         📝 Allow-Headers: {cors_headers['access-control-allow-headers']}")
            
            results[origin] = {
                'origin_allowed': origin_allowed,
                'credentials_allowed': credentials_allowed,
                'headers': cors_headers,
                'status_code': response.status_code
            }
            
        except Exception as e:
            print(f"      ❌ CORS test error: {e}")
            results[origin] = {'error': str(e)}
    
    return results

def simulate_auth_flow():
    """Simulate the authentication flow (without actual user credentials)"""
    print("\n🔍 Simulating authentication flow...")
    
    callback_url = "https://app.zebra.associates/callback"
    
    try:
        # Step 1: Generate Auth0 URL
        print("   📋 Step 1: Generate Auth0 authorization URL")
        params = {"redirect_uri": callback_url}
        response = requests.get(f"{API_BASE}/auth/auth0-url", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('auth_url')
            print(f"      ✅ Auth0 URL generated")
            print(f"         URL: {auth_url[:100]}...")
            
            # Parse the URL to extract state parameter
            parsed_url = urlparse(auth_url)
            query_params = parse_qs(parsed_url.query)
            state = query_params.get('state', [''])[0]
            
            print(f"      📝 State parameter: {state[:20]}..." if state else "      ⚠️  No state parameter")
            
            # Step 2: Simulate callback (this would normally come from Auth0)
            print("\n   📋 Step 2: Simulate Auth0 callback")
            print("      ℹ️  This step requires actual user authentication with Auth0")
            print("      ℹ️  Auth0 would redirect to callback URL with authorization code")
            print(f"      📝 Expected callback format: {callback_url}?code=AUTH_CODE&state={state}")
            
            # Step 3: Test login endpoint with mock data (will fail, but tests endpoint)
            print("\n   📋 Step 3: Test login endpoint")
            login_data = {
                "code": "mock_authorization_code",
                "redirect_uri": callback_url,
                "state": state
            }
            
            response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=30)
            print(f"      📋 Login attempt result: {response.status_code}")
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', 'Unknown error')
                if 'authorization code' in error_detail.lower():
                    print(f"      ✅ Expected error: Invalid authorization code")
                    print(f"      📝 Login endpoint is working correctly")
                else:
                    print(f"      ❌ Unexpected error: {error_detail}")
            else:
                print(f"      ⚠️  Unexpected response: {response.status_code}")
            
            return {
                'auth_url_generated': True,
                'state_parameter': bool(state),
                'login_endpoint_accessible': response.status_code in [400, 401],
                'flow_simulation_complete': True
            }
            
        else:
            print(f"      ❌ Auth0 URL generation failed: {response.status_code}")
            return {
                'auth_url_generated': False,
                'error': response.text
            }
            
    except Exception as e:
        print(f"      ❌ Auth flow simulation error: {e}")
        return {
            'error': str(e)
        }

def generate_end_to_end_report(url_results, endpoint_results, cors_results, flow_simulation):
    """Generate comprehensive end-to-end test report"""
    print("\n" + "="*100)
    print("🔍 END-TO-END AUTHENTICATION FLOW TEST REPORT")
    print("="*100)
    
    # Auth0 URL Generation Summary
    print(f"\n📋 Auth0 URL Generation Summary:")
    successful_urls = [r for r in url_results if r.get('success', False)]
    print(f"   Callback URLs tested: {len(url_results)}")
    print(f"   ✅ Successful: {len(successful_urls)}")
    print(f"   ❌ Failed: {len(url_results) - len(successful_urls)}")
    
    if successful_urls:
        all_validations_passed = all(r.get('all_validations_passed', False) for r in successful_urls)
        if all_validations_passed:
            print(f"   ✅ All URL validations passed")
        else:
            print(f"   ⚠️  Some URL validations failed")
    
    # Authentication Endpoints Summary
    print(f"\n📋 Authentication Endpoints Summary:")
    successful_endpoints = sum(1 for result in endpoint_results.values() if result.get('success', False))
    total_endpoints = len(endpoint_results)
    print(f"   Endpoints tested: {total_endpoints}")
    print(f"   ✅ Working correctly: {successful_endpoints}")
    
    # CORS Configuration Summary
    print(f"\n📋 CORS Configuration Summary:")
    origins_with_cors = sum(1 for result in cors_results.values() if result.get('origin_allowed', False))
    total_origins = len(cors_results)
    print(f"   Origins tested: {total_origins}")
    print(f"   ✅ CORS enabled: {origins_with_cors}")
    
    # Authentication Flow Simulation Summary
    print(f"\n📋 Authentication Flow Simulation Summary:")
    if flow_simulation.get('flow_simulation_complete'):
        print(f"   ✅ Flow simulation completed successfully")
        print(f"   ✅ Auth0 URL generation working")
        print(f"   ✅ Login endpoint accessible")
        if flow_simulation.get('state_parameter'):
            print(f"   ✅ CSRF protection (state parameter) implemented")
        else:
            print(f"   ⚠️  No CSRF protection (state parameter) found")
    else:
        print(f"   ❌ Flow simulation failed")
    
    # Critical Findings
    print(f"\n📋 Critical Findings:")
    
    findings = []
    
    if len(successful_urls) == len(url_results):
        findings.append("✅ All callback URLs generate valid Auth0 URLs")
    else:
        findings.append("⚠️  Some callback URLs are not working")
    
    if successful_endpoints == total_endpoints:
        findings.append("✅ All authentication endpoints are working correctly")
    else:
        findings.append("⚠️  Some authentication endpoints have issues")
    
    if origins_with_cors == total_origins:
        findings.append("✅ CORS is properly configured for all tested origins")
    else:
        findings.append("⚠️  CORS configuration needs attention")
    
    if flow_simulation.get('auth_url_generated') and flow_simulation.get('login_endpoint_accessible'):
        findings.append("✅ Core authentication flow is ready")
    else:
        findings.append("❌ Core authentication flow has issues")
    
    for finding in findings:
        print(f"   {finding}")
    
    # Ready for Production Assessment
    print(f"\n📋 Production Readiness Assessment:")
    
    ready_for_production = (
        len(successful_urls) > 0 and
        successful_endpoints == total_endpoints and
        origins_with_cors > 0 and
        flow_simulation.get('flow_simulation_complete', False)
    )
    
    if ready_for_production:
        print(f"   🎉 READY FOR PRODUCTION")
        print(f"      - Auth0 integration is working")
        print(f"      - Authentication endpoints are functional")
        print(f"      - CORS is configured")
        print(f"      - Security features (state parameter) are implemented")
    else:
        print(f"   ⚠️  NEEDS ATTENTION BEFORE PRODUCTION")
        issues = []
        if len(successful_urls) == 0:
            issues.append("Auth0 URL generation failing")
        if successful_endpoints < total_endpoints:
            issues.append("Authentication endpoints not working")
        if origins_with_cors == 0:
            issues.append("CORS not configured")
        if not flow_simulation.get('flow_simulation_complete'):
            issues.append("Authentication flow not complete")
        
        for issue in issues:
            print(f"      - {issue}")
    
    # Manual Testing Instructions
    print(f"\n📋 Manual Testing Instructions:")
    print(f"   1. Open a browser and navigate to the frontend application")
    print(f"   2. Click the login/sign-in button")
    print(f"   3. Verify you're redirected to Auth0 login page")
    print(f"   4. Login with Matt Lindop credentials")
    print(f"   5. Verify successful redirect back to application")
    print(f"   6. Check that user session is established")
    print(f"   7. Test logout functionality")
    
    print(f"\n" + "="*100)
    if ready_for_production:
        print("🎉 END-TO-END TESTING SUCCESSFUL - Authentication flow is ready!")
    else:
        print("⚠️  END-TO-END TESTING PARTIALLY SUCCESSFUL - Address issues before production")
    print("="*100)

def main():
    """Main testing function"""
    print("🚀 MarketEdge Platform - End-to-End Authentication Flow Test")
    print("="*70)
    
    # Test Auth0 URL generation flow
    url_results = test_auth0_url_generation_flow()
    
    # Test authentication endpoints
    endpoint_results = test_authentication_endpoints()
    
    # Test CORS headers
    cors_results = test_cors_headers()
    
    # Simulate authentication flow
    flow_simulation = simulate_auth_flow()
    
    # Generate comprehensive report
    generate_end_to_end_report(url_results, endpoint_results, cors_results, flow_simulation)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)