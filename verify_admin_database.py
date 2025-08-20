#!/usr/bin/env python3
"""
Database Verification Script: Check which database has Matt Lindop's admin privileges
====================================================================================

This script checks both local and production databases to determine where
Matt Lindop's admin privileges were actually applied.
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class DatabaseVerifier:
    """Verifies admin user setup across different database environments"""
    
    def __init__(self):
        self.matt_email = 'matt.lindop@zebra.associates'
        
    def test_connection(self, database_url: str, env_name: str) -> bool:
        """Test database connection"""
        try:
            logger.info(f"Testing {env_name} database connection...")
            engine = create_engine(database_url, echo=False)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version_info = result.fetchone()[0]
                logger.info(f"✅ {env_name} database connection successful")
                logger.info(f"   PostgreSQL version: {version_info.split(',')[0]}")
                return True
        except Exception as e:
            logger.error(f"❌ {env_name} database connection failed: {e}")
            return False
    
    def check_matt_admin_status(self, database_url: str, env_name: str):
        """Check Matt Lindop's admin status in the specified database"""
        logger.info(f"\n--- Checking {env_name} Database ---")
        
        if not self.test_connection(database_url, env_name):
            return None
            
        try:
            engine = create_engine(database_url, echo=False)
            Session = sessionmaker(bind=engine)
            
            with Session() as session:
                # Check if Matt Lindop exists in users table
                user_result = session.execute(text("""
                    SELECT u.id, u.email, u.first_name, u.last_name, u.role, u.is_active,
                           o.name as org_name, o.subscription_plan
                    FROM users u 
                    LEFT JOIN organisations o ON u.organisation_id = o.id 
                    WHERE u.email = :email
                """), {"email": self.matt_email}).fetchone()
                
                if user_result:
                    logger.info(f"✅ User found in {env_name} database:")
                    logger.info(f"   ID: {user_result[0]}")
                    logger.info(f"   Email: {user_result[1]}")
                    logger.info(f"   Name: {user_result[2]} {user_result[3]}")
                    logger.info(f"   Legacy Role: {user_result[4]}")
                    logger.info(f"   Active: {user_result[5]}")
                    logger.info(f"   Organization: {user_result[6] or 'None'}")
                    logger.info(f"   Subscription: {user_result[7] or 'None'}")
                    
                    user_id = user_result[0]
                    
                    # Check hierarchy assignments
                    hierarchy_result = session.execute(text("""
                        SELECT uha.id, uha.role, uha.is_primary, uha.is_active,
                               oh.name, oh.level, oh.hierarchy_path
                        FROM user_hierarchy_assignments uha
                        JOIN organization_hierarchy oh ON uha.hierarchy_node_id = oh.id
                        WHERE uha.user_id = :user_id
                    """), {"user_id": user_id}).fetchall()
                    
                    if hierarchy_result:
                        logger.info(f"   Hierarchy Assignments ({len(hierarchy_result)}):")
                        for assignment in hierarchy_result:
                            logger.info(f"     - Role: {assignment[1]} | Primary: {assignment[2]} | Active: {assignment[3]}")
                            logger.info(f"       Node: {assignment[4]} ({assignment[5]}) | Path: {assignment[6]}")
                    else:
                        logger.warning(f"   ⚠️  No hierarchy assignments found")
                        
                    return {
                        'exists': True,
                        'user_id': user_id,
                        'legacy_role': user_result[4],
                        'organization': user_result[6],
                        'hierarchy_assignments': len(hierarchy_result),
                        'has_super_admin': any(h[1] == 'super_admin' for h in hierarchy_result)
                    }
                else:
                    logger.warning(f"❌ User NOT found in {env_name} database")
                    return {'exists': False}
                    
        except Exception as e:
            logger.error(f"❌ Error checking {env_name} database: {e}")
            return None
    
    def get_database_urls(self):
        """Get database URLs for different environments"""
        urls = {}
        
        # Local development database (from backend .env)
        local_url = "postgresql://platform_user:platform_password@localhost:5432/platform_wrapper"
        urls['local'] = local_url
        
        # Production database (would be set in Render environment)
        prod_url = os.getenv('DATABASE_URL')
        if prod_url:
            urls['production'] = prod_url
        else:
            logger.warning("⚠️  Production DATABASE_URL not set in current environment")
        
        return urls
    
    def run_verification(self):
        """Run complete verification across environments"""
        logger.info("=" * 80)
        logger.info("DATABASE ADMIN VERIFICATION - Matt Lindop Admin Status Check")
        logger.info("=" * 80)
        logger.info(f"Target User: {self.matt_email}")
        logger.info(f"Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        urls = self.get_database_urls()
        results = {}
        
        for env_name, database_url in urls.items():
            results[env_name] = self.check_matt_admin_status(database_url, env_name)
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        
        admin_found = False
        for env_name, result in results.items():
            if result and result.get('exists'):
                admin_found = True
                has_super_admin = result.get('has_super_admin', False)
                logger.info(f"✅ {env_name.upper()} Database: User exists with {'SUPER_ADMIN' if has_super_admin else 'LEGACY ADMIN'} privileges")
                
                if not has_super_admin:
                    logger.warning(f"   ⚠️  ATTENTION: User exists but lacks super_admin hierarchy assignment!")
            else:
                logger.info(f"❌ {env_name.upper()} Database: User not found or connection failed")
        
        if not admin_found:
            logger.error("❌ CRITICAL: Matt Lindop not found in any accessible database!")
            logger.error("   This means the admin upgrade may not have been applied to production.")
            
        logger.info("=" * 80)
        
        return results

def main():
    """Main function"""
    try:
        verifier = DatabaseVerifier()
        results = verifier.run_verification()
        
        # Determine next steps
        production_result = results.get('production')
        local_result = results.get('local')
        
        print("\n" + "🔍 ANALYSIS & RECOMMENDATIONS:")
        print("=" * 50)
        
        if local_result and local_result.get('exists'):
            print("✅ Admin user found in LOCAL database")
            if not (production_result and production_result.get('exists')):
                print("⚠️  ISSUE: Admin user NOT found in production database")
                print("💡 RECOMMENDATION: Run production admin setup script")
        else:
            print("❌ Admin user not found in local database")
            
        if production_result and production_result.get('exists'):
            print("✅ Admin user found in PRODUCTION database")
            if not production_result.get('has_super_admin'):
                print("⚠️  ISSUE: Production user lacks super_admin privileges")
                print("💡 RECOMMENDATION: Update production hierarchy assignments")
        elif 'production' in results:
            print("❌ Cannot access or user not found in production database")
            print("💡 RECOMMENDATION: Create production admin setup script")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()