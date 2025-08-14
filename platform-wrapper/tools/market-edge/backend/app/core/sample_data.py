import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..models.market_edge import (
    Market, Competitor, PricingData, MarketAlert, 
    CompetitiveInsight, MarketAnalytics
)


class SampleDataGenerator:
    """Generate realistic sample data for Market Edge"""
    
    def __init__(self, db: Session, organisation_id: str, user_id: str):
        self.db = db
        self.organisation_id = organisation_id
        self.user_id = user_id
    
    def generate_cinema_market_data(self) -> str:
        """Generate UK cinema market data"""
        # Create market
        market = Market(
            name="UK Cinema Market",
            geographic_bounds={
                "country": "United Kingdom",
                "regions": ["England", "Scotland", "Wales", "Northern Ireland"],
                "focus_cities": ["London", "Manchester", "Birmingham", "Glasgow", "Cardiff"]
            },
            organisation_id=self.organisation_id,
            created_by=self.user_id,
            tracking_config={
                "price_tracking": True,
                "promotion_tracking": True,
                "location_tracking": True,
                "alert_thresholds": {
                    "price_change_percent": 10,
                    "new_competitor": True
                }
            }
        )
        self.db.add(market)
        self.db.flush()
        market_id = market.id
        
        # Create competitors
        competitors_data = [
            {
                "name": "Odeon Cinemas",
                "business_type": "Cinema Chain",
                "website": "https://www.odeon.co.uk",
                "market_share": 35.5,
                "locations": {"total_locations": 120, "major_cities": 45},
                "priority": 5
            },
            {
                "name": "Cineworld",
                "business_type": "Cinema Chain", 
                "website": "https://www.cineworld.co.uk",
                "market_share": 28.2,
                "locations": {"total_locations": 99, "major_cities": 38},
                "priority": 5
            },
            {
                "name": "Vue Entertainment",
                "business_type": "Cinema Chain",
                "website": "https://www.myvue.com",
                "market_share": 22.1,
                "locations": {"total_locations": 91, "major_cities": 34},
                "priority": 4
            },
            {
                "name": "Showcase Cinemas",
                "business_type": "Cinema Chain",
                "website": "https://www.showcasecinemas.co.uk",
                "market_share": 8.7,
                "locations": {"total_locations": 21, "major_cities": 15},
                "priority": 3
            },
            {
                "name": "Everyman Cinema",
                "business_type": "Boutique Cinema",
                "website": "https://www.everymancinema.com",
                "market_share": 2.1,
                "locations": {"total_locations": 35, "major_cities": 12},
                "priority": 2
            },
            {
                "name": "Curzon Cinemas",
                "business_type": "Art House Cinema",
                "website": "https://www.curzoncinemas.com",
                "market_share": 1.8,
                "locations": {"total_locations": 16, "major_cities": 8},
                "priority": 2
            }
        ]
        
        competitors = []
        for comp_data in competitors_data:
            competitor = Competitor(
                name=comp_data["name"],
                market_id=market_id,
                organisation_id=self.organisation_id,
                business_type=comp_data["business_type"],
                website=comp_data["website"],
                locations=comp_data["locations"],
                tracking_priority=comp_data["priority"],
                market_share_estimate=comp_data["market_share"],
                description=f"Major {comp_data['business_type'].lower()} operating across the UK"
            )
            self.db.add(competitor)
            competitors.append(competitor)
        
        self.db.flush()
        
        # Generate pricing data for last 90 days
        self._generate_cinema_pricing_data(competitors)
        
        # Update market competitor count
        market.competitor_count = len(competitors)
        self.db.commit()
        
        return market_id
    
    def generate_hotel_market_data(self) -> str:
        """Generate Manchester hotel market data"""
        # Create market
        market = Market(
            name="Manchester Hotel Market",
            geographic_bounds={
                "city": "Manchester",
                "region": "Greater Manchester",
                "country": "United Kingdom",
                "coordinates": {"lat": 53.4808, "lng": -2.2426}
            },
            organisation_id=self.organisation_id,
            created_by=self.user_id,
            tracking_config={
                "price_tracking": True,
                "occupancy_tracking": True,
                "seasonal_analysis": True,
                "alert_thresholds": {
                    "price_change_percent": 15,
                    "occupancy_change": 20
                }
            }
        )
        self.db.add(market)
        self.db.flush()
        market_id = market.id
        
        # Create competitors
        competitors_data = [
            {
                "name": "Premier Inn Manchester",
                "business_type": "Budget Hotel Chain",
                "website": "https://www.premierinn.com",
                "market_share": 18.5,
                "locations": {"properties": 12, "rooms": 1800},
                "priority": 5
            },
            {
                "name": "Travelodge Manchester",
                "business_type": "Budget Hotel Chain",
                "website": "https://www.travelodge.co.uk",
                "market_share": 15.2,
                "locations": {"properties": 8, "rooms": 1200},
                "priority": 5
            },
            {
                "name": "Holiday Inn Manchester",
                "business_type": "Mid-Range Hotel",
                "website": "https://www.ihg.com",
                "market_share": 12.8,
                "locations": {"properties": 5, "rooms": 850},
                "priority": 4
            },
            {
                "name": "Ibis Manchester",
                "business_type": "Budget Hotel Chain",
                "website": "https://www.ibis.com",
                "market_share": 8.9,
                "locations": {"properties": 3, "rooms": 600},
                "priority": 3
            },
            {
                "name": "Malmaison Manchester",
                "business_type": "Boutique Hotel",
                "website": "https://www.malmaison.com",
                "market_share": 4.2,
                "locations": {"properties": 1, "rooms": 167},
                "priority": 3
            }
        ]
        
        competitors = []
        for comp_data in competitors_data:
            competitor = Competitor(
                name=comp_data["name"],
                market_id=market_id,
                organisation_id=self.organisation_id,
                business_type=comp_data["business_type"],
                website=comp_data["website"],
                locations=comp_data["locations"],
                tracking_priority=comp_data["priority"],
                market_share_estimate=comp_data["market_share"],
                description=f"{comp_data['business_type']} with strong presence in Manchester"
            )
            self.db.add(competitor)
            competitors.append(competitor)
        
        self.db.flush()
        
        # Generate pricing data
        self._generate_hotel_pricing_data(competitors)
        
        # Update market competitor count
        market.competitor_count = len(competitors)
        self.db.commit()
        
        return market_id
    
    def generate_restaurant_market_data(self) -> str:
        """Generate London restaurant market data"""
        # Create market
        market = Market(
            name="London Fast Casual Restaurant Market",
            geographic_bounds={
                "city": "London",
                "region": "Greater London",
                "country": "United Kingdom",
                "focus_areas": ["Central London", "Canary Wharf", "Kings Cross", "Shoreditch"]
            },
            organisation_id=self.organisation_id,
            created_by=self.user_id,
            tracking_config={
                "price_tracking": True,
                "menu_tracking": True,
                "delivery_tracking": True,
                "alert_thresholds": {
                    "price_change_percent": 8,
                    "menu_changes": True
                }
            }
        )
        self.db.add(market)
        self.db.flush()
        market_id = market.id
        
        # Create competitors
        competitors_data = [
            {
                "name": "Pret A Manger",
                "business_type": "Fast Casual Restaurant",
                "website": "https://www.pret.co.uk",
                "market_share": 22.4,
                "locations": {"london_stores": 350, "total_uk": 450},
                "priority": 5
            },
            {
                "name": "Leon",
                "business_type": "Healthy Fast Food",
                "website": "https://www.leon.co",
                "market_share": 8.9,
                "locations": {"london_stores": 75, "total_uk": 120},
                "priority": 4
            },
            {
                "name": "Wasabi",
                "business_type": "Sushi Fast Food",
                "website": "https://www.wasabi.uk.com",
                "market_share": 5.2,
                "locations": {"london_stores": 45, "total_uk": 55},
                "priority": 3
            },
            {
                "name": "Itsu",
                "business_type": "Asian Fast Casual",
                "website": "https://www.itsu.com",
                "market_share": 4.8,
                "locations": {"london_stores": 35, "total_uk": 70},
                "priority": 3
            },
            {
                "name": "Tortilla",
                "business_type": "Mexican Fast Casual",
                "website": "https://www.tortilla.co.uk",
                "market_share": 3.1,
                "locations": {"london_stores": 25, "total_uk": 65},
                "priority": 2
            }
        ]
        
        competitors = []
        for comp_data in competitors_data:
            competitor = Competitor(
                name=comp_data["name"],
                market_id=market_id,
                organisation_id=self.organisation_id,
                business_type=comp_data["business_type"],
                website=comp_data["website"],
                locations=comp_data["locations"],
                tracking_priority=comp_data["priority"],
                market_share_estimate=comp_data["market_share"],
                description=f"{comp_data['business_type']} chain with strong London presence"
            )
            self.db.add(competitor)
            competitors.append(competitor)
        
        self.db.flush()
        
        # Generate pricing data
        self._generate_restaurant_pricing_data(competitors)
        
        # Update market competitor count
        market.competitor_count = len(competitors)
        self.db.commit()
        
        return market_id
    
    def _generate_cinema_pricing_data(self, competitors: List[Competitor]):
        """Generate cinema pricing data"""
        products = [
            "Standard Adult Ticket",
            "Standard Child Ticket", 
            "Premium Adult Ticket",
            "Premium Child Ticket",
            "IMAX Adult Ticket",
            "IMAX Child Ticket",
            "Small Popcorn",
            "Large Popcorn",
            "Soft Drink Medium",
            "Soft Drink Large"
        ]
        
        # Base prices by competitor and product
        base_prices = {
            "Odeon Cinemas": {
                "Standard Adult Ticket": 12.50, "Standard Child Ticket": 9.50,
                "Premium Adult Ticket": 16.50, "Premium Child Ticket": 13.50,
                "IMAX Adult Ticket": 19.50, "IMAX Child Ticket": 16.50,
                "Small Popcorn": 4.50, "Large Popcorn": 6.50,
                "Soft Drink Medium": 3.80, "Soft Drink Large": 4.80
            },
            "Cineworld": {
                "Standard Adult Ticket": 11.80, "Standard Child Ticket": 9.20,
                "Premium Adult Ticket": 15.80, "Premium Child Ticket": 12.80,
                "IMAX Adult Ticket": 18.80, "IMAX Child Ticket": 15.80,
                "Small Popcorn": 4.20, "Large Popcorn": 6.20,
                "Soft Drink Medium": 3.60, "Soft Drink Large": 4.60
            },
            "Vue Entertainment": {
                "Standard Adult Ticket": 11.20, "Standard Child Ticket": 8.50,
                "Premium Adult Ticket": 14.90, "Premium Child Ticket": 11.90,
                "IMAX Adult Ticket": 17.90, "IMAX Child Ticket": 14.90,
                "Small Popcorn": 4.00, "Large Popcorn": 5.80,
                "Soft Drink Medium": 3.40, "Soft Drink Large": 4.40
            },
            "Showcase Cinemas": {
                "Standard Adult Ticket": 10.50, "Standard Child Ticket": 8.00,
                "Premium Adult Ticket": 13.50, "Premium Child Ticket": 10.50,
                "IMAX Adult Ticket": 16.50, "IMAX Child Ticket": 13.50,
                "Small Popcorn": 3.80, "Large Popcorn": 5.50,
                "Soft Drink Medium": 3.20, "Soft Drink Large": 4.20
            },
            "Everyman Cinema": {
                "Standard Adult Ticket": 18.50, "Standard Child Ticket": 15.50,
                "Premium Adult Ticket": 22.50, "Premium Child Ticket": 19.50,
                "Small Popcorn": 5.50, "Large Popcorn": 7.50,
                "Soft Drink Medium": 4.50, "Soft Drink Large": 5.50
            },
            "Curzon Cinemas": {
                "Standard Adult Ticket": 16.50, "Standard Child Ticket": 13.50,
                "Premium Adult Ticket": 19.50, "Premium Child Ticket": 16.50,
                "Small Popcorn": 5.00, "Large Popcorn": 7.00,
                "Soft Drink Medium": 4.20, "Soft Drink Large": 5.20
            }
        }
        
        # Generate 90 days of data
        end_date = datetime.utcnow()
        
        for competitor in competitors:
            comp_base_prices = base_prices.get(competitor.name, {})
            
            for days_ago in range(90):
                current_date = end_date - timedelta(days=days_ago)
                
                # Generate 2-5 price points per day
                num_prices = random.randint(2, 5)
                available_products = [p for p in products if p in comp_base_prices]
                
                for _ in range(num_prices):
                    if not available_products:
                        continue
                        
                    product = random.choice(available_products)
                    base_price = comp_base_prices[product]
                    
                    # Add some variation (±10%)
                    variation = random.uniform(-0.1, 0.1)
                    price = base_price * (1 + variation)
                    
                    # Weekend premium
                    if current_date.weekday() >= 5:  # Saturday/Sunday
                        price *= 1.15
                    
                    # Holiday seasons (rough approximation)
                    if current_date.month in [12, 7, 8]:  # Christmas, summer holidays
                        price *= 1.05
                    
                    # Random promotions (5% chance)
                    is_promotion = random.random() < 0.05
                    if is_promotion:
                        price *= 0.85  # 15% discount
                    
                    pricing_data = PricingData(
                        competitor_id=competitor.id,
                        market_id=competitor.market_id,
                        product_service=product,
                        price_point=round(price, 2),
                        currency="GBP",
                        date_collected=current_date,
                        source="automated_scraping",
                        is_promotion=is_promotion,
                        promotion_details="Weekend Special" if is_promotion else None,
                        metadata={
                            "day_of_week": current_date.strftime("%A"),
                            "is_weekend": current_date.weekday() >= 5,
                            "collection_time": current_date.strftime("%H:%M")
                        }
                    )
                    
                    self.db.add(pricing_data)
    
    def _generate_hotel_pricing_data(self, competitors: List[Competitor]):
        """Generate hotel pricing data"""
        room_types = [
            "Standard Room",
            "Superior Room", 
            "Executive Room",
            "Suite",
            "Family Room"
        ]
        
        # Base prices by competitor and room type
        base_prices = {
            "Premier Inn Manchester": {
                "Standard Room": 75, "Superior Room": 95, "Family Room": 110
            },
            "Travelodge Manchester": {
                "Standard Room": 65, "Superior Room": 85, "Family Room": 95
            },
            "Holiday Inn Manchester": {
                "Standard Room": 95, "Superior Room": 125, "Executive Room": 155, "Suite": 195
            },
            "Ibis Manchester": {
                "Standard Room": 70, "Superior Room": 90
            },
            "Malmaison Manchester": {
                "Standard Room": 140, "Superior Room": 180, "Suite": 280
            }
        }
        
        end_date = datetime.utcnow()
        
        for competitor in competitors:
            comp_base_prices = base_prices.get(competitor.name, {})
            
            for days_ago in range(90):
                current_date = end_date - timedelta(days=days_ago)
                
                # Generate 1-3 room type prices per day
                available_rooms = list(comp_base_prices.keys())
                num_prices = min(random.randint(1, 3), len(available_rooms))
                
                for room_type in random.sample(available_rooms, num_prices):
                    base_price = comp_base_prices[room_type]
                    
                    # Weekend premium
                    if current_date.weekday() >= 5:
                        price = base_price * 1.4
                    else:
                        price = base_price * random.uniform(0.9, 1.2)
                    
                    # Event-based pricing (random events)
                    if random.random() < 0.15:  # 15% chance of event
                        price *= random.uniform(1.5, 2.2)  # Event premium
                    
                    # Seasonal variation
                    if current_date.month in [12, 7, 8]:
                        price *= 1.25
                    elif current_date.month in [1, 2]:
                        price *= 0.85
                    
                    pricing_data = PricingData(
                        competitor_id=competitor.id,
                        market_id=competitor.market_id,
                        product_service=room_type,
                        price_point=round(price, 2),
                        currency="GBP",
                        date_collected=current_date,
                        source="booking_platform_api",
                        metadata={
                            "booking_date": current_date.strftime("%Y-%m-%d"),
                            "is_weekend": current_date.weekday() >= 5,
                            "occupancy_rate": random.uniform(60, 95)
                        }
                    )
                    
                    self.db.add(pricing_data)
    
    def _generate_restaurant_pricing_data(self, competitors: List[Competitor]):
        """Generate restaurant pricing data"""
        menu_items = [
            "Sandwich Classic",
            "Sandwich Premium",
            "Salad Bowl",
            "Hot Food Main",
            "Soup Cup",
            "Coffee Regular",
            "Coffee Large",
            "Smoothie",
            "Snack Pack",
            "Meal Deal"
        ]
        
        # Base prices by competitor
        base_prices = {
            "Pret A Manger": {
                "Sandwich Classic": 4.50, "Sandwich Premium": 5.75, "Salad Bowl": 5.95,
                "Hot Food Main": 6.25, "Soup Cup": 3.95, "Coffee Regular": 2.40,
                "Coffee Large": 2.75, "Smoothie": 4.25, "Snack Pack": 2.95, "Meal Deal": 8.50
            },
            "Leon": {
                "Sandwich Classic": 4.75, "Sandwich Premium": 6.25, "Salad Bowl": 6.50,
                "Hot Food Main": 7.25, "Soup Cup": 4.25, "Coffee Regular": 2.60,
                "Coffee Large": 2.95, "Smoothie": 4.95, "Snack Pack": 3.25, "Meal Deal": 9.50
            },
            "Wasabi": {
                "Sandwich Classic": 3.95, "Hot Food Main": 5.95, "Soup Cup": 3.50,
                "Coffee Regular": 2.30, "Smoothie": 3.95, "Snack Pack": 2.75, "Meal Deal": 7.95
            },
            "Itsu": {
                "Sandwich Classic": 4.25, "Salad Bowl": 5.75, "Hot Food Main": 6.75,
                "Soup Cup": 3.75, "Coffee Regular": 2.50, "Smoothie": 4.50, "Meal Deal": 8.95
            },
            "Tortilla": {
                "Hot Food Main": 6.95, "Salad Bowl": 6.45, "Coffee Regular": 2.20,
                "Smoothie": 3.75, "Snack Pack": 2.95, "Meal Deal": 9.25
            }
        }
        
        end_date = datetime.utcnow()
        
        for competitor in competitors:
            comp_base_prices = base_prices.get(competitor.name, {})
            
            for days_ago in range(90):
                current_date = end_date - timedelta(days=days_ago)
                
                # Generate 3-6 menu items per day
                available_items = list(comp_base_prices.keys())
                num_prices = min(random.randint(3, 6), len(available_items))
                
                for item in random.sample(available_items, num_prices):
                    base_price = comp_base_prices[item]
                    
                    # Small daily variation
                    price = base_price * random.uniform(0.95, 1.05)
                    
                    # Lunch premium (11-14h)
                    if 11 <= current_date.hour <= 14:
                        price *= 1.02
                    
                    # Random promotions (3% chance)
                    is_promotion = random.random() < 0.03
                    if is_promotion:
                        price *= 0.9  # 10% discount
                    
                    pricing_data = PricingData(
                        competitor_id=competitor.id,
                        market_id=competitor.market_id,
                        product_service=item,
                        price_point=round(price, 2),
                        currency="GBP",
                        date_collected=current_date,
                        source="menu_tracking",
                        is_promotion=is_promotion,
                        promotion_details="Lunch Special" if is_promotion else None,
                        metadata={
                            "meal_period": self._get_meal_period(current_date.hour),
                            "location_zone": random.choice(["Central", "Canary Wharf", "Kings Cross"]),
                            "day_of_week": current_date.strftime("%A")
                        }
                    )
                    
                    self.db.add(pricing_data)
    
    def _get_meal_period(self, hour: int) -> str:
        """Get meal period based on hour"""
        if 6 <= hour < 11:
            return "breakfast"
        elif 11 <= hour < 16:
            return "lunch"
        elif 16 <= hour < 22:
            return "dinner"
        else:
            return "late_night"
    
    def generate_sample_alerts(self, market_id: str):
        """Generate sample alerts for a market"""
        alert_types = [
            {
                "type": "price_change",
                "title": "Significant Price Increase Detected",
                "message": "Odeon Cinemas has increased IMAX ticket prices by 12% across London venues",
                "severity": "medium"
            },
            {
                "type": "new_competitor",
                "title": "New Competitor Detected",
                "message": "New cinema chain 'Luxe Cinemas' has opened 3 locations in Manchester area",
                "severity": "high"
            },
            {
                "type": "anomaly",
                "title": "Pricing Anomaly Alert",
                "message": "Vue Entertainment showing unusual pricing patterns for weekend showtimes",
                "severity": "low"
            },
            {
                "type": "promotion",
                "title": "Competitor Promotion Launched",
                "message": "Cineworld launched '50% off Tuesdays' promotion across all UK venues",
                "severity": "medium"
            }
        ]
        
        # Generate 3-5 alerts over the last week
        end_date = datetime.utcnow()
        
        for i in range(random.randint(3, 5)):
            alert_data = random.choice(alert_types)
            alert_date = end_date - timedelta(days=random.randint(0, 7))
            
            alert = MarketAlert(
                market_id=market_id,
                organisation_id=self.organisation_id,
                alert_type=alert_data["type"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                message=alert_data["message"],
                trigger_data={
                    "detected_at": alert_date.isoformat(),
                    "confidence": random.uniform(0.7, 0.95),
                    "affected_competitors": random.randint(1, 3)
                },
                is_read=random.choice([True, False]),
                created_at=alert_date
            )
            
            self.db.add(alert)
        
        self.db.commit()
    
    def generate_all_sample_data(self) -> Dict[str, str]:
        """Generate all sample market data"""
        market_ids = {}
        
        # Generate cinema market
        cinema_market_id = self.generate_cinema_market_data()
        market_ids["cinema"] = cinema_market_id
        self.generate_sample_alerts(cinema_market_id)
        
        # Generate hotel market
        hotel_market_id = self.generate_hotel_market_data()
        market_ids["hotel"] = hotel_market_id
        self.generate_sample_alerts(hotel_market_id)
        
        # Generate restaurant market
        restaurant_market_id = self.generate_restaurant_market_data()
        market_ids["restaurant"] = restaurant_market_id
        self.generate_sample_alerts(restaurant_market_id)
        
        return market_ids