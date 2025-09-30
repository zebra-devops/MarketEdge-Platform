from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.database import get_async_db
from app.models.tool import Tool
from app.models.organisation_tool_access import OrganisationToolAccess
from app.models.user import User
from app.auth.dependencies import get_current_user, require_admin

router = APIRouter()


class ToolResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    version: str
    is_active: bool
    has_access: bool = False
    subscription_tier: Optional[str] = None
    features_enabled: List[str] = []

    class Config:
        from_attributes = True


class ToolAccessResponse(BaseModel):
    tool: ToolResponse
    subscription_tier: str
    features_enabled: List[str]
    usage_limits: Dict[str, Any]


@router.get("/", response_model=List[ToolResponse])
async def get_tools(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available tools with access information for current organisation"""
    from sqlalchemy import select

    # Query tools
    tools_query = select(Tool).filter(Tool.is_active == True).offset(skip).limit(limit)
    tools_result = await db.execute(tools_query)
    tools = tools_result.scalars().all()

    # Query tool access
    tool_access_query = select(OrganisationToolAccess).filter(
        OrganisationToolAccess.organisation_id == current_user.organisation_id
    )
    tool_access_result = await db.execute(tool_access_query)
    tool_access = tool_access_result.scalars().all()
    
    access_dict = {access.tool_id: access for access in tool_access}
    
    result = []
    for tool in tools:
        access = access_dict.get(tool.id)
        result.append(ToolResponse(
            id=str(tool.id),
            name=tool.name,
            description=tool.description,
            version=tool.version,
            is_active=tool.is_active,
            has_access=access is not None,
            subscription_tier=access.subscription_tier if access else None,
            features_enabled=access.features_enabled if access else []
        ))
    
    return result


@router.get("/access", response_model=List[ToolAccessResponse])
async def get_organisation_tool_access(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get tools that current organisation has access to"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Query tool access with joined Tool data
    tool_access_query = select(OrganisationToolAccess).join(Tool).filter(
        OrganisationToolAccess.organisation_id == current_user.organisation_id,
        Tool.is_active == True
    ).options(selectinload(OrganisationToolAccess.tool))
    tool_access_result = await db.execute(tool_access_query)
    tool_access = tool_access_result.scalars().all()
    
    result = []
    for access in tool_access:
        result.append(ToolAccessResponse(
            tool=ToolResponse(
                id=str(access.tool.id),
                name=access.tool.name,
                description=access.tool.description,
                version=access.tool.version,
                is_active=access.tool.is_active,
                has_access=True,
                subscription_tier=access.subscription_tier,
                features_enabled=access.features_enabled
            ),
            subscription_tier=access.subscription_tier,
            features_enabled=access.features_enabled,
            usage_limits=access.usage_limits
        ))
    
    return result


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific tool with access information"""
    from sqlalchemy import select

    # Query tool
    tool_query = select(Tool).filter(Tool.id == tool_id, Tool.is_active == True)
    tool_result = await db.execute(tool_query)
    tool = tool_result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )

    # Query access
    access_query = select(OrganisationToolAccess).filter(
        OrganisationToolAccess.organisation_id == current_user.organisation_id,
        OrganisationToolAccess.tool_id == tool_id
    )
    access_result = await db.execute(access_query)
    access = access_result.scalar_one_or_none()
    
    return ToolResponse(
        id=str(tool.id),
        name=tool.name,
        description=tool.description,
        version=tool.version,
        is_active=tool.is_active,
        has_access=access is not None,
        subscription_tier=access.subscription_tier if access else None,
        features_enabled=access.features_enabled if access else []
    )