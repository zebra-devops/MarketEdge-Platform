"""
Industry Configuration Template Management API

This module provides APIs for managing industry-specific configuration templates
supporting template creation, customization, and application to organizations.
"""
import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field, validator

from ....core.database import get_db
from ....auth.dependencies import get_current_user, require_role
from ....models.user import User, UserRole
from ....models.hierarchy import IndustryTemplate, OrganizationTemplateApplication, EnhancedUserRole
from ....services.permission_service import IndustryTemplateService
from ....core.logging import logger

router = APIRouter()


# Pydantic Models
class CreateIndustryTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    industry_code: str = Field(..., min_length=1, max_length=20, description="Industry code (e.g., 'CINEMA', 'HOTEL')")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    default_settings: Dict[str, Any] = Field(..., description="Default configuration settings")
    default_permissions: Dict[str, List[str]] = Field(..., description="Default role-permission mapping")
    default_features: Dict[str, Any] = Field(..., description="Default feature flags")
    dashboard_config: Optional[Dict[str, Any]] = Field(None, description="Dashboard layout configuration")
    parent_template_id: Optional[uuid.UUID] = Field(None, description="Parent template for inheritance")
    customizable_fields: Optional[List[str]] = Field(None, description="Fields that can be customized")
    is_base_template: bool = Field(False, description="Whether this is a base template")
    version: str = Field("1.0.0", description="Template version")
    
    @validator('industry_code')
    def industry_code_must_be_uppercase(cls, v):
        return v.upper()
    
    @validator('default_permissions')
    def validate_permissions(cls, v):
        valid_roles = [role.value for role in EnhancedUserRole]
        for role in v.keys():
            if role not in valid_roles:
                raise ValueError(f'Invalid role: {role}. Must be one of {valid_roles}')
        return v


class UpdateIndustryTemplateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    default_settings: Optional[Dict[str, Any]] = None
    default_permissions: Optional[Dict[str, List[str]]] = None
    default_features: Optional[Dict[str, Any]] = None
    dashboard_config: Optional[Dict[str, Any]] = None
    customizable_fields: Optional[List[str]] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None


class ApplyTemplateRequest(BaseModel):
    template_id: uuid.UUID = Field(..., description="Template ID to apply")
    organization_id: uuid.UUID = Field(..., description="Organization ID")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Template customizations")
    override_existing: bool = Field(False, description="Override existing template applications")


class IndustryTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    industry_code: str
    display_name: str
    description: Optional[str]
    default_settings: Dict[str, Any]
    default_permissions: Dict[str, List[str]]
    default_features: Dict[str, Any]
    dashboard_config: Optional[Dict[str, Any]]
    parent_template_id: Optional[uuid.UUID]
    customizable_fields: Optional[List[str]]
    is_base_template: bool
    is_active: bool
    version: str
    child_templates_count: int
    organizations_count: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


# Default industry templates
CINEMA_DEFAULT_TEMPLATE = {
    "name": "Cinema Industry Standard",
    "industry_code": "CINEMA",
    "display_name": "Cinema & Entertainment",
    "description": "Standard configuration for cinema and entertainment venues",
    "default_settings": {
        "industry_type": "cinema",
        "subscription_plan": "professional",
        "rate_limit_per_hour": 2000,
        "burst_limit": 200,
        "features": {
            "dynamic_pricing": True,
            "competitor_tracking": True,
            "capacity_monitoring": True,
            "seasonal_adjustments": True,
            "real_time_updates": True
        },
        "dashboard_widgets": ["revenue_chart", "competitor_comparison", "capacity_utilization"],
        "data_refresh_interval": 300  # 5 minutes
    },
    "default_permissions": {
        "super_admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"],
        "org_admin": ["read", "write", "delete", "manage_users", "manage_settings", "view_reports", "export_data"],
        "location_manager": ["read", "write", "manage_users", "view_reports", "export_data"],
        "department_lead": ["read", "write", "view_reports"],
        "user": ["read", "view_reports"],
        "viewer": ["read"]
    },
    "default_features": {
        "pricing_optimization": True,
        "competitor_analysis": True,
        "market_trends": True,
        "automated_alerts": True,
        "custom_reports": True,
        "api_access": False
    },
    "dashboard_config": {
        "layout": "cinema",
        "default_view": "performance_overview",
        "widgets": [
            {"type": "revenue_chart", "position": {"row": 1, "col": 1, "span": 2}},
            {"type": "competitor_comparison", "position": {"row": 1, "col": 3, "span": 1}},
            {"type": "capacity_utilization", "position": {"row": 2, "col": 1, "span": 1}},
            {"type": "pricing_alerts", "position": {"row": 2, "col": 2, "span": 2}}
        ]
    },
    "customizable_fields": [
        "data_refresh_interval", 
        "dashboard_widgets", 
        "rate_limit_per_hour", 
        "burst_limit",
        "features.dynamic_pricing",
        "features.competitor_tracking"
    ]
}

HOTEL_DEFAULT_TEMPLATE = {
    "name": "Hotel Industry Standard",
    "industry_code": "HOTEL",
    "display_name": "Hotel & Hospitality",
    "description": "Standard configuration for hotels and hospitality businesses",
    "default_settings": {
        "industry_type": "hotel",
        "subscription_plan": "enterprise",
        "rate_limit_per_hour": 3000,
        "burst_limit": 300,
        "features": {
            "room_rate_optimization": True,
            "occupancy_forecasting": True,
            "competitor_benchmarking": True,
            "seasonal_pricing": True,
            "real_time_availability": True
        },
        "dashboard_widgets": ["adr_chart", "occupancy_trends", "revenue_per_room"],
        "data_refresh_interval": 600  # 10 minutes
    },
    "default_permissions": {
        "super_admin": ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"],
        "org_admin": ["read", "write", "delete", "manage_users", "manage_settings", "view_reports", "export_data"],
        "location_manager": ["read", "write", "manage_users", "view_reports", "export_data"],
        "department_lead": ["read", "write", "view_reports"],
        "user": ["read", "view_reports"],
        "viewer": ["read"]
    },
    "default_features": {
        "revenue_management": True,
        "competitor_analysis": True,
        "demand_forecasting": True,
        "rate_recommendations": True,
        "performance_analytics": True,
        "api_access": True
    },
    "dashboard_config": {
        "layout": "hotel",
        "default_view": "revenue_dashboard",
        "widgets": [
            {"type": "adr_chart", "position": {"row": 1, "col": 1, "span": 2}},
            {"type": "occupancy_trends", "position": {"row": 1, "col": 3, "span": 1}},
            {"type": "revenue_per_room", "position": {"row": 2, "col": 1, "span": 1}},
            {"type": "competitor_rates", "position": {"row": 2, "col": 2, "span": 2}}
        ]
    },
    "customizable_fields": [
        "data_refresh_interval",
        "dashboard_widgets",
        "rate_limit_per_hour",
        "burst_limit",
        "features.room_rate_optimization",
        "features.occupancy_forecasting"
    ]
}


@router.post("/industry-templates", response_model=IndustryTemplateResponse)
async def create_industry_template(
    request: CreateIndustryTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """Create a new industry template"""
    
    # Check for duplicate industry code
    existing_template = db.query(IndustryTemplate).filter(
        IndustryTemplate.industry_code == request.industry_code
    ).first()
    
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with industry code '{request.industry_code}' already exists"
        )
    
    # Validate parent template if specified
    if request.parent_template_id:
        parent_template = db.query(IndustryTemplate).filter(
            IndustryTemplate.id == request.parent_template_id
        ).first()
        if not parent_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent template not found"
            )
    
    try:
        # Create the template
        template = IndustryTemplate(
            name=request.name,
            industry_code=request.industry_code,
            display_name=request.display_name,
            description=request.description,
            default_settings=str(request.default_settings).replace("'", '"'),
            default_permissions=str(request.default_permissions).replace("'", '"'),
            default_features=str(request.default_features).replace("'", '"'),
            dashboard_config=str(request.dashboard_config).replace("'", '"') if request.dashboard_config else None,
            parent_template_id=request.parent_template_id,
            is_base_template=request.is_base_template,
            customizable_fields=str(request.customizable_fields).replace("'", '"') if request.customizable_fields else None,
            is_active=True,
            version=request.version
        )
        
        db.add(template)
        db.commit()
        
        logger.info(f"Created industry template: {template.name} ({template.industry_code})")
        
        return IndustryTemplateResponse(
            id=template.id,
            name=template.name,
            industry_code=template.industry_code,
            display_name=template.display_name,
            description=template.description,
            default_settings=json.loads(template.default_settings),
            default_permissions=json.loads(template.default_permissions),
            default_features=json.loads(template.default_features),
            dashboard_config=json.loads(template.dashboard_config) if template.dashboard_config else None,
            parent_template_id=template.parent_template_id,
            customizable_fields=json.loads(template.customizable_fields) if template.customizable_fields else None,
            is_base_template=template.is_base_template,
            is_active=template.is_active,
            version=template.version,
            child_templates_count=0,
            organizations_count=0,
            created_at=template.created_at.isoformat(),
            updated_at=template.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating industry template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create industry template: {str(e)}"
        )


@router.get("/industry-templates", response_model=List[IndustryTemplateResponse])
async def list_industry_templates(
    active_only: bool = Query(True, description="Only return active templates"),
    industry_code: Optional[str] = Query(None, description="Filter by industry code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all industry templates"""
    
    query = db.query(IndustryTemplate)
    
    if active_only:
        query = query.filter(IndustryTemplate.is_active == True)
    
    if industry_code:
        query = query.filter(IndustryTemplate.industry_code == industry_code.upper())
    
    templates = query.all()
    
    # Get counts for each template
    result = []
    for template in templates:
        child_count = db.query(IndustryTemplate).filter(
            IndustryTemplate.parent_template_id == template.id
        ).count()
        
        org_count = db.query(OrganizationTemplateApplication).filter(
            and_(
                OrganizationTemplateApplication.template_id == template.id,
                OrganizationTemplateApplication.is_active == True
            )
        ).count()
        
        result.append(IndustryTemplateResponse(
            id=template.id,
            name=template.name,
            industry_code=template.industry_code,
            display_name=template.display_name,
            description=template.description,
            default_settings=json.loads(template.default_settings),
            default_permissions=json.loads(template.default_permissions),
            default_features=json.loads(template.default_features),
            dashboard_config=json.loads(template.dashboard_config) if template.dashboard_config else None,
            parent_template_id=template.parent_template_id,
            customizable_fields=json.loads(template.customizable_fields) if template.customizable_fields else None,
            is_base_template=template.is_base_template,
            is_active=template.is_active,
            version=template.version,
            child_templates_count=child_count,
            organizations_count=org_count,
            created_at=template.created_at.isoformat(),
            updated_at=template.updated_at.isoformat()
        ))
    
    return result


@router.get("/industry-templates/{template_id}", response_model=IndustryTemplateResponse)
async def get_industry_template(
    template_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific industry template"""
    
    template = db.query(IndustryTemplate).filter(
        IndustryTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Industry template not found"
        )
    
    # Get counts
    child_count = db.query(IndustryTemplate).filter(
        IndustryTemplate.parent_template_id == template.id
    ).count()
    
    org_count = db.query(OrganizationTemplateApplication).filter(
        and_(
            OrganizationTemplateApplication.template_id == template.id,
            OrganizationTemplateApplication.is_active == True
        )
    ).count()
    
    return IndustryTemplateResponse(
        id=template.id,
        name=template.name,
        industry_code=template.industry_code,
        display_name=template.display_name,
        description=template.description,
        default_settings=json.loads(template.default_settings),
        default_permissions=json.loads(template.default_permissions),
        default_features=json.loads(template.default_features),
        dashboard_config=json.loads(template.dashboard_config) if template.dashboard_config else None,
        parent_template_id=template.parent_template_id,
        customizable_fields=json.loads(template.customizable_fields) if template.customizable_fields else None,
        is_base_template=template.is_base_template,
        is_active=template.is_active,
        version=template.version,
        child_templates_count=child_count,
        organizations_count=org_count,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat()
    )


@router.put("/industry-templates/{template_id}", response_model=IndustryTemplateResponse)
async def update_industry_template(
    template_id: uuid.UUID = Path(...),
    request: UpdateIndustryTemplateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """Update an industry template"""
    
    template = db.query(IndustryTemplate).filter(
        IndustryTemplate.id == template_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Industry template not found"
        )
    
    try:
        # Update fields if provided
        if request.name is not None:
            template.name = request.name
        if request.display_name is not None:
            template.display_name = request.display_name
        if request.description is not None:
            template.description = request.description
        if request.default_settings is not None:
            template.default_settings = str(request.default_settings).replace("'", '"')
        if request.default_permissions is not None:
            template.default_permissions = str(request.default_permissions).replace("'", '"')
        if request.default_features is not None:
            template.default_features = str(request.default_features).replace("'", '"')
        if request.dashboard_config is not None:
            template.dashboard_config = str(request.dashboard_config).replace("'", '"')
        if request.customizable_fields is not None:
            template.customizable_fields = str(request.customizable_fields).replace("'", '"')
        if request.is_active is not None:
            template.is_active = request.is_active
        if request.version is not None:
            template.version = request.version
        
        db.commit()
        
        logger.info(f"Updated industry template: {template.name}")
        
        # Return updated template (reuse get logic)
        child_count = db.query(IndustryTemplate).filter(
            IndustryTemplate.parent_template_id == template.id
        ).count()
        
        org_count = db.query(OrganizationTemplateApplication).filter(
            and_(
                OrganizationTemplateApplication.template_id == template.id,
                OrganizationTemplateApplication.is_active == True
            )
        ).count()
        
        return IndustryTemplateResponse(
            id=template.id,
            name=template.name,
            industry_code=template.industry_code,
            display_name=template.display_name,
            description=template.description,
            default_settings=json.loads(template.default_settings),
            default_permissions=json.loads(template.default_permissions),
            default_features=json.loads(template.default_features),
            dashboard_config=json.loads(template.dashboard_config) if template.dashboard_config else None,
            parent_template_id=template.parent_template_id,
            customizable_fields=json.loads(template.customizable_fields) if template.customizable_fields else None,
            is_base_template=template.is_base_template,
            is_active=template.is_active,
            version=template.version,
            child_templates_count=child_count,
            organizations_count=org_count,
            created_at=template.created_at.isoformat(),
            updated_at=template.updated_at.isoformat()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating industry template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update industry template: {str(e)}"
        )


@router.post("/industry-templates/apply", response_model=Dict[str, Any])
async def apply_template_to_organization(
    request: ApplyTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """Apply an industry template to an organization"""
    
    template_service = IndustryTemplateService(db)
    
    # Check if template application already exists
    if not request.override_existing:
        existing_application = db.query(OrganizationTemplateApplication).filter(
            and_(
                OrganizationTemplateApplication.organization_id == request.organization_id,
                OrganizationTemplateApplication.template_id == request.template_id,
                OrganizationTemplateApplication.is_active == True
            )
        ).first()
        
        if existing_application:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template already applied to organization. Use override_existing=true to reapply."
            )
    
    success = template_service.apply_template_to_organization(
        request.organization_id,
        request.template_id,
        current_user.id,
        request.customizations
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply template to organization"
        )
    
    return {
        "message": "Template applied successfully",
        "organization_id": str(request.organization_id),
        "template_id": str(request.template_id),
        "applied_by": str(current_user.id),
        "customizations_applied": bool(request.customizations)
    }


@router.post("/industry-templates/initialize-defaults")
async def initialize_default_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.admin]))
):
    """Initialize default industry templates (Cinema, Hotel, etc.)"""
    
    default_templates = [CINEMA_DEFAULT_TEMPLATE, HOTEL_DEFAULT_TEMPLATE]
    created_templates = []
    
    for template_data in default_templates:
        # Check if template already exists
        existing = db.query(IndustryTemplate).filter(
            IndustryTemplate.industry_code == template_data["industry_code"]
        ).first()
        
        if existing:
            logger.info(f"Template {template_data['industry_code']} already exists, skipping")
            continue
        
        try:
            template = IndustryTemplate(
                name=template_data["name"],
                industry_code=template_data["industry_code"],
                display_name=template_data["display_name"],
                description=template_data["description"],
                default_settings=str(template_data["default_settings"]).replace("'", '"'),
                default_permissions=str(template_data["default_permissions"]).replace("'", '"'),
                default_features=str(template_data["default_features"]).replace("'", '"'),
                dashboard_config=str(template_data["dashboard_config"]).replace("'", '"'),
                customizable_fields=str(template_data["customizable_fields"]).replace("'", '"'),
                is_base_template=True,
                is_active=True,
                version="1.0.0"
            )
            
            db.add(template)
            created_templates.append(template_data["industry_code"])
            
        except Exception as e:
            logger.error(f"Error creating default template {template_data['industry_code']}: {str(e)}")
    
    try:
        db.commit()
        logger.info(f"Initialized {len(created_templates)} default templates")
        
        return {
            "message": "Default templates initialized successfully",
            "created_templates": created_templates,
            "total_created": len(created_templates)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing default templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize default templates: {str(e)}"
        )