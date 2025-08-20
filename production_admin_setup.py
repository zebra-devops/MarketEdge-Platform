#!/usr/bin/env python3
"""
Production Database Admin Setup Script
======================================

This script creates Matt Lindop as a super admin user in the PRODUCTION 
Render PostgreSQL database. It's designed to be run with production 
DATABASE_URL environment variable.

IMPORTANT: This script is specifically for the PRODUCTION database on Render.

Usage:
    export DATABASE_URL="postgresql://render_production_url_here"
    python3 production_admin_setup.py

Environment Variables Required:
    DATABASE_URL: Production PostgreSQL connection string from Render
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'production_admin_setup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class ProductionAdminSetup:
    """Handles creating super admin user in production database"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Configuration
        self.zebra_org_data = {
            'name': 'Zebra Associates',
            'industry': 'Consulting',
            'industry_type': 'DEFAULT',  # Using DEFAULT from Industry enum
            'subscription_plan': 'enterprise',
            'is_active': True,
            'rate_limit_per_hour': 10000,  # High limit for super admin org
            'burst_limit': 1000,
            'rate_limit_enabled': True
        }
        
        self.matt_user_data = {
            'email': 'matt.lindop@zebra.associates',
            'first_name': 'Matt',
            'last_name': 'Lindop',
            'role': 'admin',  # Legacy role (maps to super_admin via hierarchy)
            'is_active': True
        }
        
        self.hierarchy_data = {
            'name': 'Zebra Associates',
            'slug': 'zebra-associates',
            'description': 'Super Admin Organization for Platform Management',
            'level': 'organization',
            'hierarchy_path': 'zebra-associates',
            'depth': 0,
            'is_active': True
        }

    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions with proper transaction handling"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def verify_production_database(self):
        """Verify we're connected to the production database"""
        logger.info("Verifying production database connection...")
        
        try:
            with self.engine.connect() as conn:
                # Get database info
                db_info = conn.execute(text("SELECT current_database(), current_user, version()")).fetchone()
                logger.info(f"✅ Connected to database: {db_info[0]}")
                logger.info(f"   User: {db_info[1]}")
                logger.info(f"   Version: {db_info[2].split(',')[0]}")
                
                # Check if this looks like a production environment
                if "render" in self.database_url.lower() or "railway" in self.database_url.lower():
                    logger.info("✅ Confirmed: This appears to be a production database")
                    return True
                elif "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                    logger.error("❌ SAFETY CHECK: This appears to be a local database!")
                    logger.error("   This script is intended for PRODUCTION use only.")
                    return False
                else:
                    logger.warning("⚠️  Cannot confirm if this is production. Proceeding with caution...")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Database verification failed: {e}")
            return False

    def check_existing_organization(self, session, org_name: str) -> Optional[str]:
        """Check if organization already exists"""
        result = session.execute(
            text("SELECT id FROM organisations WHERE name = :name"),
            {"name": org_name}
        ).fetchone()
        return str(result[0]) if result else None

    def check_existing_user(self, session, email: str) -> Optional[str]:
        """Check if user already exists"""
        result = session.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()
        return str(result[0]) if result else None

    def check_existing_hierarchy(self, session, slug: str) -> Optional[str]:
        """Check if hierarchy node already exists"""
        result = session.execute(
            text("SELECT id FROM organization_hierarchy WHERE slug = :slug"),
            {"slug": slug}
        ).fetchone()
        return str(result[0]) if result else None

    def create_zebra_organization(self, session) -> str:
        """Create Zebra Associates organization"""
        logger.info("Creating Zebra Associates organization in PRODUCTION...")
        
        org_id = str(uuid.uuid4())
        insert_org_sql = text("""
            INSERT INTO organisations (
                id, name, industry, industry_type, subscription_plan, is_active,
                rate_limit_per_hour, burst_limit, rate_limit_enabled, created_at, updated_at
            ) VALUES (
                :id, :name, :industry, :industry_type, :subscription_plan, :is_active,
                :rate_limit_per_hour, :burst_limit, :rate_limit_enabled, :created_at, :updated_at
            )
        """)
        
        session.execute(insert_org_sql, {
            'id': org_id,
            'name': self.zebra_org_data['name'],
            'industry': self.zebra_org_data['industry'],
            'industry_type': self.zebra_org_data['industry_type'],
            'subscription_plan': self.zebra_org_data['subscription_plan'],
            'is_active': self.zebra_org_data['is_active'],
            'rate_limit_per_hour': self.zebra_org_data['rate_limit_per_hour'],
            'burst_limit': self.zebra_org_data['burst_limit'],
            'rate_limit_enabled': self.zebra_org_data['rate_limit_enabled'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"✅ Created organization in PRODUCTION: {self.zebra_org_data['name']} (ID: {org_id})")
        return org_id

    def create_matt_user(self, session, org_id: str) -> str:
        """Create Matt Lindop user"""
        logger.info("Creating Matt Lindop user in PRODUCTION...")
        
        user_id = str(uuid.uuid4())
        insert_user_sql = text("""
            INSERT INTO users (
                id, email, first_name, last_name, organisation_id, role, is_active, created_at, updated_at
            ) VALUES (
                :id, :email, :first_name, :last_name, :organisation_id, :role, :is_active, :created_at, :updated_at
            )
        """)
        
        session.execute(insert_user_sql, {
            'id': user_id,
            'email': self.matt_user_data['email'],
            'first_name': self.matt_user_data['first_name'],
            'last_name': self.matt_user_data['last_name'],
            'organisation_id': org_id,
            'role': self.matt_user_data['role'],
            'is_active': self.matt_user_data['is_active'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"✅ Created user in PRODUCTION: {self.matt_user_data['email']} (ID: {user_id})")
        return user_id

    def create_hierarchy_node(self, session, org_id: str) -> str:
        """Create organization hierarchy node"""
        logger.info("Creating organization hierarchy node in PRODUCTION...")
        
        hierarchy_id = str(uuid.uuid4())
        insert_hierarchy_sql = text("""
            INSERT INTO organization_hierarchy (
                id, name, slug, description, level, hierarchy_path, depth, 
                legacy_organisation_id, is_active, created_at, updated_at
            ) VALUES (
                :id, :name, :slug, :description, :level, :hierarchy_path, :depth,
                :legacy_organisation_id, :is_active, :created_at, :updated_at
            )
        """)
        
        session.execute(insert_hierarchy_sql, {
            'id': hierarchy_id,
            'name': self.hierarchy_data['name'],
            'slug': self.hierarchy_data['slug'],
            'description': self.hierarchy_data['description'],
            'level': self.hierarchy_data['level'],
            'hierarchy_path': self.hierarchy_data['hierarchy_path'],
            'depth': self.hierarchy_data['depth'],
            'legacy_organisation_id': org_id,
            'is_active': self.hierarchy_data['is_active'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"✅ Created hierarchy node in PRODUCTION: {self.hierarchy_data['name']} (ID: {hierarchy_id})")
        return hierarchy_id

    def create_user_hierarchy_assignment(self, session, user_id: str, hierarchy_id: str):
        """Create user hierarchy assignment with super_admin role"""
        logger.info("Creating user hierarchy assignment with super_admin role in PRODUCTION...")
        
        assignment_id = str(uuid.uuid4())
        insert_assignment_sql = text("""
            INSERT INTO user_hierarchy_assignments (
                id, user_id, hierarchy_node_id, role, is_primary, is_active, created_at, updated_at
            ) VALUES (
                :id, :user_id, :hierarchy_node_id, :role, :is_primary, :is_active, :created_at, :updated_at
            )
        """)
        
        session.execute(insert_assignment_sql, {
            'id': assignment_id,
            'user_id': user_id,
            'hierarchy_node_id': hierarchy_id,
            'role': 'super_admin',  # Enhanced role for platform-wide access
            'is_primary': True,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        logger.info(f"✅ Created super_admin hierarchy assignment in PRODUCTION (ID: {assignment_id})")

    def verify_production_setup(self, session, user_id: str):
        """Verify the super admin setup is correct in production"""
        logger.info("Verifying super admin setup in PRODUCTION...")
        
        # Check user exists and has correct organization
        user_check = session.execute(text("""
            SELECT u.email, u.first_name, u.last_name, u.role, o.name as org_name, o.subscription_plan
            FROM users u 
            JOIN organisations o ON u.organisation_id = o.id 
            WHERE u.id = :user_id
        """), {"user_id": user_id}).fetchone()
        
        if user_check:
            logger.info(f"✅ PRODUCTION User verified: {user_check[0]} ({user_check[1]} {user_check[2]})")
            logger.info(f"   Legacy Role: {user_check[3]}")
            logger.info(f"   Organization: {user_check[4]} ({user_check[5]})")
        else:
            raise Exception("❌ PRODUCTION User verification failed")
        
        # Check hierarchy assignment
        hierarchy_check = session.execute(text("""
            SELECT uha.role, oh.name, oh.level, oh.hierarchy_path
            FROM user_hierarchy_assignments uha
            JOIN organization_hierarchy oh ON uha.hierarchy_node_id = oh.id
            WHERE uha.user_id = :user_id AND uha.is_active = true
        """), {"user_id": user_id}).fetchone()
        
        if hierarchy_check:
            logger.info(f"✅ PRODUCTION Hierarchy assignment verified:")
            logger.info(f"   Role: {hierarchy_check[0]}")
            logger.info(f"   Node: {hierarchy_check[1]} ({hierarchy_check[2]})")
            logger.info(f"   Path: {hierarchy_check[3]}")
        else:
            raise Exception("❌ PRODUCTION Hierarchy assignment verification failed")

    def run_production_setup(self):
        """Run the complete production setup"""
        logger.info("=" * 80)
        logger.info("PRODUCTION DATABASE ADMIN SETUP - Matt Lindop Super Admin Creation")
        logger.info("=" * 80)
        logger.info(f"Target Database: PRODUCTION (Render PostgreSQL)")
        logger.info(f"Setup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Verify we're connected to production
        if not self.verify_production_database():
            logger.error("❌ Production database verification failed. Aborting for safety.")
            sys.exit(1)
        
        try:
            with self.get_db_session() as session:
                # Check if organization already exists
                existing_org_id = self.check_existing_organization(session, self.zebra_org_data['name'])
                if existing_org_id:
                    logger.info(f"ℹ️  Organization '{self.zebra_org_data['name']}' already exists in PRODUCTION (ID: {existing_org_id})")
                    org_id = existing_org_id
                else:
                    org_id = self.create_zebra_organization(session)
                
                # Check if user already exists
                existing_user_id = self.check_existing_user(session, self.matt_user_data['email'])
                if existing_user_id:
                    logger.warning(f"⚠️  User '{self.matt_user_data['email']}' already exists in PRODUCTION (ID: {existing_user_id})")
                    logger.info("Skipping user creation but continuing with hierarchy setup...")
                    user_id = existing_user_id
                else:
                    user_id = self.create_matt_user(session, org_id)
                
                # Check if hierarchy node already exists
                existing_hierarchy_id = self.check_existing_hierarchy(session, self.hierarchy_data['slug'])
                if existing_hierarchy_id:
                    logger.info(f"ℹ️  Hierarchy node '{self.hierarchy_data['slug']}' already exists in PRODUCTION (ID: {existing_hierarchy_id})")
                    hierarchy_id = existing_hierarchy_id
                else:
                    hierarchy_id = self.create_hierarchy_node(session, org_id)
                
                # Check if user hierarchy assignment already exists
                existing_assignment = session.execute(text("""
                    SELECT id, role FROM user_hierarchy_assignments 
                    WHERE user_id = :user_id AND hierarchy_node_id = :hierarchy_node_id AND is_active = true
                """), {"user_id": user_id, "hierarchy_node_id": hierarchy_id}).fetchone()
                
                if existing_assignment:
                    logger.info(f"ℹ️  Hierarchy assignment already exists in PRODUCTION (ID: {existing_assignment[0]}, Role: {existing_assignment[1]})")
                    if existing_assignment[1] != 'super_admin':
                        logger.warning(f"⚠️  Existing assignment role is '{existing_assignment[1]}', not 'super_admin'")
                        # Update the assignment to super_admin
                        session.execute(text("""
                            UPDATE user_hierarchy_assignments 
                            SET role = 'super_admin', updated_at = :updated_at
                            WHERE id = :assignment_id
                        """), {"assignment_id": existing_assignment[0], "updated_at": datetime.utcnow()})
                        logger.info("✅ Updated existing assignment to super_admin role")
                else:
                    self.create_user_hierarchy_assignment(session, user_id, hierarchy_id)
                
                # Verify the complete setup
                self.verify_production_setup(session, user_id)
                
                logger.info("=" * 80)
                logger.info("✅ PRODUCTION SUPER ADMIN SETUP COMPLETED SUCCESSFULLY")
                logger.info("=" * 80)
                logger.info(f"Environment: PRODUCTION (Render PostgreSQL)")
                logger.info(f"Organization: {self.zebra_org_data['name']} (ID: {org_id})")
                logger.info(f"User: {self.matt_user_data['email']} (ID: {user_id})")
                logger.info(f"Hierarchy: {self.hierarchy_data['name']} (ID: {hierarchy_id})")
                logger.info("Super Admin Access: GRANTED with super_admin role in PRODUCTION")
                logger.info("=" * 80)
                logger.info("🎉 Matt Lindop now has super admin access in the PRODUCTION database!")
                
        except Exception as e:
            logger.error(f"❌ PRODUCTION setup failed: {e}")
            raise


def get_production_database_url() -> str:
    """Get production database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable is required.")
        logger.error("   Set it to your production PostgreSQL connection string:")
        logger.error("   export DATABASE_URL='postgresql://user:password@host:port/database'")
        sys.exit(1)
    
    # Safety check - ensure this looks like a production URL
    if "localhost" in database_url or "127.0.0.1" in database_url:
        logger.error("❌ SAFETY CHECK FAILED: DATABASE_URL appears to be local!")
        logger.error("   This script is intended for PRODUCTION use only.")
        logger.error(f"   Provided URL: {database_url}")
        sys.exit(1)
    
    return database_url


def main():
    """Main function to run the production setup"""
    try:
        # Get production database URL
        database_url = get_production_database_url()
        logger.info(f"Using PRODUCTION database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
        
        # Confirm this is intentional
        print("\n" + "⚠️" * 20)
        print("WARNING: You are about to modify the PRODUCTION database!")
        print("This will create Matt Lindop as a super admin user.")
        print("⚠️" * 20)
        response = input("\nType 'PRODUCTION' to confirm this is intentional: ")
        
        if response != 'PRODUCTION':
            logger.info("Setup cancelled by user - confirmation not provided")
            sys.exit(0)
        
        # Run production setup
        setup = ProductionAdminSetup(database_url)
        setup.run_production_setup()
        
        print(f"\n🎉 SUCCESS: Matt Lindop has been successfully set up as a super admin in PRODUCTION!")
        print(f"   Email: {setup.matt_user_data['email']}")
        print(f"   Organization: {setup.zebra_org_data['name']}")
        print(f"   Role: super_admin (platform-wide access)")
        print(f"   Environment: PRODUCTION")
        
    except KeyboardInterrupt:
        logger.info("\n❌ Production setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Production setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()