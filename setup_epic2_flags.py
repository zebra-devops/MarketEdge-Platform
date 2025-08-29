#!/usr/bin/env python3
"""
Epic 2 Feature Flag Setup Script

Creates the initial feature flags needed for Epic 2: Feature Flag Control System
deployment with progressive rollout configuration.
"""

import asyncio
import sys
import uuid
from typing import List, Dict, Any

# Add backend to path
sys.path.append('/Users/matt/Sites/MarketEdge/platform-wrapper/backend')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_async_db
from app.models.feature_flags import FeatureFlag, FeatureFlagScope, FeatureFlagStatus
from app.services.feature_flag_service import FeatureFlagService


async def setup_epic2_feature_flags():
    """Setup feature flags for Epic 2 deployment"""
    print("🚀 Setting up Epic 2: Feature Flag Control System")
    print("=" * 50)
    
    # Epic 2 feature flags for progressive rollout (5%)
    epic2_flags = [
        {
            "flag_key": "show_placeholder_content",
            "name": "Show Placeholder Content",
            "description": "Display placeholder content when real data is unavailable",
            "is_enabled": True,
            "rollout_percentage": 5,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "rollout_percentage": 5,
                "deployment": "epic2",
                "priority": "high"
            }
        },
        {
            "flag_key": "demo_mode",
            "name": "Demo Mode",
            "description": "Enable demo mode with safe test data for new users",
            "is_enabled": True,
            "rollout_percentage": 5,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "rollout_percentage": 5,
                "deployment": "epic2",
                "priority": "high",
                "demo_data_enabled": True
            }
        },
        {
            "flag_key": "live_data_enabled",
            "name": "Live Data Enabled",
            "description": "Enable live data connections (disabled for initial rollout)",
            "is_enabled": False,
            "rollout_percentage": 0,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "rollout_percentage": 0,
                "deployment": "epic2",
                "priority": "medium",
                "requires_approval": True
            }
        },
        {
            "flag_key": "modules.market_edge.enabled",
            "name": "MarketEdge Module",
            "description": "Enable the MarketEdge analytics module",
            "is_enabled": True,
            "rollout_percentage": 5,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "rollout_percentage": 5,
                "deployment": "epic2",
                "priority": "high",
                "module_id": "market_edge"
            }
        },
        {
            "flag_key": "modules.enhanced_ui.enabled", 
            "name": "Enhanced UI Components",
            "description": "Enable enhanced user interface components",
            "is_enabled": True,
            "rollout_percentage": 5,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "rollout_percentage": 5,
                "deployment": "epic2",
                "priority": "medium",
                "ui_version": "2.0"
            }
        }
    ]
    
    try:
        # Get database session
        async_db_gen = get_async_db()
        db_session: AsyncSession = await anext(async_db_gen)
        
        print(f"📊 Creating {len(epic2_flags)} feature flags...")
        
        # Clear existing flags to ensure clean Epic 2 deployment
        await db_session.execute(delete(FeatureFlag))
        
        # Create new flags
        created_flags = []
        for flag_data in epic2_flags:
            # Create feature flag instance
            feature_flag = FeatureFlag(
                id=str(uuid.uuid4()),
                flag_key=flag_data["flag_key"],
                name=flag_data["name"], 
                description=flag_data["description"],
                is_enabled=flag_data["is_enabled"],
                rollout_percentage=flag_data["rollout_percentage"],
                scope=flag_data["scope"],
                status=flag_data["status"],
                config=flag_data["config"],
                allowed_sectors=[],
                blocked_sectors=[],
                created_by="epic2_deployment"
            )
            
            db_session.add(feature_flag)
            created_flags.append(feature_flag)
        
        # Commit changes
        await db_session.commit()
        
        print("✅ Feature flags created successfully!")
        print("\n📋 Epic 2 Feature Flag Status:")
        print("-" * 30)
        
        for flag in created_flags:
            status = f"ENABLED ({flag.rollout_percentage}%)" if flag.is_enabled else "DISABLED"
            print(f"  🏴 {flag.flag_key}")
            print(f"     └─ {status} - {flag.name}")
        
        print(f"\n🎯 Progressive Rollout Configuration:")
        print(f"   • Initial rollout: 5% of users")
        print(f"   • Feature flags ready for production")
        print(f"   • Module connections configured")
        
        # Test feature flag service
        print(f"\n🧪 Testing Feature Flag Service...")
        flag_service = FeatureFlagService(db_session)
        
        # Test one flag
        test_result = await flag_service.is_feature_enabled(
            "show_placeholder_content",
            user_id="test_user_001"
        )
        print(f"   ✓ Feature flag service operational: {test_result}")
        
        await db_session.close()
        
        print(f"\n🚀 Epic 2 deployment ready!")
        print(f"   Backend: ✅ Feature flags configured")
        print(f"   Frontend: ⏳ Hooks ready for deployment")
        print(f"   Rollout: 5% progressive deployment")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up feature flags: {e}")
        if 'db_session' in locals():
            await db_session.rollback()
            await db_session.close()
        return False


if __name__ == "__main__":
    success = asyncio.run(setup_epic2_feature_flags())
    if success:
        print("\n✅ Epic 2 feature flag setup completed successfully")
        exit(0)
    else:
        print("\n❌ Epic 2 feature flag setup failed")
        exit(1)