from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, asc

from ..models.market_edge import (
    Market, Competitor, PricingData, MarketAlert, 
    CompetitiveInsight, UserMarketPreference
)
from .market_analysis import MarketAnalysisService


class CompetitiveIntelligenceService:
    """Service for competitive intelligence and competitor tracking"""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_analysis = MarketAnalysisService(db)
    
    def get_market_overview(
        self, 
        market_id: str, 
        organisation_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive market overview"""
        market = self.db.query(Market).filter(
            Market.id == market_id,
            Market.organisation_id == organisation_id
        ).first()
        
        if not market:
            return {"error": "Market not found"}
        
        # Get competitors
        competitors = self.db.query(Competitor).filter(
            Competitor.market_id == market_id,
            Competitor.organisation_id == organisation_id
        ).all()
        
        # Get recent pricing data
        recent_pricing = self.db.query(PricingData).filter(
            PricingData.market_id == market_id,
            PricingData.date_collected >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Get market metrics
        metrics = self.market_analysis.calculate_market_metrics(market_id)
        
        # Get recent alerts
        recent_alerts = self.db.query(MarketAlert).filter(
            MarketAlert.market_id == market_id,
            MarketAlert.organisation_id == organisation_id,
            MarketAlert.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(desc(MarketAlert.created_at)).limit(5).all()
        
        return {
            "market": {
                "id": market.id,
                "name": market.name,
                "is_active": market.is_active,
                "competitor_count": len(competitors),
                "created_at": market.created_at
            },
            "competitors": [
                {
                    "id": comp.id,
                    "name": comp.name,
                    "business_type": comp.business_type,
                    "tracking_priority": comp.tracking_priority,
                    "market_share_estimate": float(comp.market_share_estimate) if comp.market_share_estimate else None,
                    "last_updated": comp.last_updated
                }
                for comp in competitors
            ],
            "metrics": metrics,
            "recent_data_points": recent_pricing,
            "recent_alerts": [
                {
                    "id": alert.id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "message": alert.message,
                    "created_at": alert.created_at,
                    "is_read": alert.is_read
                }
                for alert in recent_alerts
            ]
        }
    
    def get_competitor_analysis(
        self, 
        competitor_id: str, 
        organisation_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get detailed competitor analysis"""
        competitor = self.db.query(Competitor).filter(
            Competitor.id == competitor_id,
            Competitor.organisation_id == organisation_id
        ).first()
        
        if not competitor:
            return {"error": "Competitor not found"}
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get pricing data
        pricing_data = self.db.query(PricingData).filter(
            PricingData.competitor_id == competitor_id,
            PricingData.date_collected >= start_date
        ).order_by(desc(PricingData.date_collected)).all()
        
        # Calculate competitor-specific metrics
        if pricing_data:
            prices = [float(pd.price_point) for pd in pricing_data]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            # Product/service breakdown
            product_breakdown = {}
            for pd in pricing_data:
                product = pd.product_service
                if product not in product_breakdown:
                    product_breakdown[product] = []
                product_breakdown[product].append(float(pd.price_point))
            
            product_stats = {}
            for product, prices in product_breakdown.items():
                product_stats[product] = {
                    "average_price": sum(prices) / len(prices),
                    "min_price": min(prices),
                    "max_price": max(prices),
                    "data_points": len(prices)
                }
        else:
            avg_price = min_price = max_price = 0
            product_stats = {}
        
        # Get market position
        market_metrics = self.market_analysis.calculate_market_metrics(
            competitor.market_id
        )
        market_avg = market_metrics.get("average_price", 0)
        
        position_vs_market = "unknown"
        if market_avg > 0 and avg_price > 0:
            if avg_price < market_avg * 0.9:
                position_vs_market = "below_market"
            elif avg_price > market_avg * 1.1:
                position_vs_market = "above_market"
            else:
                position_vs_market = "at_market"
        
        return {
            "competitor": {
                "id": competitor.id,
                "name": competitor.name,
                "business_type": competitor.business_type,
                "website": competitor.website,
                "tracking_priority": competitor.tracking_priority,
                "description": competitor.description,
                "market_share_estimate": float(competitor.market_share_estimate) if competitor.market_share_estimate else None,
                "locations": competitor.locations,
                "last_updated": competitor.last_updated
            },
            "pricing_metrics": {
                "average_price": round(avg_price, 2),
                "min_price": min_price,
                "max_price": max_price,
                "total_data_points": len(pricing_data),
                "position_vs_market": position_vs_market,
                "market_average": market_metrics.get("average_price", 0)
            },
            "product_breakdown": {
                product: {
                    "average_price": round(stats["average_price"], 2),
                    "min_price": stats["min_price"],
                    "max_price": stats["max_price"],
                    "data_points": stats["data_points"]
                }
                for product, stats in product_stats.items()
            },
            "recent_pricing": [
                {
                    "id": pd.id,
                    "product_service": pd.product_service,
                    "price_point": float(pd.price_point),
                    "currency": pd.currency,
                    "date_collected": pd.date_collected,
                    "source": pd.source,
                    "is_promotion": pd.is_promotion
                }
                for pd in pricing_data[:10]  # Last 10 data points
            ]
        }
    
    def compare_competitors(
        self,
        market_id: str,
        organisation_id: str,
        competitor_ids: Optional[List[str]] = None,
        product_service: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare multiple competitors side by side"""
        # Get competitors
        query = self.db.query(Competitor).filter(
            Competitor.market_id == market_id,
            Competitor.organisation_id == organisation_id
        )
        
        if competitor_ids:
            query = query.filter(Competitor.id.in_(competitor_ids))
        
        competitors = query.all()
        
        if not competitors:
            return {"error": "No competitors found"}
        
        # Get pricing data for comparison
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        comparison_data = {}
        
        for competitor in competitors:
            pricing_query = self.db.query(PricingData).filter(
                PricingData.competitor_id == competitor.id,
                PricingData.date_collected >= start_date
            )
            
            if product_service:
                pricing_query = pricing_query.filter(
                    PricingData.product_service == product_service
                )
            
            pricing_data = pricing_query.all()
            
            if pricing_data:
                prices = [float(pd.price_point) for pd in pricing_data]
                avg_price = sum(prices) / len(prices)
                
                # Get unique products/services
                products = list(set(pd.product_service for pd in pricing_data))
                
                comparison_data[competitor.id] = {
                    "name": competitor.name,
                    "business_type": competitor.business_type,
                    "average_price": round(avg_price, 2),
                    "min_price": min(prices),
                    "max_price": max(prices),
                    "data_points": len(pricing_data),
                    "products_services": products,
                    "market_share_estimate": float(competitor.market_share_estimate) if competitor.market_share_estimate else None,
                    "tracking_priority": competitor.tracking_priority
                }
            else:
                comparison_data[competitor.id] = {
                    "name": competitor.name,
                    "business_type": competitor.business_type,
                    "average_price": 0,
                    "min_price": 0,
                    "max_price": 0,
                    "data_points": 0,
                    "products_services": [],
                    "market_share_estimate": float(competitor.market_share_estimate) if competitor.market_share_estimate else None,
                    "tracking_priority": competitor.tracking_priority
                }
        
        # Rank competitors by average price
        ranked_competitors = sorted(
            comparison_data.items(),
            key=lambda x: x[1]["average_price"]
        )
        
        # Add rankings
        for i, (comp_id, data) in enumerate(ranked_competitors):
            data["price_rank"] = i + 1
        
        return {
            "market_id": market_id,
            "product_service_filter": product_service,
            "comparison_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "competitors": dict(comparison_data),
            "rankings": {
                "by_price": [
                    {
                        "competitor_id": comp_id,
                        "name": data["name"],
                        "average_price": data["average_price"],
                        "rank": data["price_rank"]
                    }
                    for comp_id, data in ranked_competitors
                ]
            }
        }
    
    def get_pricing_trends(
        self,
        market_id: str,
        organisation_id: str,
        competitor_id: Optional[str] = None,
        product_service: Optional[str] = None,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Get pricing trends over time"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Build query
        query = self.db.query(PricingData).filter(
            PricingData.market_id == market_id,
            PricingData.date_collected >= start_date,
            PricingData.date_collected <= end_date
        )
        
        if competitor_id:
            query = query.filter(PricingData.competitor_id == competitor_id)
        
        if product_service:
            query = query.filter(PricingData.product_service == product_service)
        
        pricing_data = query.order_by(PricingData.date_collected).all()
        
        if not pricing_data:
            return {"error": "No pricing data found"}
        
        # Group by week
        weekly_trends = {}
        competitor_trends = {}
        
        for pd in pricing_data:
            week_key = pd.date_collected.strftime("%Y-W%U")
            
            # Overall market trend
            if week_key not in weekly_trends:
                weekly_trends[week_key] = []
            weekly_trends[week_key].append(float(pd.price_point))
            
            # Per-competitor trend
            comp_id = pd.competitor_id
            if comp_id not in competitor_trends:
                competitor_trends[comp_id] = {}
            if week_key not in competitor_trends[comp_id]:
                competitor_trends[comp_id][week_key] = []
            competitor_trends[comp_id][week_key].append(float(pd.price_point))
        
        # Calculate weekly averages
        market_trend = {
            week: sum(prices) / len(prices) 
            for week, prices in weekly_trends.items()
        }
        
        competitor_trend_averages = {}
        for comp_id, weeks_data in competitor_trends.items():
            competitor = self.db.query(Competitor).filter(
                Competitor.id == comp_id
            ).first()
            
            competitor_trend_averages[comp_id] = {
                "name": competitor.name if competitor else "Unknown",
                "weekly_averages": {
                    week: sum(prices) / len(prices)
                    for week, prices in weeks_data.items()
                }
            }
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days_back": days_back
            },
            "filters": {
                "competitor_id": competitor_id,
                "product_service": product_service
            },
            "market_trend": dict(sorted(market_trend.items())),
            "competitor_trends": competitor_trend_averages,
            "data_points_count": len(pricing_data)
        }
    
    def detect_competitor_moves(
        self,
        market_id: str,
        organisation_id: str,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """Detect significant competitor moves or changes"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        moves = []
        
        # Get all competitors
        competitors = self.db.query(Competitor).filter(
            Competitor.market_id == market_id,
            Competitor.organisation_id == organisation_id
        ).all()
        
        for competitor in competitors:
            # Check for new pricing data
            recent_pricing = self.db.query(PricingData).filter(
                PricingData.competitor_id == competitor.id,
                PricingData.date_collected >= start_date
            ).count()
            
            if recent_pricing > 0:
                # Check for significant price changes
                current_avg = self.db.query(func.avg(PricingData.price_point)).filter(
                    PricingData.competitor_id == competitor.id,
                    PricingData.date_collected >= start_date
                ).scalar()
                
                previous_avg = self.db.query(func.avg(PricingData.price_point)).filter(
                    PricingData.competitor_id == competitor.id,
                    PricingData.date_collected >= start_date - timedelta(days=days_back),
                    PricingData.date_collected < start_date
                ).scalar()
                
                if current_avg and previous_avg:
                    change_percent = ((float(current_avg) - float(previous_avg)) / float(previous_avg)) * 100
                    
                    if abs(change_percent) >= 5:  # 5% threshold
                        moves.append({
                            "type": "price_change",
                            "competitor_id": competitor.id,
                            "competitor_name": competitor.name,
                            "change_type": "increase" if change_percent > 0 else "decrease",
                            "change_percent": round(change_percent, 2),
                            "current_average": round(float(current_avg), 2),
                            "previous_average": round(float(previous_avg), 2),
                            "significance": "high" if abs(change_percent) >= 15 else "medium",
                            "detected_at": datetime.utcnow()
                        })
            
            # Check for new products/services
            recent_products = set(
                pd.product_service for pd in 
                self.db.query(PricingData).filter(
                    PricingData.competitor_id == competitor.id,
                    PricingData.date_collected >= start_date
                ).all()
            )
            
            previous_products = set(
                pd.product_service for pd in
                self.db.query(PricingData).filter(
                    PricingData.competitor_id == competitor.id,
                    PricingData.date_collected < start_date,
                    PricingData.date_collected >= start_date - timedelta(days=30)
                ).all()
            )
            
            new_products = recent_products - previous_products
            if new_products:
                moves.append({
                    "type": "new_products",
                    "competitor_id": competitor.id,
                    "competitor_name": competitor.name,
                    "new_products": list(new_products),
                    "significance": "medium",
                    "detected_at": datetime.utcnow()
                })
        
        return sorted(moves, key=lambda x: x["detected_at"], reverse=True)
    
    def generate_market_report(
        self,
        market_id: str,
        organisation_id: str,
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate comprehensive market report"""
        market_overview = self.get_market_overview(market_id, organisation_id)
        
        if "error" in market_overview:
            return market_overview
        
        # Get competitor comparison
        competitor_comparison = self.compare_competitors(market_id, organisation_id)
        
        # Get pricing trends
        pricing_trends = self.get_pricing_trends(market_id, organisation_id)
        
        # Get competitor moves
        competitor_moves = self.detect_competitor_moves(market_id, organisation_id)
        
        # Generate insights
        insights = self.market_analysis.generate_competitive_insights(
            market_id, organisation_id
        )
        
        return {
            "report_type": report_type,
            "generated_at": datetime.utcnow(),
            "market_overview": market_overview,
            "competitor_analysis": competitor_comparison,
            "pricing_trends": pricing_trends,
            "recent_moves": competitor_moves,
            "insights": insights,
            "summary": {
                "total_competitors": len(market_overview.get("competitors", [])),
                "active_alerts": len([
                    a for a in market_overview.get("recent_alerts", []) 
                    if not a["is_read"]
                ]),
                "recent_moves": len(competitor_moves),
                "key_insights": len(insights)
            }
        }
    
    def save_user_preferences(
        self,
        user_id: str,
        market_id: str,
        preferences: Dict[str, Any]
    ) -> None:
        """Save user market preferences"""
        existing = self.db.query(UserMarketPreference).filter(
            UserMarketPreference.user_id == user_id,
            UserMarketPreference.market_id == market_id
        ).first()
        
        if existing:
            existing.dashboard_config = preferences.get("dashboard_config")
            existing.alert_preferences = preferences.get("alert_preferences")
            existing.favorite_competitors = preferences.get("favorite_competitors")
            existing.updated_at = datetime.utcnow()
        else:
            new_pref = UserMarketPreference(
                user_id=user_id,
                market_id=market_id,
                dashboard_config=preferences.get("dashboard_config"),
                alert_preferences=preferences.get("alert_preferences"),
                favorite_competitors=preferences.get("favorite_competitors")
            )
            self.db.add(new_pref)
        
        self.db.commit()
    
    def get_user_preferences(
        self,
        user_id: str,
        market_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user market preferences"""
        pref = self.db.query(UserMarketPreference).filter(
            UserMarketPreference.user_id == user_id,
            UserMarketPreference.market_id == market_id
        ).first()
        
        if not pref:
            return None
        
        return {
            "dashboard_config": pref.dashboard_config,
            "alert_preferences": pref.alert_preferences,
            "favorite_competitors": pref.favorite_competitors,
            "updated_at": pref.updated_at
        }