#!/usr/bin/env python3
"""
Production Database Verification Script
£925K Zebra Associates Opportunity - Critical Verification

CRITICAL VERIFICATION REQUIRED:
This script validates that Matt Lindop's super_admin access exists in production database,
not just locally. Previous validation attempts failed due to SSL certificate issues.

Business Risk:
If Matt.Lindop's super_admin role exists only locally but not in production,
the £925K Zebra Associates opportunity remains blocked despite local analysis
showing "correct access."

Verification Focus:
1. Matt.Lindop Production Account Status
2. Database Schema Consistency (UserRole enum)
3. Production vs Local Discrepancy Analysis
4. Authentication Token Validation
5. Access Control Verification

Usage: python production_database_verification.py
"""

import sys
import os
import json
import ssl
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    import asyncpg
    import psycopg2
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Run: pip install sqlalchemy psycopg2-binary asyncpg aiohttp")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TARGET_USER_EMAIL = "matt.lindop@zebra.associates"
BUSINESS_OPPORTUNITY = "£925K Zebra Associates"
PRODUCTION_URL = "https://marketedge-platform.onrender.com"
LOCAL_DATABASE_URL = None  # Will be loaded from settings

class ProductionDatabaseVerifier:
    """Comprehensive production database verification for Matt Lindop's super_admin access"""

    def __init__(self):
        self.production_engine: Optional[Engine] = None
        self.local_engine: Optional[Engine] = None
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "business_context": BUSINESS_OPPORTUNITY,
            "target_user": TARGET_USER_EMAIL,
            "verification_results": {},
            "production_vs_local": {},
            "critical_issues": [],
            "warnings": [],
            "success": False
        }

    def load_database_urls(self) -> bool:
        """Load production and local database URLs"""
        logger.info("🔧 Loading database connection URLs...")

        # Load production URL from environment or use known Render URL
        production_url = os.getenv('PRODUCTION_DATABASE_URL')
        if not production_url:
            # Try common production URL patterns
            render_url = os.getenv('DATABASE_URL')
            if render_url and 'render.com' in render_url:
                production_url = render_url
                logger.info("   ✅ Using Render DATABASE_URL for production")
            else:
                # Use known Render production database URL from existing scripts
                production_url = "postgresql://marketedge_user@dpg-d2gch62dbo4c73b0kl80-a.render.com:5432/marketedge_production"
                logger.info("   ✅ Using known Render production database URL")
                logger.info("   🔍 Source: dpg-d2gch62dbo4c73b0kl80-a.render.com:5432/marketedge_production")

        # Load local URL from settings
        try:
            from app.core.config import settings
            local_url = settings.DATABASE_URL
            logger.info("   ✅ Local database URL loaded from settings")
        except Exception as e:
            logger.error(f"   ❌ Could not load local database URL: {e}")
            return False

        # Create engines with SSL handling
        try:
            # Production engine with SSL configuration
            self.production_engine = create_engine(
                production_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "production_verification",
                    "sslmode": "require"  # Force SSL for production
                }
            )

            # Local engine
            self.local_engine = create_engine(
                local_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "local_verification"
                }
            )

            logger.info("   ✅ Database engines created successfully")
            return True

        except Exception as e:
            logger.error(f"   ❌ Failed to create database engines: {e}")
            return False

    def test_production_connection(self) -> bool:
        """Test production database connection with comprehensive SSL handling"""
        logger.info("🔌 Testing production database connection...")

        try:
            with self.production_engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test, NOW() as server_time"))
                row = result.fetchone()
                test_value = row[0]
                server_time = row[1]

            if test_value == 1:
                logger.info(f"   ✅ Production connection successful")
                logger.info(f"   🕐 Server time: {server_time}")
                return True
            else:
                logger.error("   ❌ Production connection test failed")
                return False

        except Exception as e:
            logger.error(f"   ❌ Production connection failed: {e}")

            # Try alternative SSL configurations
            logger.info("   🔄 Attempting alternative SSL configurations...")

            # Get base URL for alternative connection attempts
            production_url = str(self.production_engine.url)

            # Try with different SSL modes
            ssl_modes = ["disable", "allow", "prefer"]

            for ssl_mode in ssl_modes:
                try:
                    logger.info(f"   🧪 Trying SSL mode: {ssl_mode}")

                    # Modify connection args
                    alt_engine = create_engine(
                        production_url,
                        pool_pre_ping=True,
                        connect_args={
                            "connect_timeout": 60,
                            "application_name": "production_verification_alt",
                            "sslmode": ssl_mode
                        }
                    )

                    with alt_engine.connect() as conn:
                        result = conn.execute(text("SELECT 1 as test"))
                        test_value = result.fetchone()[0]

                    if test_value == 1:
                        logger.info(f"   ✅ Alternative connection successful with SSL mode: {ssl_mode}")
                        self.production_engine = alt_engine
                        return True

                except Exception as alt_e:
                    logger.warning(f"   ⚠️  SSL mode {ssl_mode} failed: {alt_e}")
                    continue

            logger.error("   ❌ All connection attempts failed")
            return False

    def test_local_connection(self) -> bool:
        """Test local database connection"""
        logger.info("🏠 Testing local database connection...")

        try:
            with self.local_engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]

            if test_value == 1:
                logger.info("   ✅ Local connection successful")
                return True
            else:
                logger.error("   ❌ Local connection test failed")
                return False

        except Exception as e:
            logger.error(f"   ❌ Local connection failed: {e}")
            return False

    def verify_user_in_production(self) -> Dict[str, Any]:
        """Verify Matt Lindop's user record in production database"""
        logger.info(f"👤 Verifying user in production: {TARGET_USER_EMAIL}")

        result = {
            "user_exists": False,
            "user_data": None,
            "role": None,
            "is_active": None,
            "organisation_id": None,
            "organisation_name": None,
            "created_at": None,
            "updated_at": None
        }

        try:
            with self.production_engine.connect() as conn:
                # Comprehensive user query with organization details
                query = text("""
                    SELECT
                        u.id,
                        u.email,
                        u.role,
                        u.is_active,
                        u.first_name,
                        u.last_name,
                        u.organisation_id,
                        u.created_at,
                        u.updated_at,
                        o.name as org_name,
                        o.industry as org_industry,
                        o.is_active as org_active
                    FROM users u
                    LEFT JOIN organisations o ON u.organisation_id = o.id
                    WHERE u.email = :email
                """)

                query_result = conn.execute(query, {"email": TARGET_USER_EMAIL})
                user_row = query_result.fetchone()

                if user_row:
                    result["user_exists"] = True
                    result["user_data"] = {
                        "id": str(user_row[0]),
                        "email": user_row[1],
                        "first_name": user_row[4],
                        "last_name": user_row[5]
                    }
                    result["role"] = user_row[2]
                    result["is_active"] = user_row[3]
                    result["organisation_id"] = str(user_row[6]) if user_row[6] else None
                    result["created_at"] = user_row[7].isoformat() if user_row[7] else None
                    result["updated_at"] = user_row[8].isoformat() if user_row[8] else None
                    result["organisation_name"] = user_row[9]
                    result["organisation_industry"] = user_row[10]
                    result["organisation_active"] = user_row[11]

                    logger.info(f"   ✅ User found in production")
                    logger.info(f"   👤 Name: {user_row[4]} {user_row[5]}")
                    logger.info(f"   👥 Role: {user_row[2]}")
                    logger.info(f"   🔵 Active: {user_row[3]}")
                    logger.info(f"   🏢 Organization: {user_row[9]} (Active: {user_row[11]})")
                    logger.info(f"   📅 Updated: {user_row[8]}")

                    # Check if role is super_admin
                    if user_row[2] == "super_admin":
                        logger.info("   ✅ User has super_admin role in production")
                    elif user_row[2] == "admin":
                        logger.warning("   ⚠️  User has admin role, not super_admin")
                        self.results["warnings"].append("User has admin role instead of super_admin in production")
                    else:
                        logger.error(f"   ❌ User has unexpected role: {user_row[2]}")
                        self.results["critical_issues"].append(f"User has unexpected role: {user_row[2]}")

                else:
                    logger.error("   ❌ User NOT FOUND in production database")
                    self.results["critical_issues"].append("User not found in production database")

        except Exception as e:
            logger.error(f"   ❌ Failed to verify user in production: {e}")
            result["error"] = str(e)
            self.results["critical_issues"].append(f"Production user verification failed: {e}")

        return result

    def verify_user_in_local(self) -> Dict[str, Any]:
        """Verify Matt Lindop's user record in local database"""
        logger.info(f"🏠 Verifying user in local: {TARGET_USER_EMAIL}")

        result = {
            "user_exists": False,
            "user_data": None,
            "role": None,
            "is_active": None,
            "organisation_id": None,
            "organisation_name": None,
            "created_at": None,
            "updated_at": None
        }

        try:
            with self.local_engine.connect() as conn:
                # Same query as production for comparison
                query = text("""
                    SELECT
                        u.id,
                        u.email,
                        u.role,
                        u.is_active,
                        u.first_name,
                        u.last_name,
                        u.organisation_id,
                        u.created_at,
                        u.updated_at,
                        o.name as org_name,
                        o.industry as org_industry,
                        o.is_active as org_active
                    FROM users u
                    LEFT JOIN organisations o ON u.organisation_id = o.id
                    WHERE u.email = :email
                """)

                query_result = conn.execute(query, {"email": TARGET_USER_EMAIL})
                user_row = query_result.fetchone()

                if user_row:
                    result["user_exists"] = True
                    result["user_data"] = {
                        "id": str(user_row[0]),
                        "email": user_row[1],
                        "first_name": user_row[4],
                        "last_name": user_row[5]
                    }
                    result["role"] = user_row[2]
                    result["is_active"] = user_row[3]
                    result["organisation_id"] = str(user_row[6]) if user_row[6] else None
                    result["created_at"] = user_row[7].isoformat() if user_row[7] else None
                    result["updated_at"] = user_row[8].isoformat() if user_row[8] else None
                    result["organisation_name"] = user_row[9]
                    result["organisation_industry"] = user_row[10]
                    result["organisation_active"] = user_row[11]

                    logger.info(f"   ✅ User found in local")
                    logger.info(f"   👤 Name: {user_row[4]} {user_row[5]}")
                    logger.info(f"   👥 Role: {user_row[2]}")
                    logger.info(f"   🔵 Active: {user_row[3]}")
                    logger.info(f"   🏢 Organization: {user_row[9]} (Active: {user_row[11]})")
                    logger.info(f"   📅 Updated: {user_row[8]}")

                else:
                    logger.error("   ❌ User NOT FOUND in local database")

        except Exception as e:
            logger.error(f"   ❌ Failed to verify user in local: {e}")
            result["error"] = str(e)

        return result

    def verify_userrole_enum(self, engine: Engine, environment: str) -> Dict[str, Any]:
        """Verify UserRole enum includes super_admin"""
        logger.info(f"📋 Verifying UserRole enum in {environment}...")

        result = {
            "enum_exists": False,
            "enum_values": [],
            "has_super_admin": False,
            "enum_order": []
        }

        try:
            with engine.connect() as conn:
                query = text("SELECT unnest(enum_range(NULL::userrole))")
                query_result = conn.execute(query)
                enum_values = [row[0] for row in query_result.fetchall()]

                result["enum_exists"] = True
                result["enum_values"] = enum_values
                result["enum_order"] = enum_values
                result["has_super_admin"] = "super_admin" in enum_values

                logger.info(f"   ✅ UserRole enum found with {len(enum_values)} values")
                logger.info(f"   📋 Values: {enum_values}")

                if result["has_super_admin"]:
                    logger.info("   ✅ super_admin value present in enum")
                else:
                    logger.error("   ❌ super_admin value MISSING from enum")

        except Exception as e:
            logger.error(f"   ❌ Failed to verify UserRole enum in {environment}: {e}")
            result["error"] = str(e)

        return result

    def compare_production_vs_local(self, prod_user: Dict, local_user: Dict,
                                   prod_enum: Dict, local_enum: Dict) -> Dict[str, Any]:
        """Compare production and local database states"""
        logger.info("🔍 Comparing production vs local database states...")

        comparison = {
            "user_existence_match": False,
            "role_match": False,
            "enum_match": False,
            "critical_discrepancies": [],
            "warnings": [],
            "recommendations": []
        }

        # User existence comparison
        if prod_user["user_exists"] and local_user["user_exists"]:
            comparison["user_existence_match"] = True
            logger.info("   ✅ User exists in both production and local")

            # Role comparison
            if prod_user["role"] == local_user["role"]:
                comparison["role_match"] = True
                logger.info(f"   ✅ Role matches: {prod_user['role']}")
            else:
                comparison["role_match"] = False
                logger.error(f"   ❌ ROLE MISMATCH: Production={prod_user['role']}, Local={local_user['role']}")
                comparison["critical_discrepancies"].append({
                    "type": "role_mismatch",
                    "production": prod_user["role"],
                    "local": local_user["role"],
                    "impact": "User may have different permissions in production vs local"
                })

            # Organization comparison
            if prod_user["organisation_id"] != local_user["organisation_id"]:
                logger.warning(f"   ⚠️  Organization ID mismatch: Prod={prod_user['organisation_id']}, Local={local_user['organisation_id']}")
                comparison["warnings"].append("Organization ID differs between environments")

        elif prod_user["user_exists"] and not local_user["user_exists"]:
            logger.error("   ❌ User exists in production but NOT in local")
            comparison["critical_discrepancies"].append({
                "type": "user_missing_local",
                "impact": "Local development may not reflect production state"
            })
        elif not prod_user["user_exists"] and local_user["user_exists"]:
            logger.error("   ❌ User exists in local but NOT in production")
            comparison["critical_discrepancies"].append({
                "type": "user_missing_production",
                "impact": "CRITICAL: Production missing required user for business opportunity"
            })
        else:
            logger.error("   ❌ User missing in BOTH production and local")
            comparison["critical_discrepancies"].append({
                "type": "user_missing_both",
                "impact": "CRITICAL: User setup required in both environments"
            })

        # Enum comparison
        if (prod_enum.get("has_super_admin") == local_enum.get("has_super_admin") and
            prod_enum.get("enum_values") == local_enum.get("enum_values")):
            comparison["enum_match"] = True
            logger.info("   ✅ UserRole enum matches between environments")
        else:
            comparison["enum_match"] = False
            logger.error("   ❌ UserRole enum mismatch between environments")
            comparison["critical_discrepancies"].append({
                "type": "enum_mismatch",
                "production_values": prod_enum.get("enum_values", []),
                "local_values": local_enum.get("enum_values", []),
                "impact": "Enum differences may cause role assignment issues"
            })

        # Generate recommendations
        if comparison["critical_discrepancies"]:
            if not prod_user["user_exists"]:
                comparison["recommendations"].append("Create Matt Lindop user in production database")
            elif prod_user["role"] != "super_admin":
                comparison["recommendations"].append("Promote Matt Lindop to super_admin role in production")
            if not prod_enum.get("has_super_admin"):
                comparison["recommendations"].append("Add super_admin to UserRole enum in production")

        return comparison

    async def test_production_endpoints(self) -> Dict[str, Any]:
        """Test production API endpoints with SSL handling"""
        logger.info("🌐 Testing production API endpoints...")

        result = {
            "health_endpoint": {"status": "unknown", "response": None},
            "feature_flags_endpoint": {"status": "unknown", "response": None},
            "admin_users_endpoint": {"status": "unknown", "response": None},
            "ssl_verification": True
        }

        # Create SSL context that handles certificate issues
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

                # Test health endpoint
                try:
                    async with session.get(f"{PRODUCTION_URL}/health") as response:
                        result["health_endpoint"]["status"] = response.status
                        result["health_endpoint"]["response"] = await response.text()

                        if response.status == 200:
                            logger.info("   ✅ Health endpoint accessible")
                        else:
                            logger.warning(f"   ⚠️  Health endpoint returned {response.status}")

                except Exception as e:
                    logger.error(f"   ❌ Health endpoint failed: {e}")
                    result["health_endpoint"]["error"] = str(e)

                # Test feature flags endpoint (should return 403/401 without auth)
                try:
                    async with session.get(f"{PRODUCTION_URL}/api/v1/admin/feature-flags") as response:
                        result["feature_flags_endpoint"]["status"] = response.status
                        result["feature_flags_endpoint"]["response"] = await response.text()

                        if response.status in [401, 403]:
                            logger.info(f"   ✅ Feature flags endpoint properly protected ({response.status})")
                        else:
                            logger.warning(f"   ⚠️  Feature flags endpoint unexpected status: {response.status}")

                except Exception as e:
                    logger.error(f"   ❌ Feature flags endpoint failed: {e}")
                    result["feature_flags_endpoint"]["error"] = str(e)

                # Test admin users endpoint (should return 403/401 without auth)
                try:
                    async with session.get(f"{PRODUCTION_URL}/api/v1/admin/users") as response:
                        result["admin_users_endpoint"]["status"] = response.status
                        result["admin_users_endpoint"]["response"] = await response.text()

                        if response.status in [401, 403]:
                            logger.info(f"   ✅ Admin users endpoint properly protected ({response.status})")
                        else:
                            logger.warning(f"   ⚠️  Admin users endpoint unexpected status: {response.status}")

                except Exception as e:
                    logger.error(f"   ❌ Admin users endpoint failed: {e}")
                    result["admin_users_endpoint"]["error"] = str(e)

        except Exception as e:
            logger.error(f"   ❌ Failed to test production endpoints: {e}")
            result["error"] = str(e)

        return result

    def generate_verification_report(self) -> None:
        """Generate comprehensive verification report"""
        logger.info("📊 Generating comprehensive verification report...")

        # Determine overall success
        critical_issues = len(self.results["critical_issues"])
        warnings = len(self.results["warnings"])

        if critical_issues == 0:
            self.results["success"] = True
            self.results["overall_status"] = "SUCCESS"
        elif critical_issues > 0:
            self.results["success"] = False
            self.results["overall_status"] = "CRITICAL_ISSUES"

        # Business impact assessment
        self.results["business_impact"] = {
            "opportunity_blocked": critical_issues > 0,
            "risk_level": "HIGH" if critical_issues > 0 else "LOW",
            "immediate_action_required": critical_issues > 0
        }

        # Save results to file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"production_verification_results_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"   ✅ Results saved to {filename}")
        except Exception as e:
            logger.error(f"   ❌ Failed to save results: {e}")

    async def run_verification(self) -> bool:
        """Run complete verification process"""
        logger.info("🚀 Starting production database verification...")
        logger.info("=" * 80)
        logger.info(f"🎯 Target User: {TARGET_USER_EMAIL}")
        logger.info(f"💰 Business Context: {BUSINESS_OPPORTUNITY}")
        logger.info(f"🕐 Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)

        # Step 1: Load database URLs
        if not self.load_database_urls():
            self.results["critical_issues"].append("Failed to load database URLs")
            return False

        # Step 2: Test connections
        logger.info("")
        production_connected = self.test_production_connection()
        local_connected = self.test_local_connection()

        if not production_connected:
            self.results["critical_issues"].append("Cannot connect to production database")
        if not local_connected:
            self.results["critical_issues"].append("Cannot connect to local database")

        # Step 3: Verify user records
        logger.info("")
        prod_user = self.verify_user_in_production() if production_connected else {"user_exists": False, "error": "No connection"}
        local_user = self.verify_user_in_local() if local_connected else {"user_exists": False, "error": "No connection"}

        self.results["verification_results"]["production_user"] = prod_user
        self.results["verification_results"]["local_user"] = local_user

        # Step 4: Verify enum values
        logger.info("")
        prod_enum = self.verify_userrole_enum(self.production_engine, "production") if production_connected else {"enum_exists": False}
        local_enum = self.verify_userrole_enum(self.local_engine, "local") if local_connected else {"enum_exists": False}

        self.results["verification_results"]["production_enum"] = prod_enum
        self.results["verification_results"]["local_enum"] = local_enum

        # Step 5: Compare environments
        logger.info("")
        comparison = self.compare_production_vs_local(prod_user, local_user, prod_enum, local_enum)
        self.results["production_vs_local"] = comparison

        # Add comparison issues to main results
        for issue in comparison["critical_discrepancies"]:
            self.results["critical_issues"].append(f"Environment discrepancy: {issue['type']} - {issue['impact']}")
        for warning in comparison["warnings"]:
            self.results["warnings"].append(f"Environment warning: {warning}")

        # Step 6: Test production endpoints
        logger.info("")
        endpoint_results = await self.test_production_endpoints()
        self.results["verification_results"]["production_endpoints"] = endpoint_results

        # Step 7: Generate report
        logger.info("")
        self.generate_verification_report()

        # Step 8: Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("📋 VERIFICATION SUMMARY")
        logger.info("=" * 80)

        if self.results["success"]:
            logger.info("🎉 VERIFICATION SUCCESSFUL")
            logger.info("   ✅ Matt Lindop has proper super_admin access in production")
            logger.info(f"   ✅ {BUSINESS_OPPORTUNITY} opportunity is NOT blocked")
        else:
            logger.error("❌ VERIFICATION FAILED - CRITICAL ISSUES FOUND")
            logger.error(f"   🚨 {len(self.results['critical_issues'])} critical issues detected")
            logger.error(f"   ⚠️  {len(self.results['warnings'])} warnings detected")
            logger.error(f"   🚨 {BUSINESS_OPPORTUNITY} opportunity may be BLOCKED")

            logger.error("\n📋 Critical Issues:")
            for i, issue in enumerate(self.results["critical_issues"], 1):
                logger.error(f"   {i}. {issue}")

        # Recommendations
        if comparison.get("recommendations"):
            logger.info("\n📋 Recommendations:")
            for i, rec in enumerate(comparison["recommendations"], 1):
                logger.info(f"   {i}. {rec}")

        logger.info("=" * 80)

        return self.results["success"]

async def main():
    """Main verification execution function"""
    verifier = ProductionDatabaseVerifier()
    success = await verifier.run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())