#!/usr/bin/env python3
"""
Fix cross-domain cookie issues between frontend and backend
"""
import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cookie_settings():
    """Test current cookie configuration"""
    logger.info("🔍 TESTING COOKIE CONFIGURATION")
    logger.info("=" * 60)
    
    backend_url = "https://marketedge-platform.onrender.com"
    frontend_url = "https://app.zebra.associates"
    
    logger.info(f"Backend URL: {backend_url}")
    logger.info(f"Frontend URL: {frontend_url}")
    logger.info("")
    
    # Test if cookies can be set cross-domain
    logger.info("Cross-Domain Cookie Issues:")
    logger.info("❌ Backend sets cookies for: marketedge-platform.onrender.com")
    logger.info("❌ Frontend tries to read from: app.zebra.associates")
    logger.info("❌ Browsers block cross-domain cookie access for security")
    logger.info("")
    
    logger.info("SOLUTION OPTIONS:")
    logger.info("1. Use token-based auth (return tokens in response body)")
    logger.info("2. Use same domain for frontend and backend")
    logger.info("3. Use a proxy to make backend appear same-origin")
    logger.info("4. Store tokens in localStorage instead of cookies")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test current cookie behavior
        logger.info("\n" + "=" * 60)
        logger.info("Testing Auth0 login endpoint cookie response...")
        
        # Simulate a login request
        test_data = "code=test_auth_code&redirect_uri=https://app.zebra.associates/callback"
        
        response = await client.post(
            f"{backend_url}/api/v1/auth/login",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": frontend_url
            },
            content=test_data,
            follow_redirects=False
        )
        
        logger.info(f"Response status: {response.status_code}")
        
        # Check Set-Cookie headers
        set_cookie_headers = response.headers.get_list("set-cookie")
        if set_cookie_headers:
            logger.info("\nSet-Cookie headers found:")
            for cookie in set_cookie_headers:
                logger.info(f"  {cookie[:100]}...")
                # Parse cookie attributes
                if "Domain=" in cookie:
                    domain = cookie.split("Domain=")[1].split(";")[0]
                    logger.info(f"    Domain: {domain}")
                else:
                    logger.info(f"    Domain: (not set - defaults to {backend_url.replace('https://', '')})")
                
                if "SameSite=" in cookie:
                    samesite = cookie.split("SameSite=")[1].split(";")[0]
                    logger.info(f"    SameSite: {samesite}")
                
                if "Secure" in cookie:
                    logger.info(f"    Secure: Yes")
        else:
            logger.info("No Set-Cookie headers in response")

def propose_solution():
    """Propose the best solution for the cross-domain cookie issue"""
    logger.info("\n" + "=" * 60)
    logger.info("🎯 RECOMMENDED SOLUTION: Modify Auth Flow")
    logger.info("=" * 60)
    
    logger.info("""
The issue is that cookies cannot be shared between different domains:
- Backend: marketedge-platform.onrender.com
- Frontend: app.zebra.associates

IMMEDIATE FIX: Return tokens in response body instead of cookies

1. Backend changes (/api/v1/auth/login):
   - Still set HTTP-only cookies for same-domain requests
   - ALSO return tokens in response body for cross-domain frontend
   
2. Frontend changes:
   - Store tokens from response body in localStorage or memory
   - Manually add Authorization headers to requests
   - Don't rely on cookies for cross-domain auth

IMPLEMENTATION:
""")
    
    print("""
# Backend: Return tokens in response body
@router.post("/login")
async def login(request: Request, response: Response):
    # ... existing auth logic ...
    
    # Set cookies (for same-domain requests)
    response.set_cookie("access_token", access_token, **cookie_settings)
    
    # ALSO return tokens in body (for cross-domain frontend)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user_data
    }

# Frontend: Store tokens and add to requests
const response = await authService.login(loginData)
// Store tokens in memory or localStorage
localStorage.setItem('access_token', response.access_token)

// Add to API requests
const token = localStorage.getItem('access_token')
config.headers.Authorization = `Bearer ${token}`
""")

async def main():
    logger.info("🚨 CROSS-DOMAIN COOKIE DIAGNOSIS")
    logger.info("Identifying why Auth0 tokens aren't accessible to frontend")
    
    await test_cookie_settings()
    propose_solution()
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 DIAGNOSIS COMPLETE")
    logger.info("""
ROOT CAUSE: Cross-domain cookie restrictions
- Backend domain: marketedge-platform.onrender.com  
- Frontend domain: app.zebra.associates
- Browsers block cross-domain cookie access

SOLUTION: Modify auth flow to return tokens in response body
instead of relying solely on HTTP-only cookies.
""")

if __name__ == "__main__":
    asyncio.run(main())