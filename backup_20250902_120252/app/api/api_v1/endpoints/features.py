from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....auth.dependencies import get_current_user
from ....models.user import User
from ....services.feature_flag_service import FeatureFlagService

router = APIRouter(prefix="/features", tags=["features"])


@router.get("/enabled")
async def get_enabled_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    module_id: Optional[str] = None
):
    """
    Get all enabled features for the current user
    Optionally filter by module
    """
    feature_flag_service = FeatureFlagService(db)
    
    try:
        enabled_features = await feature_flag_service.get_enabled_features(
            current_user,
            module_id
        )
        
        return {
            "enabled_features": enabled_features,
            "user_id": current_user.id,
            "organisation_id": current_user.organisation_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enabled features: {str(e)}"
        )


@router.get("/{flag_key}")
async def check_feature_flag(
    flag_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if a specific feature flag is enabled for the current user
    """
    feature_flag_service = FeatureFlagService(db)
    
    try:
        is_enabled = await feature_flag_service.is_feature_enabled(
            flag_key,
            current_user
        )
        
        return {
            "flag_key": flag_key,
            "enabled": is_enabled,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check feature flag: {str(e)}"
        )