#!/usr/bin/env python3
"""
Fix Default Organization Tool Access

This script ensures that the Default organization has proper tool access 
configured for all available tools. This fixes the 403 Forbidden errors
that new users experience after authentication.

Run this script to:
1. Find or create the Default organization
2. Ensure it has access to all available tools
3. Set up proper UserApplicationAccess records for all users in Default org
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organisation import Organisation, SubscriptionPlan
from app.models.tool import Tool
from app.models.organisation_tool_access import OrganisationToolAccess
from app.models.user import User
from app.models.user_application_access import UserApplicationAccess, ApplicationType
from app.core.rate_limit_config import Industry
from app.core.logging import logger
import uuid


def setup_default_organization_tool_access():
    """Set up tool access for the Default organization"""
    db = next(get_db())
    
    try:
        # 1. Find or create Default organization
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        
        if not default_org:
            logger.info("Creating Default organization")
            default_org = Organisation(
                name="Default", 
                industry=Industry.DEFAULT.value,
                industry_type=Industry.DEFAULT,
                subscription_plan=SubscriptionPlan.basic
            )
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
            logger.info(f"Created Default organization with ID: {default_org.id}")
        else:
            logger.info(f"Found existing Default organization with ID: {default_org.id}")
        
        # 2. Get all available tools
        tools = db.query(Tool).filter(Tool.is_active == True).all()
        logger.info(f"Found {len(tools)} active tools")
        
        if not tools:
            # Create some basic tools if none exist
            logger.info("No tools found, creating basic tools")
            basic_tools = [
                {"name": "Market Edge", "description": "Market analysis and competitive intelligence", "version": "1.0.0"},
                {"name": "Causal Edge", "description": "Causal analysis and insights", "version": "1.0.0"},
                {"name": "Value Edge", "description": "Value proposition analysis", "version": "1.0.0"}
            ]
            
            for tool_data in basic_tools:
                tool = Tool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    version=tool_data["version"],
                    is_active=True
                )
                db.add(tool)
            
            db.commit()
            tools = db.query(Tool).filter(Tool.is_active == True).all()
            logger.info(f"Created {len(tools)} basic tools")
        
        # 3. Set up organization tool access
        tools_configured = 0
        for tool in tools:
            # Check if access already exists
            existing_access = db.query(OrganisationToolAccess).filter(
                OrganisationToolAccess.organisation_id == default_org.id,
                OrganisationToolAccess.tool_id == tool.id
            ).first()
            
            if not existing_access:
                tool_access = OrganisationToolAccess(
                    organisation_id=default_org.id,
                    tool_id=tool.id,
                    subscription_tier="basic",
                    features_enabled=["basic_access", "read_access"],
                    usage_limits={"daily_requests": 100, "monthly_requests": 3000}
                )
                db.add(tool_access)
                tools_configured += 1
                logger.info(f"Added tool access for: {tool.name}")
            else:
                logger.info(f"Tool access already exists for: {tool.name}")
        
        db.commit()
        logger.info(f"Configured tool access for {tools_configured} tools")
        
        # 4. Set up user application access for users in Default organization
        default_org_users = db.query(User).filter(User.organisation_id == default_org.id).all()
        logger.info(f"Found {len(default_org_users)} users in Default organization")
        
        users_configured = 0
        for user in default_org_users:
            # Set up basic application access for each application type
            application_types = [ApplicationType.MARKET_EDGE, ApplicationType.CAUSAL_EDGE, ApplicationType.VALUE_EDGE]
            
            for app_type in application_types:
                existing_access = db.query(UserApplicationAccess).filter(
                    UserApplicationAccess.user_id == user.id,
                    UserApplicationAccess.application == app_type
                ).first()
                
                if not existing_access:
                    user_access = UserApplicationAccess(
                        user_id=user.id,
                        application=app_type,
                        has_access=True,
                        granted_by=user.id  # Self-granted for initial setup
                    )
                    db.add(user_access)
                    users_configured += 1
        
        db.commit()
        logger.info(f"Configured application access for {users_configured} user-application combinations")
        
        # 5. Verification
        verify_setup(db, default_org.id)
        
        logger.info("✅ Default organization tool access setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up default organization tool access: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_setup(db: Session, org_id: uuid.UUID):
    """Verify that the setup was successful"""
    # Check organization tool access
    tool_access_count = db.query(OrganisationToolAccess).filter(
        OrganisationToolAccess.organisation_id == org_id
    ).count()
    
    # Check user application access for users in the organization
    user_access_count = db.query(UserApplicationAccess).join(User).filter(
        User.organisation_id == org_id,
        UserApplicationAccess.has_access == True
    ).count()
    
    tools_count = db.query(Tool).filter(Tool.is_active == True).count()
    users_count = db.query(User).filter(User.organisation_id == org_id).count()
    
    logger.info("=== VERIFICATION RESULTS ===")
    logger.info(f"Organization tool access records: {tool_access_count}")
    logger.info(f"User application access records: {user_access_count}")
    logger.info(f"Total active tools: {tools_count}")
    logger.info(f"Total users in Default org: {users_count}")
    
    if tool_access_count >= tools_count:
        logger.info("✅ Organization tool access: GOOD")
    else:
        logger.warning("⚠️  Organization tool access: INCOMPLETE")
    
    if user_access_count > 0:
        logger.info("✅ User application access: CONFIGURED")
    else:
        logger.warning("⚠️  User application access: NOT CONFIGURED")


if __name__ == "__main__":
    print("🔧 Setting up Default organization tool access...")
    print("This fixes the 403 Forbidden errors after authentication.")
    print()
    
    success = setup_default_organization_tool_access()
    
    if success:
        print()
        print("✅ SUCCESS: Default organization tool access has been configured!")
        print("   New users should now be able to access organization endpoints.")
        print("   Existing users may need to log out and log back in.")
    else:
        print()
        print("❌ FAILED: There was an error setting up tool access.")
        print("   Check the logs for more details.")
        sys.exit(1)