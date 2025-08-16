from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from ....core.database import get_db
from ....auth.dependencies import get_current_user
from ....models.user import User

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


# Health check endpoint (no auth required)
@router.get("/health")
async def health_check():
    """Health check endpoint for Market Edge"""
    return {"status": "healthy", "service": "market-edge"}

# Temporary endpoints that return mock data until we can properly integrate the full Market Edge models
@router.get("/markets")
async def get_markets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all markets for the current user's organisation (mock data for now)"""
    # Return mock data until we can integrate the full Market Edge models
    mock_markets = [
        {
            "id": "1",
            "name": "UK Cinema Market",
            "geographic_bounds": {
                "country": "United Kingdom",
                "regions": ["England", "Scotland", "Wales", "Northern Ireland"]
            },
            "organisation_id": current_user.organisation_id,
            "created_by": current_user.id,
            "competitor_count": 6,
            "is_active": True,
            "tracking_config": {
                "price_tracking": True,
                "promotion_tracking": True
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "2", 
            "name": "Manchester Hotel Market",
            "geographic_bounds": {
                "city": "Manchester",
                "country": "United Kingdom"
            },
            "organisation_id": current_user.organisation_id,
            "created_by": current_user.id,
            "competitor_count": 5,
            "is_active": True,
            "tracking_config": {
                "price_tracking": True,
                "occupancy_tracking": True
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "3",
            "name": "London Restaurant Market", 
            "geographic_bounds": {
                "city": "London",
                "country": "United Kingdom"
            },
            "organisation_id": current_user.organisation_id,
            "created_by": current_user.id,
            "competitor_count": 5,
            "is_active": True,
            "tracking_config": {
                "price_tracking": True,
                "menu_tracking": True
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    return mock_markets


@router.get("/markets/{market_id}")
async def get_market(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific market (mock data for now)"""
    # Mock market data
    if market_id == "1":
        return {
            "id": "1",
            "name": "UK Cinema Market",
            "geographic_bounds": {
                "country": "United Kingdom",
                "regions": ["England", "Scotland", "Wales", "Northern Ireland"]
            },
            "organisation_id": current_user.organisation_id,
            "created_by": current_user.id,
            "competitor_count": 6,
            "is_active": True,
            "tracking_config": {
                "price_tracking": True,
                "promotion_tracking": True
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    raise HTTPException(status_code=404, detail="Market not found")


@router.get("/markets/{market_id}/overview")
async def get_market_overview(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive market overview (mock data for now)"""
    
    # Mock overview data
    mock_overview = {
        "market": {
            "id": market_id,
            "name": "UK Cinema Market" if market_id == "1" else "Sample Market",
            "is_active": True,
            "competitor_count": 6,
            "created_at": datetime.utcnow().isoformat()
        },
        "competitors": [
            {
                "id": "comp_1",
                "name": "Odeon Cinemas",
                "business_type": "Cinema Chain",
                "tracking_priority": 5,
                "market_share_estimate": 35.5,
                "last_updated": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "comp_2", 
                "name": "Cineworld",
                "business_type": "Cinema Chain",
                "tracking_priority": 5,
                "market_share_estimate": 28.2,
                "last_updated": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "comp_3",
                "name": "Vue Entertainment", 
                "business_type": "Cinema Chain",
                "tracking_priority": 4,
                "market_share_estimate": 22.1,
                "last_updated": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
        ],
        "metrics": {
            "period_start": (datetime.utcnow()).isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "total_data_points": 2847,
            "average_price": 12.45,
            "median_price": 11.80,
            "min_price": 8.50,
            "max_price": 22.50,
            "price_range": 14.00,
            "standard_deviation": 3.24,
            "price_quartiles": {
                "q1": 10.20,
                "q2": 11.80,
                "q3": 14.60
            },
            "competitors": {},
            "trends": {
                "trend": "increasing",
                "weekly_averages": {},
                "price_change": 0.65,
                "price_change_percent": 5.2
            },
            "anomalies": []
        },
        "recent_data_points": 2847,
        "recent_alerts": [
            {
                "id": "alert_1",
                "alert_type": "price_change",
                "severity": "medium", 
                "title": "Price Increase Detected",
                "message": "Odeon Cinemas increased IMAX ticket prices by 8% across London venues",
                "is_read": False,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "alert_2",
                "alert_type": "promotion",
                "severity": "low",
                "title": "New Promotion Launched",
                "message": "Vue Entertainment started weekend family deals promotion",
                "is_read": True,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    }
    
    return mock_overview


@router.get("/markets/{market_id}/analysis")
async def get_market_analysis(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    product_service: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365)
):
    """Get market analysis and metrics (mock data for now)"""
    
    return {
        "period_start": datetime.utcnow().isoformat(),
        "period_end": datetime.utcnow().isoformat(),
        "total_data_points": 2847,
        "average_price": 12.45,
        "median_price": 11.80,
        "min_price": 8.50,
        "max_price": 22.50,
        "price_range": 14.00,
        "standard_deviation": 3.24,
        "price_quartiles": {
            "q1": 10.20,
            "q2": 11.80,
            "q3": 14.60
        },
        "competitors": {
            "comp_1": {
                "name": "Odeon Cinemas",
                "average_price": 13.25,
                "median_price": 12.50,
                "min_price": 9.50,
                "max_price": 19.50,
                "price_points_count": 847,
                "standard_deviation": 2.84,
                "price_rank": 3,
                "position": "high"
            },
            "comp_2": {
                "name": "Cineworld", 
                "average_price": 11.95,
                "median_price": 11.80,
                "min_price": 9.20,
                "max_price": 18.80,
                "price_points_count": 756,
                "standard_deviation": 2.67,
                "price_rank": 2,
                "position": "mid"
            },
            "comp_3": {
                "name": "Vue Entertainment",
                "average_price": 11.45,
                "median_price": 11.20,
                "min_price": 8.50,
                "max_price": 17.90,
                "price_points_count": 623,
                "standard_deviation": 2.31,
                "price_rank": 1,
                "position": "low"
            }
        },
        "trends": {
            "trend": "increasing",
            "weekly_averages": {
                "2024-W30": 11.85,
                "2024-W31": 12.10,
                "2024-W32": 12.35,
                "2024-W33": 12.45
            },
            "price_change": 0.65,
            "price_change_percent": 5.2
        },
        "anomalies": [
            {
                "id": "anomaly_1",
                "competitor_name": "Premium Cinema",
                "product_service": "IMAX Adult Ticket",
                "price": 25.50,
                "z_score": 3.2,
                "date_collected": datetime.utcnow().isoformat(),
                "deviation_from_mean": 13.05,
                "severity": "high"
            }
        ]
    }


@router.get("/markets/{market_id}/trends")
async def get_pricing_trends(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    competitor_id: Optional[str] = Query(None),
    product_service: Optional[str] = Query(None),
    days_back: int = Query(90, ge=7, le=365)
):
    """Get pricing trends for a market (mock data for now)"""
    
    return {
        "period": {
            "start_date": datetime.utcnow().isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "days_back": days_back
        },
        "filters": {
            "competitor_id": competitor_id,
            "product_service": product_service
        },
        "market_trend": {
            "2024-W26": 11.20,
            "2024-W27": 11.35,
            "2024-W28": 11.55,
            "2024-W29": 11.70,
            "2024-W30": 11.85,
            "2024-W31": 12.10,
            "2024-W32": 12.35,
            "2024-W33": 12.45
        },
        "competitor_trends": {
            "comp_1": {
                "name": "Odeon Cinemas",
                "weekly_averages": {
                    "2024-W26": 12.85,
                    "2024-W27": 13.00,
                    "2024-W28": 13.15,
                    "2024-W29": 13.25,
                    "2024-W30": 13.40,
                    "2024-W31": 13.55,
                    "2024-W32": 13.65,
                    "2024-W33": 13.25
                }
            },
            "comp_2": {
                "name": "Cineworld",
                "weekly_averages": {
                    "2024-W26": 11.50,
                    "2024-W27": 11.65,
                    "2024-W28": 11.80,
                    "2024-W29": 11.90,
                    "2024-W30": 12.05,
                    "2024-W31": 12.15,
                    "2024-W32": 12.25,
                    "2024-W33": 11.95
                }
            },
            "comp_3": {
                "name": "Vue Entertainment", 
                "weekly_averages": {
                    "2024-W26": 10.95,
                    "2024-W27": 11.10,
                    "2024-W28": 11.25,
                    "2024-W29": 11.35,
                    "2024-W30": 11.50,
                    "2024-W31": 11.65,
                    "2024-W32": 11.75,
                    "2024-W33": 11.45
                }
            }
        },
        "data_points_count": 2847
    }


@router.get("/markets/{market_id}/comparison")
async def compare_competitors(
    market_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    competitor_ids: Optional[str] = Query(None, description="Comma-separated competitor IDs"),
    product_service: Optional[str] = Query(None)
):
    """Compare competitors in a market (mock data for now)"""
    
    return {
        "market_id": market_id,
        "product_service_filter": product_service,
        "comparison_period": {
            "start_date": datetime.utcnow().isoformat(),
            "end_date": datetime.utcnow().isoformat()
        },
        "competitors": {
            "comp_1": {
                "name": "Odeon Cinemas",
                "business_type": "Cinema Chain",
                "average_price": 13.25,
                "min_price": 9.50,
                "max_price": 19.50,
                "data_points": 847,
                "products_services": ["Standard Adult Ticket", "Premium Adult Ticket", "IMAX Adult Ticket"],
                "market_share_estimate": 35.5,
                "tracking_priority": 5,
                "price_rank": 3
            },
            "comp_2": {
                "name": "Cineworld",
                "business_type": "Cinema Chain", 
                "average_price": 11.95,
                "min_price": 9.20,
                "max_price": 18.80,
                "data_points": 756,
                "products_services": ["Standard Adult Ticket", "Premium Adult Ticket", "IMAX Adult Ticket"],
                "market_share_estimate": 28.2,
                "tracking_priority": 5,
                "price_rank": 2
            },
            "comp_3": {
                "name": "Vue Entertainment",
                "business_type": "Cinema Chain",
                "average_price": 11.45,
                "min_price": 8.50,
                "max_price": 17.90,
                "data_points": 623,
                "products_services": ["Standard Adult Ticket", "Premium Adult Ticket"],
                "market_share_estimate": 22.1,
                "tracking_priority": 4,
                "price_rank": 1
            }
        },
        "rankings": {
            "by_price": [
                {
                    "competitor_id": "comp_3",
                    "name": "Vue Entertainment",
                    "average_price": 11.45,
                    "rank": 1
                },
                {
                    "competitor_id": "comp_2",
                    "name": "Cineworld",
                    "average_price": 11.95,
                    "rank": 2
                },
                {
                    "competitor_id": "comp_1", 
                    "name": "Odeon Cinemas",
                    "average_price": 13.25,
                    "rank": 3
                }
            ]
        }
    }