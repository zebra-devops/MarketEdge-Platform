#!/usr/bin/env python3
"""
EMERGENCY: Set missing JWT environment variables in Render production
This fixes the "Could not validate credentials" 403 errors
"""

import sys
import secrets
import subprocess
import logging
from pathlib import Path

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_secure_jwt_secret():
    """Generate a secure JWT secret key (32+ characters)"""
    return secrets.token_urlsafe(64)  # 64 bytes = 512 bits, more than enough

def generate_env_vars_for_manual_setup():
    """Generate environment variables for manual setup in Render dashboard"""
    logger.info("🔧 Generating JWT environment variables for manual setup...")
    
    # Generate secure JWT secret
    jwt_secret = generate_secure_jwt_secret()
    logger.info(f"Generated secure JWT secret (length: {len(jwt_secret)})")
    
    # Define required environment variables
    env_vars = {
        "JWT_SECRET_KEY": jwt_secret,
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_ISSUER": "market-edge-platform",
        "JWT_AUDIENCE": "market-edge-api"
    }
    
    logger.info("\n📋 ENVIRONMENT VARIABLES TO SET IN RENDER DASHBOARD:")
    logger.info("=" * 60)
    
    for key, value in env_vars.items():
        if 'secret' in key.lower() or 'key' in key.lower():
            logger.info(f"{key}={value}")
            logger.info(f"  ^ Copy this EXACT value for {key}")
        else:
            logger.info(f"{key}={value}")
        logger.info("")
    
    logger.info("=" * 60)
    
    # Save to file for easy copying
    env_file_path = "/Users/matt/Sites/MarketEdge/render_env_vars.txt"
    with open(env_file_path, "w") as f:
        f.write("# RENDER ENVIRONMENT VARIABLES - COPY TO DASHBOARD\n")
        f.write("# Generated: JWT production fix\n\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    logger.info(f"📁 Environment variables saved to: {env_file_path}")
    
    return env_vars

def verify_current_jwt_config():
    """Verify current JWT configuration"""
    logger.info("=== Current JWT Configuration ===")
    
    logger.info(f"JWT_SECRET_KEY: {'SET' if settings.JWT_SECRET_KEY else 'NOT SET'}")
    if settings.JWT_SECRET_KEY:
        logger.info(f"JWT_SECRET_KEY length: {len(settings.JWT_SECRET_KEY)}")
    
    logger.info(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    
    # Check optional JWT settings
    jwt_issuer = getattr(settings, 'JWT_ISSUER', None)
    jwt_audience = getattr(settings, 'JWT_AUDIENCE', None)
    
    logger.info(f"JWT_ISSUER: {jwt_issuer or 'NOT SET'}")
    logger.info(f"JWT_AUDIENCE: {jwt_audience or 'NOT SET'}")

def create_verification_script():
    """Create a script to verify the fix works"""
    verification_script = '''#!/bin/bash
# Verify JWT configuration fix

echo "🔍 Testing API endpoints after JWT fix..."

# Test organization endpoints that were returning 403
endpoints=(
    "/api/v1/organisations/current"
    "/api/v1/organisations/industries" 
    "/api/v1/organisations/accessible"
    "/api/v1/tools/"
)

base_url="https://marketedge-platform.onrender.com"

for endpoint in "${endpoints[@]}"; do
    echo "Testing: $endpoint"
    
    response=$(curl -s -w "\\nHTTP_STATUS:%{http_code}\\n" \\
        -H "Authorization: Bearer test_token_will_be_replaced" \\
        -H "Origin: https://app.zebra.associates" \\
        "$base_url$endpoint")
    
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
    
    if [ "$http_status" = "401" ] || [ "$http_status" = "422" ]; then
        echo "✅ $endpoint: Authentication working (expected 401/422 for test token)"
    elif [ "$http_status" = "403" ]; then
        echo "❌ $endpoint: Still getting 403 - JWT config issue"
    else
        echo "ℹ️  $endpoint: Status $http_status"
    fi
    
    echo "---"
done

echo "🏁 Verification complete!"
echo "If you see 401/422 errors instead of 403, the JWT fix worked!"
'''
    
    with open("/Users/matt/Sites/MarketEdge/verify_jwt_fix.sh", "w") as f:
        f.write(verification_script)
    
    # Make executable
    subprocess.run(["chmod", "+x", "/Users/matt/Sites/MarketEdge/verify_jwt_fix.sh"])
    logger.info("📝 Created verification script: verify_jwt_fix.sh")

def main():
    logger.info("🚨 EMERGENCY JWT PRODUCTION FIX")
    logger.info("=" * 60)
    
    logger.info("Problem: Production missing JWT environment variables")
    logger.info("Symptom: 'Could not validate credentials' 403 errors")
    logger.info("Solution: Set JWT_SECRET_KEY and related config in Render")
    logger.info("")
    
    verify_current_jwt_config()
    logger.info("\n" + "=" * 60)
    
    env_vars = generate_env_vars_for_manual_setup()
    logger.info("\n" + "=" * 60)
    
    create_verification_script()
    logger.info("\n" + "=" * 60)
    
    logger.info("🎯 MANUAL SETUP INSTRUCTIONS:")
    logger.info("1. Go to https://dashboard.render.com")
    logger.info("2. Select your MarketEdge service")
    logger.info("3. Go to Environment tab")
    logger.info("4. Add the environment variables shown above")
    logger.info("5. Click 'Deploy' to trigger redeploy")
    logger.info("")
    logger.info("🕐 TIMELINE:")
    logger.info("- Environment setup: 2-3 minutes")
    logger.info("- Redeploy time: 3-5 minutes")
    logger.info("- Total time to fix: 5-8 minutes")
    logger.info("")
    logger.info("🔍 Expected outcome:")
    logger.info("- 403 'Could not validate credentials' → 401 'Unauthorized' (normal)")
    logger.info("- API endpoints accessible with valid Auth0 tokens")
    logger.info("- Frontend can load organization and tool data")

if __name__ == "__main__":
    main()