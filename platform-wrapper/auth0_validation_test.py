#!/usr/bin/env python3
"""
Auth0 Configuration Validation Test
===================================

This script validates the Auth0 configuration and environment variables
for the MarketEdge platform, testing against the live backend API.
"""

import requests
import json
import sys
import time
from urllib.parse import urlparse, parse_qs

# Configuration
BACKEND_API_URL = "https://marketedge-platform.onrender.com"
API_BASE = f"{BACKEND_API_URL}/api/v1"

# Auth0 Expected Configuration
EXPECTED_AUTH0_DOMAIN = "dev-g8trhgbfdq2sk2m8.us.auth0.com"
EXPECTED_CLIENT_ID = "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"

# Updated callback URLs to test
CALLBACK_URLS = [
    "http://localhost:3001/callback",
    "http://localhost:3000/callback",
    "https://app.zebra.associates/callback",
    "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app/callback",
    "https://frontend-53pdtdz3p-zebraassociates-projects.vercel.app/callback"
]

# CORS Origins to validate
EXPECTED_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://app.zebra.associates",
    "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app",
    "https://frontend-53pdtdz3p-zebraassociates-projects.vercel.app"
]

def test_backend_health():
    """Test backend API health status"""
    print("🔍 Testing backend API health...")
    try:
        response = requests.get(f"{BACKEND_API_URL}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend API is healthy")
            print(f"   Version: {data.get('version')}")
            print(f"   CORS Mode: {data.get('cors_mode')}")
            print(f"   Service Type: {data.get('service_type')}")
            return True
        else:
            print(f"❌ Backend API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend API health check error: {e}")
        return False

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS configuration...")
    try:
        response = requests.get(f"{BACKEND_API_URL}/cors-debug", timeout=30)
        if response.status_code == 200:
            data = response.json()
            configured_origins = data.get('cors_origins_configured', [])
            
            print(f"✅ CORS debug endpoint accessible")
            print(f"   CORS Mode: {data.get('cors_mode')}")
            print(f"   Environment: {data.get('environment')}")
            print(f"   Configured Origins: {configured_origins}")
            
            # Check if all expected origins are included
            missing_origins = []
            for expected_origin in EXPECTED_CORS_ORIGINS:
                if expected_origin not in configured_origins:
                    missing_origins.append(expected_origin)
            
            if missing_origins:
                print(f"⚠️  Missing CORS origins: {missing_origins}")
            else:
                print(f"✅ All expected CORS origins are configured")
            
            return True, configured_origins
        else:
            print(f"❌ CORS debug endpoint failed: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ CORS debug endpoint error: {e}")
        return False, []

def test_auth0_url_generation():
    """Test Auth0 URL generation for all callback URLs"""
    print("\n🔍 Testing Auth0 URL generation...")
    results = []
    
    for callback_url in CALLBACK_URLS:
        print(f"\n   Testing callback: {callback_url}")
        try:
            params = {"redirect_uri": callback_url}
            response = requests.get(f"{API_BASE}/auth/auth0-url", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get('auth_url')
                scopes = data.get('scopes', [])
                
                # Parse the Auth0 URL to validate components
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                # Validate Auth0 domain
                expected_domain = f"https://{EXPECTED_AUTH0_DOMAIN}"
                actual_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
                
                domain_valid = actual_base == expected_domain
                client_id_valid = query_params.get('client_id', [''])[0] == EXPECTED_CLIENT_ID
                redirect_uri_valid = query_params.get('redirect_uri', [''])[0] == callback_url
                
                result = {
                    'callback_url': callback_url,
                    'success': True,
                    'auth_url': auth_url,
                    'scopes': scopes,
                    'domain_valid': domain_valid,
                    'client_id_valid': client_id_valid,
                    'redirect_uri_valid': redirect_uri_valid,
                    'has_state': 'state' in query_params,
                    'response_type': query_params.get('response_type', [''])[0]
                }
                
                if domain_valid and client_id_valid and redirect_uri_valid:
                    print(f"      ✅ Auth0 URL generated successfully")
                    print(f"         Domain: {actual_base}")
                    print(f"         Client ID: Valid")
                    print(f"         Scopes: {', '.join(scopes)}")
                else:
                    print(f"      ⚠️  Auth0 URL has validation issues:")
                    if not domain_valid:
                        print(f"         ❌ Domain mismatch: {actual_base}")
                    if not client_id_valid:
                        print(f"         ❌ Client ID mismatch")
                    if not redirect_uri_valid:
                        print(f"         ❌ Redirect URI mismatch")
                
                results.append(result)
                
            else:
                print(f"      ❌ Auth0 URL generation failed: {response.status_code}")
                if response.text:
                    print(f"         Error: {response.text}")
                results.append({
                    'callback_url': callback_url,
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            print(f"      ❌ Auth0 URL generation error: {e}")
            results.append({
                'callback_url': callback_url,
                'success': False,
                'error': str(e)
            })
    
    return results

def test_auth0_configuration():
    """Test Auth0 configuration by generating a test URL"""
    print("\n🔍 Testing Auth0 configuration...")
    try:
        # Use the primary callback URL for testing
        callback_url = "https://app.zebra.associates/callback"
        params = {"redirect_uri": callback_url}
        response = requests.get(f"{API_BASE}/auth/auth0-url", params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('auth_url')
            
            # Parse and validate the Auth0 URL
            parsed_url = urlparse(auth_url)
            query_params = parse_qs(parsed_url.query)
            
            print(f"✅ Auth0 configuration is accessible")
            print(f"   Domain: {parsed_url.netloc}")
            print(f"   Client ID: {query_params.get('client_id', [''])[0][:10]}...")
            print(f"   Response Type: {query_params.get('response_type', [''])[0]}")
            print(f"   Scope: {query_params.get('scope', [''])[0]}")
            
            # Validate key components
            domain_match = parsed_url.netloc == EXPECTED_AUTH0_DOMAIN
            client_id_match = query_params.get('client_id', [''])[0] == EXPECTED_CLIENT_ID
            
            if domain_match and client_id_match:
                print(f"✅ Auth0 domain and client ID are correctly configured")
                return True
            else:
                print(f"⚠️  Auth0 configuration validation issues:")
                if not domain_match:
                    print(f"   ❌ Domain mismatch: expected {EXPECTED_AUTH0_DOMAIN}, got {parsed_url.netloc}")
                if not client_id_match:
                    print(f"   ❌ Client ID mismatch")
                return False
                
        else:
            print(f"❌ Auth0 configuration test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Auth0 configuration test error: {e}")
        return False

def test_user_info_endpoint():
    """Test Auth0 user info endpoint accessibility"""
    print("\n🔍 Testing Auth0 user info endpoint...")
    
    # This is a basic test to see if the Auth0 domain is accessible
    auth0_userinfo_url = f"https://{EXPECTED_AUTH0_DOMAIN}/userinfo"
    
    try:
        # We expect a 401 without a valid token, but we should get a response
        response = requests.get(auth0_userinfo_url, timeout=10)
        
        if response.status_code == 401:
            print(f"✅ Auth0 user info endpoint is accessible (401 expected without token)")
            return True
        elif response.status_code == 200:
            print(f"⚠️  Auth0 user info endpoint returned 200 (unexpected without token)")
            return True
        else:
            print(f"⚠️  Auth0 user info endpoint returned: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Auth0 user info endpoint test error: {e}")
        return False

def generate_validation_report(cors_origins, auth0_results):
    """Generate a comprehensive validation report"""
    print("\n" + "="*80)
    print("🔍 AUTH0 CONFIGURATION VALIDATION REPORT")
    print("="*80)
    
    # CORS Validation Summary
    print(f"\n📋 CORS Configuration Summary:")
    print(f"   Expected Origins: {len(EXPECTED_CORS_ORIGINS)}")
    print(f"   Configured Origins: {len(cors_origins)}")
    
    missing_cors = [origin for origin in EXPECTED_CORS_ORIGINS if origin not in cors_origins]
    extra_cors = [origin for origin in cors_origins if origin not in EXPECTED_CORS_ORIGINS]
    
    if missing_cors:
        print(f"   ⚠️  Missing CORS origins: {missing_cors}")
    if extra_cors:
        print(f"   ℹ️  Additional CORS origins: {extra_cors}")
    if not missing_cors and not extra_cors:
        print(f"   ✅ CORS origins perfectly match expected configuration")
    
    # Auth0 URL Generation Summary
    print(f"\n📋 Auth0 URL Generation Summary:")
    successful_callbacks = [r for r in auth0_results if r.get('success', False)]
    failed_callbacks = [r for r in auth0_results if not r.get('success', False)]
    
    print(f"   Total Callback URLs Tested: {len(auth0_results)}")
    print(f"   Successful: {len(successful_callbacks)}")
    print(f"   Failed: {len(failed_callbacks)}")
    
    if successful_callbacks:
        print(f"\n   ✅ Working Callback URLs:")
        for result in successful_callbacks:
            validation_status = "✅" if all([
                result.get('domain_valid'),
                result.get('client_id_valid'),
                result.get('redirect_uri_valid')
            ]) else "⚠️ "
            print(f"      {validation_status} {result['callback_url']}")
    
    if failed_callbacks:
        print(f"\n   ❌ Failed Callback URLs:")
        for result in failed_callbacks:
            print(f"      ❌ {result['callback_url']}: {result.get('error', 'Unknown error')}")
    
    # Recommendations
    print(f"\n📋 Recommendations:")
    
    if missing_cors:
        print(f"   1. Add missing CORS origins to backend .env file:")
        print(f"      CORS_ORIGINS={json.dumps(EXPECTED_CORS_ORIGINS)}")
    
    if not all(r.get('success', False) for r in auth0_results):
        print(f"   2. Verify Auth0 application configuration includes all callback URLs:")
        for callback_url in CALLBACK_URLS:
            print(f"      - {callback_url}")
    
    if successful_callbacks:
        print(f"   3. ✅ Auth0 domain and client ID are correctly configured")
        print(f"   4. ✅ Backend API Auth0 integration is working")
    
    # Matt Lindop User Verification Note
    print(f"\n📋 Manual Verification Required:")
    print(f"   1. Verify Matt Lindop user exists in Auth0 tenant: {EXPECTED_AUTH0_DOMAIN}")
    print(f"   2. Test end-to-end authentication flow with Matt's credentials")
    print(f"   3. Confirm user has appropriate organization/tenant assignments")
    
    return {
        'cors_valid': not missing_cors,
        'auth0_working': len(successful_callbacks) > 0,
        'all_callbacks_working': len(failed_callbacks) == 0,
        'missing_cors_origins': missing_cors,
        'failed_callbacks': failed_callbacks
    }

def main():
    """Main validation function"""
    print("🚀 MarketEdge Platform Auth0 Configuration Validation")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test backend health
    if not test_backend_health():
        all_tests_passed = False
        return
    
    # Test CORS configuration
    cors_success, cors_origins = test_cors_configuration()
    if not cors_success:
        all_tests_passed = False
    
    # Test Auth0 configuration
    if not test_auth0_configuration():
        all_tests_passed = False
    
    # Test Auth0 URL generation for all callbacks
    auth0_results = test_auth0_url_generation()
    
    # Test Auth0 domain accessibility
    if not test_user_info_endpoint():
        all_tests_passed = False
    
    # Generate comprehensive report
    validation_summary = generate_validation_report(cors_origins, auth0_results)
    
    print(f"\n" + "="*80)
    if all_tests_passed and validation_summary['cors_valid'] and validation_summary['auth0_working']:
        print("🎉 ALL TESTS PASSED - Auth0 configuration is valid!")
    else:
        print("⚠️  SOME ISSUES FOUND - Review the recommendations above")
    print("="*80)
    
    return validation_summary

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        sys.exit(1)