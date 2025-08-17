#!/usr/bin/env python3
"""
Epic 2 Final Phase: Auth0 Configuration Update Automation
Author: DevOps Engineer
Date: 2025-08-16

This script provides comprehensive Auth0 configuration updates for the Railway to Render migration.

CRITICAL UPDATES REQUIRED:
- Current Backend: Railway (being migrated from)
- New Backend: https://marketedge-platform.onrender.com
- Frontend: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app
- Auth0 Domain: dev-g8trhgbfdq2sk2m8.us.auth0.com

CONFIGURATION CHANGES:
1. Update callback URLs to include Render backend
2. Add Render backend to allowed origins
3. Update logout URLs for Render backend
4. Verify CORS settings for Auth0 integration
"""

import asyncio
import httpx
import json
import time
import sys
import os
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Epic2Auth0ConfigUpdater:
    """Auth0 configuration update automation for Epic 2 migration"""
    
    def __init__(self):
        # CRITICAL: Production URLs post-Epic 2 migration
        self.render_backend_url = "https://marketedge-platform.onrender.com"
        self.frontend_url = "https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
        self.auth0_domain = "dev-g8trhgbfdq2sk2m8.us.auth0.com"
        self.auth0_client_id = "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"
        
        # Auth0 Management API configuration
        # Note: This would require Auth0 Management API token in production
        self.management_api_token = None  # To be set from environment or manual input
        
    def generate_auth0_configuration_update_guide(self) -> str:
        """Generate comprehensive Auth0 configuration update guide"""
        
        guide_content = f"""
# Epic 2 Final Phase: Auth0 Configuration Update Guide
## Railway to Render Migration - Auth0 Settings

Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

## 🎯 MISSION CRITICAL OBJECTIVE
Update Auth0 configuration to support the migrated Render backend while maintaining £925K Odeon demo functionality.

## 📋 CURRENT CONFIGURATION ANALYSIS

### Auth0 Application Details:
- **Domain**: {self.auth0_domain}
- **Client ID**: {self.auth0_client_id}
- **Application Type**: Single Page Application (SPA)

### Migration Details:
- **OLD Backend**: Railway (being deprecated)
- **NEW Backend**: {self.render_backend_url}
- **Frontend**: {self.frontend_url}

## 🔧 REQUIRED CONFIGURATION UPDATES

### 1. Callback URLs Update
**CRITICAL**: Add Render backend callback URLs

#### Current Callback URLs (to verify):
```
https://frontend-5r7ft62po-zebraassociates-projects.vercel.app/callback
http://localhost:3000/callback (development)
```

#### NEW Callback URLs (to add):
```
{self.render_backend_url}/callback
{self.render_backend_url}/api/v1/auth/callback
{self.frontend_url}/callback
{self.frontend_url}/auth/callback
http://localhost:3000/callback
http://localhost:8000/callback (development)
```

### 2. Allowed Logout URLs Update
#### NEW Logout URLs (to add):
```
{self.render_backend_url}/logout
{self.render_backend_url}/api/v1/auth/logout
{self.frontend_url}/logout
{self.frontend_url}/
http://localhost:3000/logout
http://localhost:3000/
```

### 3. Allowed Origins (CORS) Update
#### NEW Origins (to add):
```
{self.render_backend_url}
{self.frontend_url}
http://localhost:3000 (development)
http://localhost:8000 (development)
```

### 4. Allowed Web Origins Update
#### NEW Web Origins (to add):
```
{self.render_backend_url}
{self.frontend_url}
http://localhost:3000 (development)
```

## 🔍 STEP-BY-STEP UPDATE PROCESS

### Step 1: Access Auth0 Dashboard
1. Navigate to: https://manage.auth0.com/
2. Login with appropriate credentials
3. Select the correct tenant: {self.auth0_domain}

### Step 2: Navigate to Application Settings
1. Go to Applications → Applications
2. Find application: "MarketEdge Platform" (Client ID: {self.auth0_client_id})
3. Click on the application name

### Step 3: Update Application Settings

#### 3.1 Application URIs Section:
```
Allowed Callback URLs:
{self.render_backend_url}/callback,
{self.render_backend_url}/api/v1/auth/callback,
{self.frontend_url}/callback,
{self.frontend_url}/auth/callback,
http://localhost:3000/callback,
http://localhost:8000/callback

Allowed Logout URLs:
{self.render_backend_url}/logout,
{self.render_backend_url}/api/v1/auth/logout,
{self.frontend_url}/logout,
{self.frontend_url}/,
http://localhost:3000/logout,
http://localhost:3000/

Allowed Web Origins:
{self.render_backend_url},
{self.frontend_url},
http://localhost:3000

Allowed Origins (CORS):
{self.render_backend_url},
{self.frontend_url},
http://localhost:3000,
http://localhost:8000
```

#### 3.2 Advanced Settings → Grant Types:
Ensure the following grant types are enabled:
- ✅ Authorization Code
- ✅ Refresh Token
- ✅ Implicit (if needed for SPA)

#### 3.3 Advanced Settings → Endpoints:
Verify the following endpoints are accessible:
- Authorization: https://{self.auth0_domain}/authorize
- Token: https://{self.auth0_domain}/oauth/token
- UserInfo: https://{self.auth0_domain}/userinfo

### Step 4: Save Changes
1. Click "Save Changes" at the bottom of the page
2. Wait for confirmation message

### Step 5: Test Configuration
1. Run the CORS testing suite: `python epic2-cors-testing-suite.py`
2. Verify Auth0 URL generation works
3. Test callback handling

## 🧪 VALIDATION CHECKLIST

### Auth0 Configuration Validation:
- [ ] Render backend callback URLs added
- [ ] Frontend callback URLs preserved
- [ ] Logout URLs updated
- [ ] CORS origins include both frontend and backend
- [ ] Web origins properly configured
- [ ] Grant types appropriate for SPA + API
- [ ] Changes saved successfully

### Functional Validation:
- [ ] Auth0 URL generation works from Render backend
- [ ] Frontend can initiate Auth0 login flow
- [ ] Callback handling works on Render backend
- [ ] CORS preflight requests succeed
- [ ] No CORS errors in browser console
- [ ] End-to-end authentication flow functional

## 🚨 CRITICAL SECURITY CONSIDERATIONS

### 1. Production Security:
- Only include production URLs in production Auth0 tenant
- Remove development URLs from production configuration
- Ensure HTTPS-only for all production URLs

### 2. CORS Security:
- Avoid using wildcard (*) origins in production
- Specify exact domains for security
- Validate callback URLs match expected patterns

### 3. Token Security:
- Verify token expiration settings are appropriate
- Ensure refresh token rotation is enabled
- Validate audience claims for API access

## 🔄 ROLLBACK PLAN

If issues occur after configuration update:

### 1. Immediate Rollback:
- Revert callback URLs to pre-migration state
- Remove Render backend URLs temporarily
- Keep only working Railway URLs until resolution

### 2. Gradual Migration:
- Add Render URLs alongside existing URLs
- Test thoroughly before removing Railway URLs
- Monitor for any authentication failures

## 📊 MONITORING AND ALERTS

### Post-Update Monitoring:
1. **Auth0 Dashboard Monitoring**:
   - Login attempts and success rates
   - Failed authentication logs
   - CORS-related errors

2. **Application Monitoring**:
   - Frontend authentication flow success
   - Backend callback processing
   - API access token validation

3. **Alert Conditions**:
   - Authentication failure rate > 5%
   - CORS errors in browser console
   - Callback processing failures

## 🎯 SUCCESS CRITERIA

### Epic 2 Auth0 Migration Success:
- ✅ All callback URLs functional
- ✅ Frontend can authenticate via Auth0
- ✅ Backend can process Auth0 callbacks
- ✅ No CORS errors during authentication
- ✅ £925K Odeon demo authentication works
- ✅ All API endpoints accessible with valid tokens

## 📞 SUPPORT AND ESCALATION

### If Issues Occur:
1. **Immediate**: Revert to previous working configuration
2. **Investigation**: Check Auth0 logs and application logs
3. **Resolution**: Update configuration based on error analysis
4. **Validation**: Re-run testing suite before declaring success

### Contact Information:
- Auth0 Support: https://support.auth0.com/
- Platform Team: (internal escalation)
- Emergency Rollback: Use provided rollback scripts

---

**⚠️ IMPORTANT**: This configuration update is CRITICAL for Epic 2 success.
Ensure all steps are completed and validated before declaring migration complete.

**🎉 GOAL**: Enable seamless authentication for £925K Odeon demo on migrated platform.
"""
        
        return guide_content
    
    def generate_auth0_testing_script(self) -> str:
        """Generate Auth0 specific testing script"""
        
        script_content = f"""#!/usr/bin/env python3
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
    
    backend_url = "{self.render_backend_url}"
    frontend_url = "{self.frontend_url}"
    auth0_domain = "{self.auth0_domain}"
    
    results = {{
        "timestamp": "{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        "tests": [],
        "success": False
    }}
    
    print("🔐 Testing Auth0 Integration with Render Backend")
    print(f"Backend: {{backend_url}}")
    print(f"Frontend: {{frontend_url}}")
    print(f"Auth0: {{auth0_domain}}")
    print("-" * 60)
    
    # Test 1: Auth0 URL Generation
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{{backend_url}}/api/v1/auth/auth0-url",
                params={{
                    "redirect_uri": f"{{frontend_url}}/callback",
                    "state": "test_state_123"
                }},
                headers={{"Origin": frontend_url}}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                auth_url = auth_data.get("auth_url", "")
                
                # Validate Auth0 URL structure
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                
                validations = {{
                    "correct_domain": parsed_url.netloc == auth0_domain,
                    "has_client_id": "client_id" in query_params,
                    "has_redirect_uri": "redirect_uri" in query_params,
                    "has_state": "state" in query_params,
                    "correct_response_type": query_params.get("response_type", [""])[0] == "code"
                }}
                
                all_valid = all(validations.values())
                
                results["tests"].append({{
                    "name": "Auth0 URL Generation",
                    "status": "PASS" if all_valid else "FAIL",
                    "details": {{
                        "auth_url": auth_url,
                        "validations": validations,
                        "has_cors": "access-control-allow-origin" in response.headers
                    }}
                }})
                
                if all_valid:
                    print("✅ Auth0 URL Generation: PASS")
                else:
                    print("❌ Auth0 URL Generation: FAIL")
                    print(f"   Validations: {{validations}}")
            else:
                results["tests"].append({{
                    "name": "Auth0 URL Generation",
                    "status": "FAIL",
                    "error": f"HTTP {{response.status_code}}"
                }})
                print(f"❌ Auth0 URL Generation: FAIL (HTTP {{response.status_code}})")
                
    except Exception as e:
        results["tests"].append({{
            "name": "Auth0 URL Generation",
            "status": "FAIL",
            "error": str(e)
        }})
        print(f"❌ Auth0 URL Generation: FAIL ({{str(e)}})")
    
    # Test 2: Auth0 OpenID Configuration
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"https://{{auth0_domain}}/.well-known/openid_configuration")
            
            if response.status_code == 200:
                config = response.json()
                issuer = config.get("issuer", "")
                
                if issuer == f"https://{{auth0_domain}}/":
                    results["tests"].append({{
                        "name": "Auth0 OpenID Configuration",
                        "status": "PASS",
                        "details": {{
                            "issuer": issuer,
                            "authorization_endpoint": config.get("authorization_endpoint"),
                            "token_endpoint": config.get("token_endpoint")
                        }}
                    }})
                    print("✅ Auth0 OpenID Configuration: PASS")
                else:
                    results["tests"].append({{
                        "name": "Auth0 OpenID Configuration",
                        "status": "FAIL",
                        "error": f"Invalid issuer: {{issuer}}"
                    }})
                    print(f"❌ Auth0 OpenID Configuration: FAIL (Invalid issuer)")
            else:
                results["tests"].append({{
                    "name": "Auth0 OpenID Configuration",
                    "status": "FAIL",
                    "error": f"HTTP {{response.status_code}}"
                }})
                print(f"❌ Auth0 OpenID Configuration: FAIL (HTTP {{response.status_code}})")
                
    except Exception as e:
        results["tests"].append({{
            "name": "Auth0 OpenID Configuration",
            "status": "FAIL",
            "error": str(e)
        }})
        print(f"❌ Auth0 OpenID Configuration: FAIL ({{str(e)}})")
    
    # Test 3: Callback Endpoint CORS
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.options(
                f"{{backend_url}}/api/v1/auth/callback",
                headers={{
                    "Origin": frontend_url,
                    "Access-Control-Request-Method": "GET"
                }}
            )
            
            cors_origin = response.headers.get("access-control-allow-origin")
            has_valid_cors = cors_origin and (cors_origin == frontend_url or cors_origin == "*")
            
            if response.status_code in [200, 204] and has_valid_cors:
                results["tests"].append({{
                    "name": "Callback Endpoint CORS",
                    "status": "PASS",
                    "details": {{
                        "cors_origin": cors_origin,
                        "status_code": response.status_code
                    }}
                }})
                print("✅ Callback Endpoint CORS: PASS")
            else:
                results["tests"].append({{
                    "name": "Callback Endpoint CORS",
                    "status": "FAIL",
                    "details": {{
                        "cors_origin": cors_origin,
                        "status_code": response.status_code,
                        "error": "Invalid CORS configuration"
                    }}
                }})
                print(f"❌ Callback Endpoint CORS: FAIL")
                
    except Exception as e:
        results["tests"].append({{
            "name": "Callback Endpoint CORS",
            "status": "FAIL",
            "error": str(e)
        }})
        print(f"❌ Callback Endpoint CORS: FAIL ({{str(e)}})")
    
    # Calculate overall success
    passed_tests = len([t for t in results["tests"] if t["status"] == "PASS"])
    total_tests = len(results["tests"])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    results["success"] = success_rate >= 100  # All tests must pass
    results["summary"] = {{
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": success_rate
    }}
    
    print("-" * 60)
    print(f"📊 Results: {{passed_tests}}/{{total_tests}} tests passed ({{success_rate:.1f}}%)")
    
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
"""
        
        return script_content
    
    def generate_configuration_summary(self) -> Dict[str, Any]:
        """Generate configuration summary for review"""
        
        summary = {
            "migration_details": {
                "source_platform": "Railway",
                "target_platform": "Render",
                "backend_url": self.render_backend_url,
                "frontend_url": self.frontend_url,
                "auth0_domain": self.auth0_domain,
                "migration_date": time.strftime('%Y-%m-%d', time.gmtime())
            },
            "required_auth0_updates": {
                "callback_urls": [
                    f"{self.render_backend_url}/callback",
                    f"{self.render_backend_url}/api/v1/auth/callback",
                    f"{self.frontend_url}/callback",
                    f"{self.frontend_url}/auth/callback",
                    "http://localhost:3000/callback",
                    "http://localhost:8000/callback"
                ],
                "logout_urls": [
                    f"{self.render_backend_url}/logout",
                    f"{self.render_backend_url}/api/v1/auth/logout",
                    f"{self.frontend_url}/logout",
                    f"{self.frontend_url}/",
                    "http://localhost:3000/logout",
                    "http://localhost:3000/"
                ],
                "allowed_origins": [
                    self.render_backend_url,
                    self.frontend_url,
                    "http://localhost:3000",
                    "http://localhost:8000"
                ],
                "web_origins": [
                    self.render_backend_url,
                    self.frontend_url,
                    "http://localhost:3000"
                ]
            },
            "validation_steps": [
                "Update Auth0 application settings",
                "Save configuration changes",
                "Run CORS testing suite",
                "Validate Auth0 URL generation",
                "Test end-to-end authentication flow",
                "Monitor for CORS errors",
                "Confirm Odeon demo readiness"
            ],
            "critical_success_factors": [
                "No CORS errors during authentication",
                "Successful Auth0 callback processing",
                "Frontend can authenticate users",
                "Backend can validate tokens",
                "£925K Odeon demo fully functional"
            ]
        }
        
        return summary

async def main():
    """Main execution function"""
    print("🔐 Epic 2 Final Phase: Auth0 Configuration Update Automation")
    print("=" * 80)
    
    updater = Epic2Auth0ConfigUpdater()
    
    try:
        # Generate configuration guide
        guide = updater.generate_auth0_configuration_update_guide()
        
        # Generate testing script
        test_script = updater.generate_auth0_testing_script()
        
        # Generate configuration summary
        summary = updater.generate_configuration_summary()
        
        # Save files
        timestamp = int(time.time())
        
        guide_file = f"epic2_auth0_configuration_guide_{timestamp}.md"
        test_file = f"epic2_auth0_testing_script_{timestamp}.py"
        summary_file = f"epic2_auth0_config_summary_{timestamp}.json"
        
        with open(guide_file, 'w') as f:
            f.write(guide)
        
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("📄 Auth0 Configuration Update Guide Generated")
        print(f"📋 Guide saved to: {guide_file}")
        print(f"🧪 Test script saved to: {test_file}")
        print(f"📊 Summary saved to: {summary_file}")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Review the configuration guide")
        print("2. Update Auth0 settings manually via dashboard")
        print("3. Run the testing script to validate changes")
        print("4. Execute comprehensive CORS testing suite")
        
        print("\n✅ Auth0 Configuration Update Package Ready!")
        
    except Exception as e:
        logger.error(f"💥 Auth0 configuration update failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())