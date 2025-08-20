#!/usr/bin/env python3
"""
CRITICAL: Check for JWT configuration mismatch between local and production
The issue is that tokens created locally fail validation on production
"""

import sys
from pathlib import Path
import logging

# Add app directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.auth.jwt import create_access_token, verify_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_jwt_config():
    """Check JWT configuration that might differ between local and production"""
    logger.info("=== JWT Configuration Analysis ===")
    
    logger.info(f"JWT_SECRET_KEY: {'SET' if settings.JWT_SECRET_KEY else 'NOT SET'}")
    logger.info(f"JWT_SECRET_KEY length: {len(settings.JWT_SECRET_KEY) if settings.JWT_SECRET_KEY else 0}")
    logger.info(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    logger.info(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    
    # Check for JWT issuer and audience settings
    jwt_issuer = getattr(settings, 'JWT_ISSUER', None)
    jwt_audience = getattr(settings, 'JWT_AUDIENCE', None)
    
    logger.info(f"JWT_ISSUER: {jwt_issuer or 'DEFAULT (market-edge-platform)'}")
    logger.info(f"JWT_AUDIENCE: {jwt_audience or 'DEFAULT (market-edge-api)'}")
    
    # Test token creation and verification
    logger.info("\n=== Local Token Test ===")
    
    test_data = {
        "sub": "test-user-12345",
        "email": "test@example.com"
    }
    
    try:
        # Create token with all the claims production would expect
        token = create_access_token(
            data=test_data,
            tenant_id="test-tenant-id",
            user_role="viewer",
            permissions=["read:organizations"],
            industry="default"
        )
        
        logger.info(f"✅ Token created: {token[:100]}...")
        
        # Verify the token
        verified = verify_token(token, expected_type="access")
        if verified:
            logger.info("✅ Token verification: SUCCESS")
            logger.info(f"Payload keys: {list(verified.keys())}")
            logger.info(f"Issuer: {verified.get('iss')}")
            logger.info(f"Audience: {verified.get('aud')}")
            logger.info(f"Type: {verified.get('type')}")
        else:
            logger.error("❌ Token verification: FAILED")
            
    except Exception as e:
        logger.error(f"❌ Token creation/verification failed: {str(e)}")

def check_environment_differences():
    """Check environment-specific settings that might affect JWT"""
    logger.info("\n=== Environment Configuration ===")
    
    logger.info(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    logger.info(f"DEBUG: {settings.DEBUG}")
    logger.info(f"DATABASE_URL: {'SET' if settings.DATABASE_URL else 'NOT SET'}")
    
    # Check all environment variables that might affect JWT
    import os
    jwt_related_vars = [
        'JWT_SECRET_KEY',
        'JWT_ALGORITHM', 
        'JWT_ISSUER',
        'JWT_AUDIENCE',
        'ACCESS_TOKEN_EXPIRE_MINUTES'
    ]
    
    logger.info("\nEnvironment variables:")
    for var in jwt_related_vars:
        value = os.getenv(var)
        if value:
            if 'secret' in var.lower() or 'key' in var.lower():
                logger.info(f"  {var}: SET (length: {len(value)})")
            else:
                logger.info(f"  {var}: {value}")
        else:
            logger.info(f"  {var}: NOT SET")

def analyze_production_token_failure():
    """Analyze why production token validation might be failing"""
    logger.info("\n=== Production Token Failure Analysis ===")
    
    logger.info("Possible causes of 'Could not validate credentials':")
    logger.info("1. JWT_SECRET_KEY mismatch between local and production")
    logger.info("2. JWT_ISSUER/JWT_AUDIENCE settings different")
    logger.info("3. Token expiration handling")
    logger.info("4. Database user lookup failing")
    logger.info("5. Organisation ID validation failing")
    
    logger.info("\nMost likely causes:")
    logger.info("❓ JWT_SECRET_KEY: Production has different secret than local")
    logger.info("❓ JWT_AUDIENCE: Production validates audience, local doesn't")
    logger.info("❓ JWT_ISSUER: Production validates issuer, local doesn't")
    
    logger.info("\nTo fix:")
    logger.info("1. Check production environment variables")
    logger.info("2. Ensure JWT_SECRET_KEY is same in both environments")
    logger.info("3. Verify JWT_ISSUER and JWT_AUDIENCE settings")
    logger.info("4. Test with production-generated token")

def create_debug_token_for_production():
    """Create a token that should work in production"""
    logger.info("\n=== Creating Production-Compatible Token ===")
    
    # Use the exact same configuration that production would use
    test_data = {
        "sub": "686db461-69bd-453f-8c98-4c8680e466fa",  # Real user ID from DB
        "email": "diagnostic@test.com"
    }
    
    try:
        token = create_access_token(
            data=test_data,
            tenant_id="835d4f24-cff2-43e8-a470-93216a3d99a3",  # Real org ID from DB
            user_role="viewer",
            permissions=["read:organizations", "read:market_edge"],
            industry="default"
        )
        
        logger.info("Production-compatible token created:")
        logger.info(f"Bearer {token}")
        logger.info("\nTo test manually:")
        logger.info(f"curl -H 'Authorization: Bearer {token}' \\")
        logger.info("     -H 'Origin: https://app.zebra.associates' \\")
        logger.info("     https://marketedge-platform.onrender.com/api/v1/organisations/current")
        
    except Exception as e:
        logger.error(f"Failed to create production token: {str(e)}")

def main():
    logger.info("🔍 JWT CONFIGURATION MISMATCH ANALYSIS")
    logger.info("=" * 60)
    
    check_jwt_config()
    check_environment_differences()
    analyze_production_token_failure()
    create_debug_token_for_production()
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 JWT analysis complete!")

if __name__ == "__main__":
    main()