from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from ....core.database import get_db
from ....core.rate_limit_config import Industry
from ....models.organisation import Organisation, SubscriptionPlan
from ....models.user import User
from ....auth.dependencies import get_current_user, require_admin, require_super_admin
from ....services.organisation_service import OrganisationService, OrganisationValidationError

router = APIRouter()


class OrganisationResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None  # Legacy field
    industry_type: str
    subscription_plan: str
    is_active: bool
    sic_code: Optional[str] = None
    rate_limit_per_hour: int
    burst_limit: int

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Industry: lambda v: v.value if v else None,
            SubscriptionPlan: lambda v: v.value if v else None
        }
    )


class OrganisationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    industry_type: Industry
    subscription_plan: SubscriptionPlan = SubscriptionPlan.basic
    sic_code: Optional[str] = Field(None, max_length=10)
    admin_email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)
    
    model_config = ConfigDict(
        json_encoders={
            Industry: lambda v: v.value if v else None,
            SubscriptionPlan: lambda v: v.value if v else None
        }
    )


class OrganisationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry_type: Optional[Industry] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    sic_code: Optional[str] = Field(None, max_length=10)
    
    model_config = ConfigDict(
        json_encoders={
            Industry: lambda v: v.value if v else None,
            SubscriptionPlan: lambda v: v.value if v else None
        }
    )


class IndustryConfigResponse(BaseModel):
    industry_type: str
    rate_limits: Dict[str, Any]
    security_config: Dict[str, Any]
    performance_config: Dict[str, Any]
    compliance_requirements: List[str]
    feature_flags: Dict[str, Any]


@router.post("", response_model=OrganisationResponse)
async def create_organisation(
    organisation_data: OrganisationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Create a new organisation with industry-specific configuration"""
    try:
        org_service = OrganisationService(db)
        
        admin_user_data = {
            'email': organisation_data.admin_email,
            'first_name': organisation_data.admin_first_name,
            'last_name': organisation_data.admin_last_name
        }
        
        organisation = org_service.create_organisation(
            name=organisation_data.name,
            industry_type=organisation_data.industry_type,
            subscription_plan=organisation_data.subscription_plan,
            sic_code=organisation_data.sic_code,
            admin_user_data=admin_user_data
        )
        
        return OrganisationResponse(
            id=str(organisation.id),
            name=organisation.name,
            industry=organisation.industry,
            industry_type=organisation.industry_type.value,
            subscription_plan=organisation.subscription_plan.value,
            is_active=organisation.is_active,
            sic_code=organisation.sic_code,
            rate_limit_per_hour=organisation.rate_limit_per_hour,
            burst_limit=organisation.burst_limit
        )
        
    except OrganisationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/current", response_model=OrganisationResponse)
async def get_current_organisation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's organisation"""
    org_service = OrganisationService(db)
    organisation = org_service.get_organisation(str(current_user.organisation_id))
    
    if not organisation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )
    
    return OrganisationResponse(
        id=str(organisation.id),
        name=organisation.name,
        industry=organisation.industry,
        industry_type=organisation.industry_type.value,
        subscription_plan=organisation.subscription_plan.value,
        is_active=organisation.is_active,
        sic_code=organisation.sic_code,
        rate_limit_per_hour=organisation.rate_limit_per_hour,
        burst_limit=organisation.burst_limit
    )


@router.put("/current", response_model=OrganisationResponse)
async def update_current_organisation(
    organisation_update: OrganisationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update current user's organisation (admin only)"""
    try:
        org_service = OrganisationService(db)
        
        organisation = org_service.update_organisation(
            organisation_id=str(current_user.organisation_id),
            name=organisation_update.name,
            industry_type=organisation_update.industry_type,
            subscription_plan=organisation_update.subscription_plan,
            sic_code=organisation_update.sic_code
        )
        
        return OrganisationResponse(
            id=str(organisation.id),
            name=organisation.name,
            industry=organisation.industry,
            industry_type=organisation.industry_type.value,
            subscription_plan=organisation.subscription_plan.value,
            is_active=organisation.is_active,
            sic_code=organisation.sic_code,
            rate_limit_per_hour=organisation.rate_limit_per_hour,
            burst_limit=organisation.burst_limit
        )
        
    except OrganisationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/current")
async def delete_current_organisation(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete current user's organisation (admin only)"""
    try:
        org_service = OrganisationService(db)
        
        result = org_service.delete_organisation(
            organisation_id=str(current_user.organisation_id),
            force=force
        )
        
        if result:
            return {"message": "Organisation deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete organisation"
            )
            
    except OrganisationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/current/config", response_model=IndustryConfigResponse)
async def get_organisation_industry_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get industry-specific configuration for current organisation"""
    try:
        org_service = OrganisationService(db)
        config = org_service.get_industry_specific_config(
            str(current_user.organisation_id),
            requesting_user_org_id=str(current_user.organisation_id)
        )
        
        return IndustryConfigResponse(
            industry_type=config['industry_type'],
            rate_limits=config['rate_limits'],
            security_config=config['security_config'],
            performance_config=config['performance_config'],
            compliance_requirements=config['compliance_requirements'],
            feature_flags=config['feature_flags']
        )
        
    except OrganisationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/industries", response_model=List[Dict[str, str]])
async def get_available_industries():
    """Get list of available industry types"""
    industries = []
    for industry in Industry:
        industries.append({
            "value": industry.value,
            "label": industry.value.replace('_', ' ').title()
        })
    return industries


@router.get("", response_model=List[OrganisationResponse])
async def get_all_organisations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Get all organisations (Super Admin only)"""
    try:
        org_service = OrganisationService(db)
        organisations = org_service.get_all_organisations()
        
        return [OrganisationResponse(
            id=str(org.id),
            name=org.name,
            industry=org.industry,
            industry_type=org.industry_type.value,
            subscription_plan=org.subscription_plan.value,
            is_active=org.is_active,
            sic_code=org.sic_code,
            rate_limit_per_hour=org.rate_limit_per_hour,
            burst_limit=org.burst_limit
        ) for org in organisations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch organisations: {str(e)}"
        )


@router.get("/stats")
async def get_organisation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get organisation statistics (admin only)"""
    org_service = OrganisationService(db)
    stats = org_service.get_organisation_stats()
    return stats


@router.get("/accessible", response_model=List[OrganisationResponse])
async def get_user_accessible_organisations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organisations the current user has access to"""
    try:
        org_service = OrganisationService(db)
        
        # For super admin, return all organisations
        if current_user.role == 'admin':
            organisations = org_service.get_all_organisations()
        else:
            # For regular users, return organisations they have access to
            # This would typically be their own org and any orgs they're invited to
            organisations = org_service.get_user_accessible_organisations(str(current_user.id))
        
        return [OrganisationResponse(
            id=str(org.id),
            name=org.name,
            industry=org.industry,
            industry_type=org.industry_type.value,
            subscription_plan=org.subscription_plan.value,
            is_active=org.is_active,
            sic_code=org.sic_code,
            rate_limit_per_hour=org.rate_limit_per_hour,
            burst_limit=org.burst_limit
        ) for org in organisations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch accessible organisations: {str(e)}"
        )