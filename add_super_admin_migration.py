#!/usr/bin/env python3
"""
Database Migration Script: Add Matt Lindop as Super Admin
=========================================================

This script adds Matt Lindop (matt.lindop@zebra.associates) as a super admin user
in the MarketEdge platform database with proper hierarchical organization setup.

Prerequisites:
- PostgreSQL database access via DATABASE_URL environment variable
- All required dependencies installed (psycopg2, sqlalchemy, etc.)

Usage:
    python add_super_admin_migration.py

Environment Variables Required:
    DATABASE_URL: PostgreSQL connection string for production database
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'super_admin_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class SuperAdminMigration:
    """Handles the migration to add super admin user and organization"""
    
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
        logger.info("Creating Zebra Associates organization...")
        
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
        
        logger.info(f"✅ Created organization: {self.zebra_org_data['name']} (ID: {org_id})")
        return org_id

    def create_matt_user(self, session, org_id: str) -> str:
        """Create Matt Lindop user"""
        logger.info("Creating Matt Lindop user...")
        
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
        
        logger.info(f"✅ Created user: {self.matt_user_data['email']} (ID: {user_id})")
        return user_id

    def create_hierarchy_node(self, session, org_id: str) -> str:
        """Create organization hierarchy node"""
        logger.info("Creating organization hierarchy node...")
        
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
        
        logger.info(f"✅ Created hierarchy node: {self.hierarchy_data['name']} (ID: {hierarchy_id})")
        return hierarchy_id

    def create_user_hierarchy_assignment(self, session, user_id: str, hierarchy_id: str):
        """Create user hierarchy assignment with super_admin role"""
        logger.info("Creating user hierarchy assignment...")
        
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
        
        logger.info(f"✅ Created hierarchy assignment with super_admin role (ID: {assignment_id})")

    def verify_setup(self, session, user_id: str):
        """Verify the super admin setup is correct"""
        logger.info("Verifying super admin setup...")
        
        # Check user exists and has correct organization
        user_check = session.execute(text("""
            SELECT u.email, u.first_name, u.last_name, u.role, o.name as org_name
            FROM users u 
            JOIN organisations o ON u.organisation_id = o.id 
            WHERE u.id = :user_id
        """), {"user_id": user_id}).fetchone()
        
        if user_check:
            logger.info(f"✅ User verified: {user_check[0]} ({user_check[1]} {user_check[2]}) "
                       f"- Role: {user_check[3]} - Org: {user_check[4]}")
        else:
            raise Exception("❌ User verification failed")
        
        # Check hierarchy assignment
        hierarchy_check = session.execute(text("""
            SELECT uha.role, oh.name, oh.level
            FROM user_hierarchy_assignments uha
            JOIN organization_hierarchy oh ON uha.hierarchy_node_id = oh.id
            WHERE uha.user_id = :user_id AND uha.is_active = true
        """), {"user_id": user_id}).fetchone()
        
        if hierarchy_check:
            logger.info(f"✅ Hierarchy assignment verified: {hierarchy_check[0]} role "
                       f"in {hierarchy_check[1]} ({hierarchy_check[2]})")
        else:
            raise Exception("❌ Hierarchy assignment verification failed")

    def run_migration(self):
        """Run the complete migration"""
        logger.info("=" * 60)
        logger.info("STARTING SUPER ADMIN MIGRATION")
        logger.info("=" * 60)
        
        try:
            with self.get_db_session() as session:
                # Check if organization already exists
                existing_org_id = self.check_existing_organization(session, self.zebra_org_data['name'])
                if existing_org_id:
                    logger.info(f"ℹ️  Organization '{self.zebra_org_data['name']}' already exists (ID: {existing_org_id})")
                    org_id = existing_org_id
                else:
                    org_id = self.create_zebra_organization(session)
                
                # Check if user already exists
                existing_user_id = self.check_existing_user(session, self.matt_user_data['email'])
                if existing_user_id:
                    logger.warning(f"⚠️  User '{self.matt_user_data['email']}' already exists (ID: {existing_user_id})")
                    logger.info("Skipping user creation but continuing with hierarchy setup...")
                    user_id = existing_user_id
                else:
                    user_id = self.create_matt_user(session, org_id)
                
                # Check if hierarchy node already exists
                existing_hierarchy_id = self.check_existing_hierarchy(session, self.hierarchy_data['slug'])
                if existing_hierarchy_id:
                    logger.info(f"ℹ️  Hierarchy node '{self.hierarchy_data['slug']}' already exists (ID: {existing_hierarchy_id})")
                    hierarchy_id = existing_hierarchy_id
                else:
                    hierarchy_id = self.create_hierarchy_node(session, org_id)
                
                # Check if user hierarchy assignment already exists
                existing_assignment = session.execute(text("""
                    SELECT id FROM user_hierarchy_assignments 
                    WHERE user_id = :user_id AND hierarchy_node_id = :hierarchy_node_id
                """), {"user_id": user_id, "hierarchy_node_id": hierarchy_id}).fetchone()
                
                if existing_assignment:
                    logger.info(f"ℹ️  Hierarchy assignment already exists (ID: {existing_assignment[0]})")
                else:
                    self.create_user_hierarchy_assignment(session, user_id, hierarchy_id)
                
                # Verify the complete setup
                self.verify_setup(session, user_id)
                
                logger.info("=" * 60)
                logger.info("✅ SUPER ADMIN MIGRATION COMPLETED SUCCESSFULLY")
                logger.info("=" * 60)
                logger.info(f"Organization: {self.zebra_org_data['name']} (ID: {org_id})")
                logger.info(f"User: {self.matt_user_data['email']} (ID: {user_id})")
                logger.info(f"Hierarchy: {self.hierarchy_data['name']} (ID: {hierarchy_id})")
                logger.info("Super Admin Access: GRANTED with super_admin role")
                logger.info("=" * 60)
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


def get_database_url() -> str:
    """Get database URL from environment variables"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Try alternative environment variable names
        database_url = os.getenv('POSTGRES_URL') or os.getenv('POSTGRESQL_URL')
    
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it to your PostgreSQL connection string: "
            "postgresql://user:password@host:port/database"
        )
    
    return database_url


def test_database_connection(database_url: str) -> bool:
    """Test database connection before running migration"""
    logger.info("Testing database connection...")
    try:
        engine = create_engine(database_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version_info = result.fetchone()[0]
            logger.info(f"✅ Database connection successful")
            logger.info(f"PostgreSQL version: {version_info.split(',')[0]}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def main():
    """Main function to run the migration"""
    try:
        # Get database URL
        database_url = get_database_url()
        logger.info(f"Using database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
        
        # Test connection
        if not test_database_connection(database_url):
            logger.error("❌ Cannot proceed without database connection")
            sys.exit(1)
        
        # Confirm production migration
        if "render.com" in database_url or "railway" in database_url:
            response = input("\n⚠️  This appears to be a PRODUCTION database. Continue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                logger.info("Migration cancelled by user")
                sys.exit(0)
        
        # Run migration
        migration = SuperAdminMigration(database_url)
        migration.run_migration()
        
        logger.info("\n🎉 Matt Lindop has been successfully added as a super admin!")
        logger.info(f"   Email: {migration.matt_user_data['email']}")
        logger.info(f"   Organization: {migration.zebra_org_data['name']}")
        logger.info(f"   Role: super_admin (platform-wide access)")
        
    except KeyboardInterrupt:
        logger.info("\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()