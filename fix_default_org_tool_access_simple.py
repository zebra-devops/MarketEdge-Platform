#!/usr/bin/env python3
"""
Simple Fix for Default Organization Tool Access

This script focuses only on setting up organization tool access 
for the Default organization, which is the main cause of 403 errors.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organisation import Organisation, SubscriptionPlan
from app.models.tool import Tool
from app.models.organisation_tool_access import OrganisationToolAccess
from app.core.rate_limit_config import Industry
from app.core.logging import logger


def fix_default_organization():
    """Fix the Default organization tool access"""
    db = next(get_db())
    
    try:
        # 1. Find Default organization
        default_org = db.query(Organisation).filter(Organisation.name == "Default").first()
        
        if not default_org:
            print("❌ No Default organization found")
            return False
            
        print(f"✅ Found Default organization: {default_org.id}")
        
        # 2. Get all tools
        tools = db.query(Tool).filter(Tool.is_active == True).all()
        print(f"✅ Found {len(tools)} active tools")
        
        # 3. Check current tool access
        existing_access = db.query(OrganisationToolAccess).filter(
            OrganisationToolAccess.organisation_id == default_org.id
        ).all()
        
        print(f"✅ Default org currently has access to {len(existing_access)} tools")
        
        # 4. Set up missing tool access
        tools_added = 0
        for tool in tools:
            has_access = any(access.tool_id == tool.id for access in existing_access)
            
            if not has_access:
                tool_access = OrganisationToolAccess(
                    organisation_id=default_org.id,
                    tool_id=tool.id,
                    subscription_tier="basic",
                    features_enabled=["basic_access", "read_access"],
                    usage_limits={"daily_requests": 100, "monthly_requests": 3000}
                )
                db.add(tool_access)
                tools_added += 1
                print(f"   ➕ Added access for: {tool.name}")
            else:
                print(f"   ✅ Already has access to: {tool.name}")
        
        db.commit()
        
        if tools_added > 0:
            print(f"✅ Added tool access for {tools_added} tools")
        else:
            print("✅ All tools already have access configured")
            
        # 5. Final verification
        final_access = db.query(OrganisationToolAccess).filter(
            OrganisationToolAccess.organisation_id == default_org.id
        ).count()
        
        print(f"✅ Final verification: Default org now has access to {final_access} tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Fixing Default organization tool access...")
    print()
    
    success = fix_default_organization()
    
    if success:
        print()
        print("✅ SUCCESS: Default organization now has proper tool access!")
        print("   Users should now be able to access /api/v1/tools/ and other org endpoints.")
    else:
        print()
        print("❌ FAILED: Could not fix the Default organization.")
        sys.exit(1)