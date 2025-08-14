from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from ....backend.app.core.database import get_db
from ....backend.app.auth.dependencies import get_current_user, require_role
from ....backend.app.models.user import User
from ..models.market_edge import Market, Competitor, PricingData, MarketAlert
from ..services import MarketAnalysisService, CompetitiveIntelligenceService

router = APIRouter(prefix="/market-edge", tags=["market-edge"])


# Pydantic models for request/response
class MarketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    geographic_bounds: Optional[Dict[str, Any]] = None
    tracking_config: Optional[Dict[str, Any]] = None


class MarketResponse(BaseModel):
    id: str
    name: str
    geographic_bounds: Optional[Dict[str, Any]]
    organisation_id: str
    created_by: str
    competitor_count: int
    is_active: bool
    tracking_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    market_id: str
    business_type: Optional[str] = None
    website: Optional[str] = None
    locations: Optional[Dict[str, Any]] = None
    tracking_priority: int = Field(default=3, ge=1, le=5)
    description: Optional[str] = None
    market_share_estimate: Optional[float] = Field(None, ge=0, le=100)


class CompetitorResponse(BaseModel):
    id: str
    name: str
    market_id: str
    organisation_id: str
    business_type: Optional[str]
    website: Optional[str]
    locations: Optional[Dict[str, Any]]
    tracking_priority: int
    description: Optional[str]
    market_share_estimate: Optional[float]
    last_updated: Optional[datetime]
    created_at: datetime


class PricingDataCreate(BaseModel):
    competitor_id: str
    product_service: str = Field(..., min_length=1, max_length=255)
    price_point: float = Field(..., gt=0)
    currency: str = Field(default="GBP", max_length=3)
    date_collected: datetime
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_promotion: bool = False
    promotion_details: Optional[str] = None


class PricingDataResponse(BaseModel):
    id: str
    competitor_id: str
    market_id: str
    product_service: str
    price_point: float
    currency: str
    date_collected: datetime
    source: Optional[str]
    metadata: Optional[Dict[str, Any]]
    is_promotion: bool
    promotion_details: Optional[str]
    created_at: datetime


class MarketAlertResponse(BaseModel):
    id: str
    market_id: str
    organisation_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    trigger_data: Optional[Dict[str, Any]]
    is_read: bool
    resolved_at: Optional[datetime]
    created_at: datetime


# Market endpoints
@router.get("/markets", response_model=List[MarketResponse])
async def get_markets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all markets for the current user's organisation"""
    markets = db.query(Market).filter(
        Market.organisation_id == current_user.organisation_id,
        Market.is_active == True
    ).all()
    
    return markets


@router.post("/markets", response_model=MarketResponse)
async def create_market(
    market_data: MarketCreate,
    current_user: User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Create a new market"""
    market = Market(
        name=market_data.name,
        geographic_bounds=market_data.geographic_bounds,
        organisation_id=current_user.organisation_id,
        created_by=current_user.id,
        tracking_config=market_data.tracking_config or {}
    )
    
    db.add(market)
    db.commit()
    db.refresh(market)
    
    return market


@router.get("/markets/{market_id}", response_model=MarketResponse)
async def get_market(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific market"""
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    return market


@router.put("/markets/{market_id}", response_model=MarketResponse)
async def update_market(
    market_id: str,
    market_data: MarketCreate,
    current_user: User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Update a market"""
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    market.name = market_data.name
    market.geographic_bounds = market_data.geographic_bounds
    market.tracking_config = market_data.tracking_config or {}
    market.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(market)
    
    return market


@router.delete("/markets/{market_id}")
async def delete_market(
    market_id: str,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete a market (soft delete by setting is_active=False)"""
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    market.is_active = False
    market.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Market deleted successfully"}


# Competitor endpoints
@router.get("/markets/{market_id}/competitors", response_model=List[CompetitorResponse])
async def get_competitors(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all competitors for a market"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id,
        Market.is_active == True
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    competitors = db.query(Competitor).filter(
        Competitor.market_id == market_id,
        Competitor.organisation_id == current_user.organisation_id
    ).all()
    
    return competitors


@router.post("/competitors", response_model=CompetitorResponse)
async def create_competitor(
    competitor_data: CompetitorCreate,
    current_user: User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Create a new competitor"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == competitor_data.market_id,
        Market.organisation_id == current_user.organisation_id,
        Market.is_active == True
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    competitor = Competitor(
        name=competitor_data.name,
        market_id=competitor_data.market_id,
        organisation_id=current_user.organisation_id,
        business_type=competitor_data.business_type,
        website=competitor_data.website,
        locations=competitor_data.locations,
        tracking_priority=competitor_data.tracking_priority,
        description=competitor_data.description,
        market_share_estimate=competitor_data.market_share_estimate
    )
    
    db.add(competitor)
    
    # Update market competitor count
    market.competitor_count = db.query(Competitor).filter(
        Competitor.market_id == market.id
    ).count() + 1
    
    db.commit()
    db.refresh(competitor)
    
    return competitor


@router.get("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific competitor"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.organisation_id == current_user.organisation_id
    ).first()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    return competitor


@router.put("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: str,
    competitor_data: CompetitorCreate,
    current_user: User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Update a competitor"""
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.organisation_id == current_user.organisation_id
    ).first()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    competitor.name = competitor_data.name
    competitor.business_type = competitor_data.business_type
    competitor.website = competitor_data.website
    competitor.locations = competitor_data.locations
    competitor.tracking_priority = competitor_data.tracking_priority
    competitor.description = competitor_data.description
    competitor.market_share_estimate = competitor_data.market_share_estimate
    competitor.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(competitor)
    
    return competitor


# Pricing data endpoints
@router.post("/pricing-data", response_model=PricingDataResponse)
async def create_pricing_data(
    pricing_data: PricingDataCreate,
    current_user: User = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """Create new pricing data"""
    # Verify competitor access
    competitor = db.query(Competitor).filter(
        Competitor.id == pricing_data.competitor_id,
        Competitor.organisation_id == current_user.organisation_id
    ).first()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    pricing = PricingData(
        competitor_id=pricing_data.competitor_id,
        market_id=competitor.market_id,
        product_service=pricing_data.product_service,
        price_point=pricing_data.price_point,
        currency=pricing_data.currency,
        date_collected=pricing_data.date_collected,
        source=pricing_data.source,
        metadata=pricing_data.metadata,
        is_promotion=pricing_data.is_promotion,
        promotion_details=pricing_data.promotion_details
    )
    
    db.add(pricing)
    
    # Update competitor last_updated
    competitor.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(pricing)
    
    return pricing


@router.get("/markets/{market_id}/pricing-data", response_model=List[PricingDataResponse])
async def get_market_pricing_data(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    competitor_id: Optional[str] = Query(None),
    product_service: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get pricing data for a market"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    query = db.query(PricingData).filter(PricingData.market_id == market_id)
    
    if competitor_id:
        query = query.filter(PricingData.competitor_id == competitor_id)
    
    if product_service:
        query = query.filter(PricingData.product_service == product_service)
    
    pricing_data = query.order_by(PricingData.date_collected.desc()).limit(limit).all()
    
    return pricing_data


# Analysis endpoints
@router.get("/markets/{market_id}/overview")
async def get_market_overview(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive market overview"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    ci_service = CompetitiveIntelligenceService(db)
    overview = ci_service.get_market_overview(market_id, current_user.organisation_id)
    
    return overview


@router.get("/markets/{market_id}/analysis")
async def get_market_analysis(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    product_service: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get market analysis and metrics"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    analysis_service = MarketAnalysisService(db)
    metrics = analysis_service.calculate_market_metrics(
        market_id, 
        product_service, 
        days_back
    )
    
    return metrics


@router.get("/competitors/{competitor_id}/analysis")
async def get_competitor_analysis(
    competitor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get detailed competitor analysis"""
    # Verify competitor access
    competitor = db.query(Competitor).filter(
        Competitor.id == competitor_id,
        Competitor.organisation_id == current_user.organisation_id
    ).first()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    ci_service = CompetitiveIntelligenceService(db)
    analysis = ci_service.get_competitor_analysis(
        competitor_id, 
        current_user.organisation_id, 
        days_back
    )
    
    return analysis


@router.get("/markets/{market_id}/comparison")
async def compare_competitors(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    competitor_ids: Optional[str] = Query(None, description="Comma-separated competitor IDs"),
    product_service: Optional[str] = Query(None)
):
    """Compare competitors in a market"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    competitor_id_list = None
    if competitor_ids:
        competitor_id_list = [id.strip() for id in competitor_ids.split(",")]
    
    ci_service = CompetitiveIntelligenceService(db)
    comparison = ci_service.compare_competitors(
        market_id,
        current_user.organisation_id,
        competitor_id_list,
        product_service
    )
    
    return comparison


@router.get("/markets/{market_id}/trends")
async def get_pricing_trends(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    competitor_id: Optional[str] = Query(None),
    product_service: Optional[str] = Query(None),
    days_back: int = Query(90, ge=7, le=365)
):
    """Get pricing trends for a market"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    ci_service = CompetitiveIntelligenceService(db)
    trends = ci_service.get_pricing_trends(
        market_id,
        current_user.organisation_id,
        competitor_id,
        product_service,
        days_back
    )
    
    return trends


@router.get("/markets/{market_id}/alerts", response_model=List[MarketAlertResponse])
async def get_market_alerts(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = Query(False),
    limit: int = Query(50, le=500)
):
    """Get alerts for a market"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    query = db.query(MarketAlert).filter(
        MarketAlert.market_id == market_id,
        MarketAlert.organisation_id == current_user.organisation_id
    )
    
    if unread_only:
        query = query.filter(MarketAlert.is_read == False)
    
    alerts = query.order_by(MarketAlert.created_at.desc()).limit(limit).all()
    
    return alerts


@router.post("/alerts/{alert_id}/mark-read")
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an alert as read"""
    alert = db.query(MarketAlert).filter(
        MarketAlert.id == alert_id,
        MarketAlert.organisation_id == current_user.organisation_id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = True
    db.commit()
    
    return {"message": "Alert marked as read"}


@router.get("/markets/{market_id}/report")
async def generate_market_report(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    report_type: str = Query("comprehensive", regex="^(comprehensive|summary|trends)$")
):
    """Generate a comprehensive market report"""
    # Verify market access
    market = db.query(Market).filter(
        Market.id == market_id,
        Market.organisation_id == current_user.organisation_id
    ).first()
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    ci_service = CompetitiveIntelligenceService(db)
    report = ci_service.generate_market_report(
        market_id,
        current_user.organisation_id,
        report_type
    )
    
    return report