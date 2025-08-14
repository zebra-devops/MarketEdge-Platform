from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from statistics import mean, median, stdev
import math
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from ..models.market_edge import (
    Market, Competitor, PricingData, MarketAlert, 
    CompetitiveInsight, MarketAnalytics
)


class MarketAnalysisService:
    """Service for market analysis and competitive intelligence"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_market_metrics(
        self, 
        market_id: str, 
        product_service: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Calculate comprehensive market metrics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Build base query
        query = self.db.query(PricingData).filter(
            PricingData.market_id == market_id,
            PricingData.date_collected >= start_date,
            PricingData.date_collected <= end_date
        )
        
        if product_service:
            query = query.filter(PricingData.product_service == product_service)
        
        pricing_data = query.all()
        
        if not pricing_data:
            return {"error": "No pricing data found for the specified criteria"}
        
        prices = [float(pd.price_point) for pd in pricing_data]
        
        # Basic statistics
        metrics = {
            "period_start": start_date,
            "period_end": end_date,
            "total_data_points": len(pricing_data),
            "average_price": round(mean(prices), 2),
            "median_price": round(median(prices), 2),
            "min_price": min(prices),
            "max_price": max(prices),
            "price_range": round(max(prices) - min(prices), 2),
            "standard_deviation": round(stdev(prices) if len(prices) > 1 else 0, 2)
        }
        
        # Price distribution
        metrics["price_quartiles"] = self._calculate_quartiles(prices)
        
        # Competitor analysis
        competitor_stats = self._analyze_competitors_pricing(pricing_data)
        metrics["competitors"] = competitor_stats
        
        # Trend analysis
        trend_data = self._analyze_pricing_trends(pricing_data)
        metrics["trends"] = trend_data
        
        # Anomaly detection
        anomalies = self._detect_price_anomalies(pricing_data)
        metrics["anomalies"] = anomalies
        
        return metrics
    
    def _calculate_quartiles(self, prices: List[float]) -> Dict[str, float]:
        """Calculate price quartiles"""
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        if n == 0:
            return {}
        
        return {
            "q1": round(sorted_prices[n // 4], 2),
            "q2": round(sorted_prices[n // 2], 2),  # Median
            "q3": round(sorted_prices[3 * n // 4], 2)
        }
    
    def _analyze_competitors_pricing(
        self, 
        pricing_data: List[PricingData]
    ) -> Dict[str, Any]:
        """Analyze pricing by competitor"""
        competitor_prices = {}
        
        for pd in pricing_data:
            competitor_id = pd.competitor_id
            if competitor_id not in competitor_prices:
                competitor_prices[competitor_id] = []
            competitor_prices[competitor_id].append(float(pd.price_point))
        
        competitor_stats = {}
        for comp_id, prices in competitor_prices.items():
            competitor = self.db.query(Competitor).filter(
                Competitor.id == comp_id
            ).first()
            
            competitor_stats[comp_id] = {
                "name": competitor.name if competitor else "Unknown",
                "average_price": round(mean(prices), 2),
                "median_price": round(median(prices), 2),
                "min_price": min(prices),
                "max_price": max(prices),
                "price_points_count": len(prices),
                "standard_deviation": round(stdev(prices) if len(prices) > 1 else 0, 2)
            }
        
        # Rank competitors by average price
        sorted_competitors = sorted(
            competitor_stats.items(),
            key=lambda x: x[1]["average_price"]
        )
        
        for i, (comp_id, stats) in enumerate(sorted_competitors):
            stats["price_rank"] = i + 1
            stats["position"] = "low" if i < len(sorted_competitors) / 3 else (
                "high" if i > 2 * len(sorted_competitors) / 3 else "mid"
            )
        
        return competitor_stats
    
    def _analyze_pricing_trends(
        self, 
        pricing_data: List[PricingData]
    ) -> Dict[str, Any]:
        """Analyze pricing trends over time"""
        # Group by week
        weekly_data = {}
        for pd in pricing_data:
            week_key = pd.date_collected.strftime("%Y-W%U")
            if week_key not in weekly_data:
                weekly_data[week_key] = []
            weekly_data[week_key].append(float(pd.price_point))
        
        if len(weekly_data) < 2:
            return {"trend": "insufficient_data"}
        
        # Calculate weekly averages
        weekly_averages = {
            week: mean(prices) for week, prices in weekly_data.items()
        }
        
        # Sort by week
        sorted_weeks = sorted(weekly_averages.items())
        if len(sorted_weeks) < 2:
            return {"trend": "insufficient_data"}
        
        # Calculate trend
        prices_timeline = [price for _, price in sorted_weeks]
        trend_direction = self._calculate_trend_direction(prices_timeline)
        
        return {
            "trend": trend_direction,
            "weekly_averages": dict(sorted_weeks),
            "price_change": round(prices_timeline[-1] - prices_timeline[0], 2),
            "price_change_percent": round(
                ((prices_timeline[-1] - prices_timeline[0]) / prices_timeline[0]) * 100, 2
            ) if prices_timeline[0] != 0 else 0
        }
    
    def _calculate_trend_direction(self, prices: List[float]) -> str:
        """Calculate overall trend direction"""
        if len(prices) < 2:
            return "stable"
        
        # Simple linear trend calculation
        n = len(prices)
        x_sum = sum(range(n))
        y_sum = sum(prices)
        xy_sum = sum(i * prices[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if abs(slope) < 0.01:  # Threshold for stability
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _detect_price_anomalies(
        self, 
        pricing_data: List[PricingData]
    ) -> List[Dict[str, Any]]:
        """Detect price anomalies using statistical methods"""
        if len(pricing_data) < 10:  # Need sufficient data for anomaly detection
            return []
        
        prices = [float(pd.price_point) for pd in pricing_data]
        mean_price = mean(prices)
        std_price = stdev(prices)
        
        # Z-score based anomaly detection
        anomalies = []
        threshold = 2.5  # Z-score threshold
        
        for pd in pricing_data:
            price = float(pd.price_point)
            z_score = abs((price - mean_price) / std_price) if std_price > 0 else 0
            
            if z_score > threshold:
                competitor = self.db.query(Competitor).filter(
                    Competitor.id == pd.competitor_id
                ).first()
                
                anomalies.append({
                    "id": pd.id,
                    "competitor_name": competitor.name if competitor else "Unknown",
                    "product_service": pd.product_service,
                    "price": price,
                    "z_score": round(z_score, 2),
                    "date_collected": pd.date_collected,
                    "deviation_from_mean": round(price - mean_price, 2),
                    "severity": "high" if z_score > 3 else "medium"
                })
        
        return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)
    
    def generate_competitive_insights(
        self, 
        market_id: str, 
        organisation_id: str
    ) -> List[Dict[str, Any]]:
        """Generate competitive insights for a market"""
        insights = []
        
        # Get recent metrics
        metrics = self.calculate_market_metrics(market_id)
        
        if "error" in metrics:
            return insights
        
        # Price positioning insight
        competitor_data = metrics.get("competitors", {})
        if competitor_data:
            insights.append(self._generate_price_positioning_insight(
                competitor_data, market_id, organisation_id
            ))
        
        # Trend insight
        trend_data = metrics.get("trends", {})
        if trend_data.get("trend") != "insufficient_data":
            insights.append(self._generate_trend_insight(
                trend_data, market_id, organisation_id
            ))
        
        # Anomaly insight
        anomalies = metrics.get("anomalies", [])
        if anomalies:
            insights.append(self._generate_anomaly_insight(
                anomalies, market_id, organisation_id
            ))
        
        return insights
    
    def _generate_price_positioning_insight(
        self,
        competitor_data: Dict[str, Any],
        market_id: str,
        organisation_id: str
    ) -> Dict[str, Any]:
        """Generate price positioning insight"""
        competitors = list(competitor_data.values())
        low_price_competitors = [c for c in competitors if c.get("position") == "low"]
        high_price_competitors = [c for c in competitors if c.get("position") == "high"]
        
        if low_price_competitors and high_price_competitors:
            price_gap = max(c["average_price"] for c in high_price_competitors) - \
                       min(c["average_price"] for c in low_price_competitors)
            
            return {
                "type": "pricing_positioning",
                "title": "Price Positioning Analysis",
                "description": f"Market shows {len(competitors)} active competitors with a price gap of £{price_gap:.2f}",
                "impact_score": min(10, price_gap / 10),  # Scale impact based on price gap
                "confidence_level": 0.85,
                "recommendations": [
                    "Consider competitive pricing strategy",
                    "Analyze value proposition differentiation",
                    "Monitor competitor pricing changes"
                ],
                "data_points": {
                    "total_competitors": len(competitors),
                    "price_gap": price_gap,
                    "low_price_leader": low_price_competitors[0]["name"],
                    "high_price_leader": high_price_competitors[0]["name"]
                }
            }
        
        return {}
    
    def _generate_trend_insight(
        self,
        trend_data: Dict[str, Any],
        market_id: str,
        organisation_id: str
    ) -> Dict[str, Any]:
        """Generate trend insight"""
        trend = trend_data.get("trend", "stable")
        price_change_percent = abs(trend_data.get("price_change_percent", 0))
        
        impact_score = min(10, price_change_percent / 5)  # Scale based on percentage change
        
        if trend == "increasing":
            title = "Rising Price Trend Detected"
            description = f"Market prices have increased by {price_change_percent:.1f}% recently"
        elif trend == "decreasing":
            title = "Declining Price Trend Detected" 
            description = f"Market prices have decreased by {price_change_percent:.1f}% recently"
        else:
            title = "Stable Market Pricing"
            description = "Market prices have remained relatively stable"
            impact_score = 2
        
        return {
            "type": "pricing_trend",
            "title": title,
            "description": description,
            "impact_score": impact_score,
            "confidence_level": 0.75,
            "recommendations": [
                "Monitor trend continuation",
                "Assess competitive response needs",
                "Review pricing strategy alignment"
            ],
            "data_points": {
                "trend_direction": trend,
                "price_change_percent": price_change_percent,
                "weekly_data": trend_data.get("weekly_averages", {})
            }
        }
    
    def _generate_anomaly_insight(
        self,
        anomalies: List[Dict[str, Any]],
        market_id: str,
        organisation_id: str
    ) -> Dict[str, Any]:
        """Generate anomaly insight"""
        high_severity_anomalies = [a for a in anomalies if a["severity"] == "high"]
        
        return {
            "type": "price_anomaly",
            "title": f"Price Anomalies Detected",
            "description": f"Found {len(anomalies)} price anomalies, {len(high_severity_anomalies)} high severity",
            "impact_score": min(10, len(high_severity_anomalies) * 2),
            "confidence_level": 0.90,
            "recommendations": [
                "Investigate unusual pricing patterns",
                "Verify data accuracy",
                "Consider competitive implications"
            ],
            "data_points": {
                "total_anomalies": len(anomalies),
                "high_severity_count": len(high_severity_anomalies),
                "anomalies": anomalies[:5]  # Top 5 anomalies
            }
        }
    
    def save_market_analytics(
        self,
        market_id: str,
        organisation_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Save market analytics to database"""
        period_start = metrics.get("period_start")
        period_end = metrics.get("period_end")
        
        # Save key metrics
        analytics_to_save = [
            ("average_price", metrics.get("average_price"), "average_price"),
            ("median_price", metrics.get("median_price"), "median_price"),
            ("price_range", metrics.get("price_range"), "price_range"),
            ("total_data_points", metrics.get("total_data_points"), "data_count"),
            ("competitor_count", len(metrics.get("competitors", {})), "competitor_count")
        ]
        
        for metric_name, metric_value, metric_type in analytics_to_save:
            if metric_value is not None:
                analytics = MarketAnalytics(
                    market_id=market_id,
                    organisation_id=organisation_id,
                    metric_name=metric_name,
                    metric_value=float(metric_value),
                    metric_type=metric_type,
                    period_start=period_start,
                    period_end=period_end,
                    calculation_method="statistical_analysis"
                )
                self.db.add(analytics)
        
        self.db.commit()
    
    def get_competitor_performance_ranking(
        self,
        market_id: str,
        metric: str = "average_price",
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get competitor performance ranking"""
        metrics = self.calculate_market_metrics(market_id, days_back=days_back)
        competitor_data = metrics.get("competitors", {})
        
        if not competitor_data:
            return []
        
        # Sort by the specified metric
        ranking = []
        for comp_id, stats in competitor_data.items():
            ranking.append({
                "competitor_id": comp_id,
                "name": stats["name"],
                "metric_value": stats.get(metric, 0),
                "rank": stats.get("price_rank", 0),
                "position": stats.get("position", "unknown"),
                "data_points": stats.get("price_points_count", 0)
            })
        
        return sorted(ranking, key=lambda x: x["metric_value"])
    
    def detect_significant_changes(
        self,
        market_id: str,
        threshold_percent: float = 10.0
    ) -> List[Dict[str, Any]]:
        """Detect significant price changes in the market"""
        # Compare last 7 days vs previous 7 days
        current_metrics = self.calculate_market_metrics(market_id, days_back=7)
        previous_metrics = self.calculate_market_metrics(
            market_id, 
            days_back=14
        )  # This would need more sophisticated date filtering
        
        changes = []
        
        # Compare average prices
        current_avg = current_metrics.get("average_price", 0)
        previous_avg = previous_metrics.get("average_price", 0)
        
        if previous_avg > 0:
            change_percent = ((current_avg - previous_avg) / previous_avg) * 100
            
            if abs(change_percent) >= threshold_percent:
                changes.append({
                    "type": "market_average_change",
                    "change_percent": round(change_percent, 2),
                    "current_value": current_avg,
                    "previous_value": previous_avg,
                    "significance": "high" if abs(change_percent) >= 20 else "medium"
                })
        
        return changes