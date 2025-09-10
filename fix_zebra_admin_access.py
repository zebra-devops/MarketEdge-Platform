#!/usr/bin/env python3
"""
EMERGENCY FIX: Zebra Associates Admin Access

This script will:
1. Ensure matt.lindop@zebra.associates exists in the database
2. Grant admin role to the user
3. Activate the user account
4. Verify the fix works

CRITICAL: This is for the £925K Zebra Associates opportunity
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Optional

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text, select
    import uuid
    import bcrypt
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("   Run: pip install sqlalchemy[asyncio] bcrypt")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZebraAdminFixer:
    """Fix admin access for Zebra Associates"""
    
    def __init__(self):
        self.zebra_email = "matt.lindop@zebra.associates"
        self.zebra_org_name = "Zebra Associates"
        
        # Environment-based database URL
        self.database_url = os.getenv("DATABASE_URL", 
            "postgresql+asyncpg://postgres:password@localhost:5432/marketedge")
        
        logger.info(f"🎯 Target: {self.zebra_email}")
        logger.info(f"💼 Organisation: {self.zebra_org_name}")
    
    async def fix_admin_access(self):
        """Main fix function"""
        logger.info("🚀 Starting Zebra Associates admin access fix...")
        
        try:
            # Create async engine
            engine = create_async_engine(self.database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            async with async_session() as session:
                # Step 1: Check if Zebra Associates organisation exists
                org_id = await self.ensure_zebra_organisation(session)
                
                # Step 2: Check if user exists
                user_id = await self.ensure_zebra_user(session, org_id)
                
                # Step 3: Ensure user has admin role
                await self.ensure_admin_role(session, user_id)
                
                # Step 4: Verify the fix
                await self.verify_fix(session, user_id)
                
                await session.commit()
                logger.info("✅ All fixes committed to database")
                
            await engine.dispose()
            
            logger.info("🎉 Zebra Associates admin access fix completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix admin access: {e}")
            return False
    
    async def ensure_zebra_organisation(self, session: AsyncSession) -> str:
        """Ensure Zebra Associates organisation exists"""
        logger.info("🏢 Checking Zebra Associates organisation...")
        
        # Check if organisation exists
        result = await session.execute(text("""
            SELECT id, name, subscription_plan 
            FROM organisations 
            WHERE name ILIKE :org_name OR email_domain ILIKE '%zebra.associates%'
        """), {"org_name": f"%{self.zebra_org_name}%"})
        
        org_data = result.fetchone()
        
        if org_data:
            logger.info(f"✅ Organisation found: {org_data.name} (ID: {org_data.id})")
            return str(org_data.id)
        else:
            # Create organisation
            org_id = str(uuid.uuid4())
            await session.execute(text("""
                INSERT INTO organisations (
                    id, name, email_domain, subscription_plan, 
                    is_active, created_at, updated_at
                ) VALUES (
                    :org_id, :name, 'zebra.associates', 'enterprise',
                    true, NOW(), NOW()
                )
            """), {
                "org_id": org_id,
                "name": self.zebra_org_name
            })
            
            logger.info(f"✅ Created organisation: {self.zebra_org_name} (ID: {org_id})")
            return org_id
    
    async def ensure_zebra_user(self, session: AsyncSession, org_id: str) -> str:
        """Ensure matt.lindop@zebra.associates user exists"""
        logger.info("👤 Checking Zebra Associates user...")
        
        # Check if user exists
        result = await session.execute(text("""
            SELECT id, email, role, is_active, organisation_id
            FROM users 
            WHERE email = :email
        """), {"email": self.zebra_email})
        
        user_data = result.fetchone()
        
        if user_data:
            logger.info(f"✅ User found: {user_data.email} (ID: {user_data.id})")
            
            # Update organisation if needed
            if str(user_data.organisation_id) != org_id:
                await session.execute(text("""
                    UPDATE users SET organisation_id = :org_id, updated_at = NOW()
                    WHERE id = :user_id
                """), {
                    "org_id": org_id,
                    "user_id": user_data.id
                })
                logger.info("🔄 Updated user organisation")
            
            return str(user_data.id)
        else:
            # Create user
            user_id = str(uuid.uuid4())
            
            # Generate a secure password hash (user will need to reset)
            password_hash = bcrypt.hashpw("TempPassword123!".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            await session.execute(text("""
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name,
                    role, organisation_id, is_active, email_verified,
                    created_at, updated_at
                ) VALUES (
                    :user_id, :email, :password_hash, 'Matt', 'Lindop',
                    'admin', :org_id, true, true,
                    NOW(), NOW()
                )
            """), {
                "user_id": user_id,
                "email": self.zebra_email,
                "password_hash": password_hash,
                "org_id": org_id
            })
            
            logger.info(f"✅ Created user: {self.zebra_email} (ID: {user_id})")
            logger.info("⚠️  Temporary password: TempPassword123! (user should reset)")
            return user_id
    
    async def ensure_admin_role(self, session: AsyncSession, user_id: str):
        """Ensure user has admin role and is active"""
        logger.info("🔐 Ensuring admin role...")
        
        # Update user to admin role and ensure active
        await session.execute(text("""
            UPDATE users 
            SET role = 'admin', is_active = true, updated_at = NOW()
            WHERE id = :user_id
        """), {"user_id": user_id})
        
        logger.info("✅ User granted admin role and activated")
    
    async def verify_fix(self, session: AsyncSession, user_id: str):
        """Verify the fix works"""
        logger.info("🔍 Verifying fix...")
        
        result = await session.execute(text("""
            SELECT u.id, u.email, u.role, u.is_active, o.name as org_name
            FROM users u
            JOIN organisations o ON u.organisation_id = o.id
            WHERE u.id = :user_id
        """), {"user_id": user_id})
        
        user_data = result.fetchone()
        
        if user_data and user_data.role == 'admin' and user_data.is_active:
            logger.info("✅ Fix verified successfully!")
            logger.info(f"   👤 User: {user_data.email}")
            logger.info(f"   🏢 Organisation: {user_data.org_name}")
            logger.info(f"   🔐 Role: {user_data.role}")
            logger.info(f"   ✅ Active: {user_data.is_active}")
            return True
        else:
            logger.error("❌ Fix verification failed!")
            return False

async def main():
    """Main execution function"""
    print("🚨 EMERGENCY FIX: Zebra Associates Admin Access")
    print("=" * 50)
    print("This will fix admin access for matt.lindop@zebra.associates")
    print("CRITICAL: £925K Zebra Associates opportunity")
    print()
    
    # Confirm execution
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        pass  # Auto-confirm
    else:
        response = input("Continue? (yes/no): ").lower().strip()
        if response != 'yes':
            print("❌ Aborted")
            return
    
    fixer = ZebraAdminFixer()
    success = await fixer.fix_admin_access()
    
    if success:
        print("\n🎉 SUCCESS: Admin access fix completed!")
        print(f"📧 {fixer.zebra_email} now has admin access")
        print("🔐 User can now access admin dashboard")
        print("⚠️  User may need to log out and log back in")
    else:
        print("\n❌ FAILED: Fix could not be completed")
        print("📞 Contact development team immediately")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())