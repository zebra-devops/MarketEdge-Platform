from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ....core.database import get_db
from ....models.organisation import Organisation, SubscriptionPlan
from ....models.user import User
from ....auth.dependencies import get_current_user, require_admin

router = APIRouter()


class OrganisationResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str]
    subscription_plan: str
    is_active: bool

    class Config:
        from_attributes = True


class OrganisationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    subscription_plan: Optional[SubscriptionPlan] = None


@router.get("/current", response_model=OrganisationResponse)
async def get_current_organisation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's organisation"""
    organisation = db.query(Organisation).filter(
        Organisation.id == current_user.organisation_id
    ).first()
    
    if not organisation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )
    
    return OrganisationResponse(
        id=str(organisation.id),
        name=organisation.name,
        industry=organisation.industry,
        subscription_plan=organisation.subscription_plan.value,
        is_active=organisation.is_active
    )


@router.put("/current", response_model=OrganisationResponse)
async def update_current_organisation(
    organisation_update: OrganisationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update current user's organisation (admin only)"""
    organisation = db.query(Organisation).filter(
        Organisation.id == current_user.organisation_id
    ).first()
    
    if not organisation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found"
        )
    
    update_data = organisation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organisation, field, value)
    
    db.commit()
    db.refresh(organisation)
    
    return OrganisationResponse(
        id=str(organisation.id),
        name=organisation.name,
        industry=organisation.industry,
        subscription_plan=organisation.subscription_plan.value,
        is_active=organisation.is_active
    )