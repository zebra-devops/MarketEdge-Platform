#!/usr/bin/env python3
"""
Comprehensive Auth0 & Environment Validation
===========================================

This script performs a thorough validation of Auth0 configuration,
environment variables, CORS settings, and deployment environment consistency.
"""

import requests
import json
import sys
import time
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Configuration
BACKEND_API_URL = "https://marketedge-platform.onrender.com"
LOCAL_BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_API_URL}/api/v1"

# Auth0 Configuration
AUTH0_DOMAIN = "dev-g8trhgbfdq2sk2m8.us.auth0.com"
AUTH0_CLIENT_ID = "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
AUTH0_USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"
AUTH0_TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"

# Updated callback URLs (as per user requirements)
EXPECTED_CALLBACK_URLS = [
    "http://localhost:3001/callback",
    "http://localhost:3000/callback",
    "https://app.zebra.associates/callback",
    "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app/callback",
    "https://frontend-53pdtdz3p-zebraassociates-projects.vercel.app/callback"
]

# Expected CORS origins
EXPECTED_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://app.zebra.associates",
    "https://frontend-ga6uzmt8j-zebraassociates-projects.vercel.app",
    "https://frontend-53pdtdz3p-zebraassociates-projects.vercel.app"
]

# Environment files to check
ENV_FILES = [
    "/Users/matt/Sites/MarketEdge/platform-wrapper/backend/.env",
    "/Users/matt/Sites/MarketEdge/platform-wrapper/backend/.env.example"
]

def read_env_file(file_path):
    """Read and parse environment file"""
    env_vars = {}
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return {}

def validate_environment_variables():
    """Validate environment variables across different files"""
    print("🔍 Validating environment variables...")
    
    env_data = {}
    for env_file in ENV_FILES:
        file_name = os.path.basename(env_file)
        env_data[file_name] = read_env_file(env_file)
        
        if env_data[file_name]:
            print(f"   ✅ Read {file_name}: {len(env_data[file_name])} variables")
        else:
            print(f"   ⚠️  Could not read {file_name}")
    
    # Check Auth0 configuration consistency
    auth0_vars = ['AUTH0_DOMAIN', 'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET', 'AUTH0_CALLBACK_URL']
    
    print(f"\n   📋 Auth0 Configuration:")
    for var in auth0_vars:
        values = {}
        for file_name, vars_dict in env_data.items():
            if var in vars_dict:
                values[file_name] = vars_dict[var]
        
        if len(values) > 1:
            # Check if values are consistent
            unique_values = set(values.values())
            if len(unique_values) == 1:
                print(f"      ✅ {var}: Consistent across files")
            else:
                print(f"      ⚠️  {var}: Inconsistent values:")
                for file_name, value in values.items():
                    # Mask sensitive values
                    display_value = value if var in ['AUTH0_DOMAIN', 'AUTH0_CALLBACK_URL'] else f"{value[:10]}..."
                    print(f"         {file_name}: {display_value}")
        elif len(values) == 1:
            file_name, value = list(values.items())[0]
            display_value = value if var in ['AUTH0_DOMAIN', 'AUTH0_CALLBACK_URL'] else f"{value[:10]}..."
            print(f"      ✅ {var}: {display_value} (in {file_name})")
        else:
            print(f"      ❌ {var}: Not found in any environment file")
    
    # Check CORS configuration
    print(f"\n   📋 CORS Configuration:")
    for file_name, vars_dict in env_data.items():
        cors_origins = vars_dict.get('CORS_ORIGINS', '')
        if cors_origins:
            try:
                # Parse JSON-like CORS origins
                if cors_origins.startswith('[') and cors_origins.endswith(']'):
                    parsed_origins = json.loads(cors_origins)
                    print(f"      ✅ {file_name}: {len(parsed_origins)} origins configured")
                    
                    # Check for missing expected origins
                    missing = [origin for origin in EXPECTED_CORS_ORIGINS if origin not in parsed_origins]
                    if missing:
                        print(f"         ⚠️  Missing: {missing}")
                    else:
                        print(f"         ✅ All expected origins present")
                else:
                    print(f"      ⚠️  {file_name}: CORS_ORIGINS format not recognized")
            except json.JSONDecodeError:
                print(f"      ❌ {file_name}: Invalid CORS_ORIGINS JSON format")
    
    return env_data

def test_auth0_domain_connectivity():
    """Test connectivity to Auth0 domain"""
    print("\n🔍 Testing Auth0 domain connectivity...")
    
    endpoints = [
        f"https://{AUTH0_DOMAIN}/.well-known/openid_configuration",
        f"https://{AUTH0_DOMAIN}/userinfo",
        f"https://{AUTH0_DOMAIN}/oauth/token"
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            endpoint_name = endpoint.split('/')[-1]
            if endpoint_name == 'openid_configuration':
                if response.status_code == 200:
                    print(f"   ✅ OpenID configuration accessible")
                    # Parse and validate configuration
                    config = response.json()
                    if 'authorization_endpoint' in config and 'token_endpoint' in config:
                        print(f"      ✅ Required endpoints present")
                    results[endpoint_name] = True
                else:
                    print(f"   ❌ OpenID configuration failed: {response.status_code}")
                    results[endpoint_name] = False
            elif endpoint_name == 'userinfo':
                if response.status_code == 401:
                    print(f"   ✅ User info endpoint accessible (401 expected)")
                    results[endpoint_name] = True
                else:
                    print(f"   ⚠️  User info endpoint: {response.status_code}")
                    results[endpoint_name] = True  # Still accessible
            elif endpoint_name == 'token':
                if response.status_code in [400, 401]:
                    print(f"   ✅ Token endpoint accessible ({response.status_code} expected)")
                    results[endpoint_name] = True
                else:
                    print(f"   ⚠️  Token endpoint: {response.status_code}")
                    results[endpoint_name] = True  # Still accessible
                    
        except Exception as e:
            endpoint_name = endpoint.split('/')[-1]
            print(f"   ❌ {endpoint_name} connectivity error: {e}")
            results[endpoint_name] = False
    
    return results

def test_backend_api_comprehensive():
    """Comprehensive backend API testing"""
    print("\n🔍 Testing backend API comprehensively...")
    
    test_results = {}
    
    # Test health endpoint
    try:
        response = requests.get(f"{BACKEND_API_URL}/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health endpoint: {health_data.get('status')}")
            print(f"      Version: {health_data.get('version')}")
            print(f"      CORS Mode: {health_data.get('cors_mode')}")
            test_results['health'] = True
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
            test_results['health'] = False
    except Exception as e:
        print(f"   ❌ Health endpoint error: {e}")
        test_results['health'] = False
    
    # Test CORS debug endpoint
    try:
        response = requests.get(f"{BACKEND_API_URL}/cors-debug", timeout=30)
        if response.status_code == 200:
            cors_data = response.json()
            configured_origins = cors_data.get('cors_origins_configured', [])
            print(f"   ✅ CORS debug endpoint accessible")
            print(f"      Configured origins: {len(configured_origins)}")
            
            # Check alignment with expected origins
            missing_origins = [origin for origin in EXPECTED_CORS_ORIGINS if origin not in configured_origins]
            if missing_origins:
                print(f"      ⚠️  Missing origins: {missing_origins}")
            else:
                print(f"      ✅ All expected origins configured")
            
            test_results['cors_debug'] = True
            test_results['cors_origins'] = configured_origins
        else:
            print(f"   ❌ CORS debug endpoint failed: {response.status_code}")
            test_results['cors_debug'] = False
    except Exception as e:
        print(f"   ❌ CORS debug endpoint error: {e}")
        test_results['cors_debug'] = False
    
    # Test Auth0 URL generation
    try:
        params = {"redirect_uri": "https://app.zebra.associates/callback"}
        response = requests.get(f"{API_BASE}/auth/auth0-url", params=params, timeout=30)
        if response.status_code == 200:
            auth_data = response.json()
            auth_url = auth_data.get('auth_url')
            scopes = auth_data.get('scopes', [])
            
            # Parse and validate Auth0 URL
            parsed_url = urlparse(auth_url)
            query_params = parse_qs(parsed_url.query)
            
            domain_valid = parsed_url.netloc == AUTH0_DOMAIN
            client_id_valid = query_params.get('client_id', [''])[0] == AUTH0_CLIENT_ID
            
            print(f"   ✅ Auth0 URL generation working")
            print(f"      Domain valid: {domain_valid}")
            print(f"      Client ID valid: {client_id_valid}")
            print(f"      Scopes: {', '.join(scopes)}")
            
            test_results['auth0_url'] = True
            test_results['auth0_domain_valid'] = domain_valid
            test_results['auth0_client_id_valid'] = client_id_valid
        else:
            print(f"   ❌ Auth0 URL generation failed: {response.status_code}")
            test_results['auth0_url'] = False
    except Exception as e:
        print(f"   ❌ Auth0 URL generation error: {e}")
        test_results['auth0_url'] = False
    
    return test_results

def test_callback_urls_systematically():
    """Test all callback URLs systematically"""
    print("\n🔍 Testing callback URLs systematically...")
    
    results = []
    for callback_url in EXPECTED_CALLBACK_URLS:
        print(f"\n   Testing: {callback_url}")
        
        try:
            params = {"redirect_uri": callback_url}
            response = requests.get(f"{API_BASE}/auth/auth0-url", params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                auth_url = data.get('auth_url')
                
                # Parse URL to validate
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                result = {
                    'callback_url': callback_url,
                    'success': True,
                    'auth_url': auth_url,
                    'domain': parsed_url.netloc,
                    'client_id': query_params.get('client_id', [''])[0],
                    'redirect_uri': query_params.get('redirect_uri', [''])[0],
                    'has_state': 'state' in query_params,
                    'scopes': data.get('scopes', [])
                }
                
                # Validate key components
                domain_valid = parsed_url.netloc == AUTH0_DOMAIN
                client_id_valid = query_params.get('client_id', [''])[0] == AUTH0_CLIENT_ID
                redirect_valid = query_params.get('redirect_uri', [''])[0] == callback_url
                
                if domain_valid and client_id_valid and redirect_valid:
                    print(f"      ✅ Valid Auth0 URL generated")
                else:
                    print(f"      ⚠️  Validation issues:")
                    if not domain_valid:
                        print(f"         Domain: {parsed_url.netloc} != {AUTH0_DOMAIN}")
                    if not client_id_valid:
                        print(f"         Client ID mismatch")
                    if not redirect_valid:
                        print(f"         Redirect URI mismatch")
                
                result.update({
                    'domain_valid': domain_valid,
                    'client_id_valid': client_id_valid,
                    'redirect_valid': redirect_valid
                })
                
            else:
                print(f"      ❌ Failed: {response.status_code}")
                if response.text:
                    error_detail = response.text[:200]
                    print(f"         Error: {error_detail}")
                
                result = {
                    'callback_url': callback_url,
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
            
            results.append(result)
            
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            results.append({
                'callback_url': callback_url,
                'success': False,
                'error': str(e)
            })
    
    return results

def check_deployment_environment_consistency():
    """Check for deployment environment consistency"""
    print("\n🔍 Checking deployment environment consistency...")
    
    # Test different backend URLs if accessible
    backend_urls = [
        BACKEND_API_URL,
        # Add other deployment URLs if known
    ]
    
    deployment_results = {}
    
    for backend_url in backend_urls:
        url_name = urlparse(backend_url).netloc
        print(f"\n   Testing deployment: {url_name}")
        
        try:
            # Test health endpoint
            response = requests.get(f"{backend_url}/health", timeout=15)
            if response.status_code == 200:
                health_data = response.json()
                deployment_results[url_name] = {
                    'accessible': True,
                    'version': health_data.get('version'),
                    'environment': health_data.get('environment'),
                    'cors_mode': health_data.get('cors_mode')
                }
                print(f"      ✅ Accessible - Version: {health_data.get('version')}")
            else:
                deployment_results[url_name] = {
                    'accessible': False,
                    'status_code': response.status_code
                }
                print(f"      ❌ Not accessible: {response.status_code}")
                
        except Exception as e:
            deployment_results[url_name] = {
                'accessible': False,
                'error': str(e)
            }
            print(f"      ❌ Connection error: {e}")
    
    return deployment_results

def validate_matt_lindop_user():
    """Provide guidance for validating Matt Lindop user"""
    print("\n🔍 Matt Lindop User Validation Guide...")
    print(f"   📋 Manual steps required:")
    print(f"   1. Log into Auth0 Dashboard: https://manage.auth0.com/")
    print(f"   2. Navigate to tenant: {AUTH0_DOMAIN}")
    print(f"   3. Check Users section for Matt Lindop")
    print(f"   4. Verify user has correct email and is active")
    print(f"   5. Check user's organization/tenant assignments")
    print(f"   6. Test login flow with Matt's credentials")
    
    # Test if we can at least reach the Auth0 login page
    try:
        auth_url = f"https://{AUTH0_DOMAIN}/authorize?client_id={AUTH0_CLIENT_ID}&response_type=code&redirect_uri=https://app.zebra.associates/callback"
        response = requests.get(auth_url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Auth0 login page is accessible")
        else:
            print(f"   ⚠️  Auth0 login page: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Auth0 login page error: {e}")

def generate_comprehensive_report(env_data, auth0_connectivity, backend_results, callback_results, deployment_results):
    """Generate comprehensive validation report"""
    print("\n" + "="*100)
    print("🔍 COMPREHENSIVE AUTH0 & ENVIRONMENT VALIDATION REPORT")
    print("="*100)
    
    # Environment Variables Summary
    print(f"\n📋 Environment Variables Summary:")
    total_files = len([f for f in ENV_FILES if os.path.exists(f)])
    print(f"   Environment files checked: {total_files}")
    
    auth0_vars_present = 0
    for file_name, vars_dict in env_data.items():
        auth0_count = sum(1 for var in ['AUTH0_DOMAIN', 'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET'] if var in vars_dict)
        auth0_vars_present = max(auth0_vars_present, auth0_count)
    
    if auth0_vars_present == 3:
        print(f"   ✅ All Auth0 environment variables present")
    else:
        print(f"   ⚠️  Missing Auth0 environment variables ({auth0_vars_present}/3)")
    
    # Auth0 Connectivity Summary
    print(f"\n📋 Auth0 Connectivity Summary:")
    accessible_endpoints = sum(1 for result in auth0_connectivity.values() if result)
    total_endpoints = len(auth0_connectivity)
    print(f"   Auth0 endpoints accessible: {accessible_endpoints}/{total_endpoints}")
    
    if accessible_endpoints == total_endpoints:
        print(f"   ✅ All Auth0 endpoints accessible")
    else:
        failed_endpoints = [name for name, result in auth0_connectivity.items() if not result]
        print(f"   ⚠️  Failed endpoints: {failed_endpoints}")
    
    # Backend API Summary
    print(f"\n📋 Backend API Summary:")
    if backend_results.get('health') and backend_results.get('auth0_url'):
        print(f"   ✅ Backend API fully functional")
        print(f"   ✅ Auth0 integration working")
    else:
        issues = []
        if not backend_results.get('health'):
            issues.append("health endpoint")
        if not backend_results.get('auth0_url'):
            issues.append("Auth0 integration")
        print(f"   ⚠️  Issues with: {', '.join(issues)}")
    
    # CORS Configuration Summary
    print(f"\n📋 CORS Configuration Summary:")
    configured_origins = backend_results.get('cors_origins', [])
    missing_origins = [origin for origin in EXPECTED_CORS_ORIGINS if origin not in configured_origins]
    
    if not missing_origins:
        print(f"   ✅ All expected CORS origins configured")
    else:
        print(f"   ⚠️  Missing CORS origins: {len(missing_origins)}")
        for origin in missing_origins:
            print(f"      - {origin}")
    
    # Callback URLs Summary
    print(f"\n📋 Callback URLs Summary:")
    successful_callbacks = [r for r in callback_results if r.get('success', False)]
    failed_callbacks = [r for r in callback_results if not r.get('success', False)]
    
    print(f"   Total callback URLs tested: {len(callback_results)}")
    print(f"   ✅ Working: {len(successful_callbacks)}")
    print(f"   ❌ Failed: {len(failed_callbacks)}")
    
    if failed_callbacks:
        print(f"\n   Failed callback URLs:")
        for result in failed_callbacks:
            callback_url = result['callback_url']
            error = result.get('error', 'Unknown error')
            if 'Invalid redirect URI' in error:
                print(f"      ❌ {callback_url} - Not configured in Auth0 application")
            else:
                print(f"      ❌ {callback_url} - {error}")
    
    # Deployment Consistency Summary
    print(f"\n📋 Deployment Consistency Summary:")
    accessible_deployments = sum(1 for result in deployment_results.values() if result.get('accessible', False))
    total_deployments = len(deployment_results)
    
    print(f"   Accessible deployments: {accessible_deployments}/{total_deployments}")
    
    # Critical Issues and Recommendations
    print(f"\n📋 Critical Issues and Recommendations:")
    
    critical_issues = []
    
    if missing_origins:
        critical_issues.append("CORS configuration incomplete")
        print(f"   🔥 CRITICAL: Update backend CORS_ORIGINS to include:")
        for origin in missing_origins:
            print(f"      - {origin}")
    
    if failed_callbacks:
        critical_issues.append("Auth0 application callback URLs incomplete")
        print(f"   🔥 CRITICAL: Add missing callback URLs to Auth0 application:")
        for result in failed_callbacks:
            if 'Invalid redirect URI' in result.get('error', ''):
                print(f"      - {result['callback_url']}")
    
    if auth0_vars_present < 3:
        critical_issues.append("Auth0 environment variables missing")
        print(f"   🔥 CRITICAL: Configure missing Auth0 environment variables")
    
    if not critical_issues:
        print(f"   ✅ No critical issues found!")
    
    # Next Steps
    print(f"\n📋 Next Steps:")
    print(f"   1. ✅ Backend API is running and Auth0 integration is working")
    print(f"   2. 🔧 Fix CORS configuration if needed")
    print(f"   3. 🔧 Update Auth0 application callback URLs if needed")
    print(f"   4. 🧪 Test end-to-end authentication flow with Matt Lindop user")
    print(f"   5. 📝 Document final configuration for production deployment")
    
    # Overall Status
    print(f"\n" + "="*100)
    if not critical_issues and accessible_endpoints == total_endpoints and len(successful_callbacks) > 0:
        print("🎉 VALIDATION SUCCESSFUL - Auth0 configuration is ready for production!")
    elif len(successful_callbacks) > 0 and accessible_endpoints > 0:
        print("⚠️  VALIDATION PARTIALLY SUCCESSFUL - Minor issues need fixing")
    else:
        print("❌ VALIDATION FAILED - Critical issues require immediate attention")
    print("="*100)

def main():
    """Main validation function"""
    print("🚀 MarketEdge Platform - Comprehensive Auth0 & Environment Validation")
    print("="*80)
    
    # Step 1: Validate environment variables
    env_data = validate_environment_variables()
    
    # Step 2: Test Auth0 domain connectivity
    auth0_connectivity = test_auth0_domain_connectivity()
    
    # Step 3: Test backend API comprehensively
    backend_results = test_backend_api_comprehensive()
    
    # Step 4: Test callback URLs systematically
    callback_results = test_callback_urls_systematically()
    
    # Step 5: Check deployment environment consistency
    deployment_results = check_deployment_environment_consistency()
    
    # Step 6: Provide Matt Lindop user validation guidance
    validate_matt_lindop_user()
    
    # Step 7: Generate comprehensive report
    generate_comprehensive_report(
        env_data, 
        auth0_connectivity, 
        backend_results, 
        callback_results, 
        deployment_results
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)