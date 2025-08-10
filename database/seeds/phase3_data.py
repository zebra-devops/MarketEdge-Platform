"""
Seed data for Phase 3 enhancements:
- UK SIC codes for supported sectors
- Initial analytics modules
- Default feature flags
- Competitive factor templates
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append('/app')

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.models.sectors import SICCode, CompetitiveFactorTemplate
from app.models.modules import AnalyticsModule, ModuleType, ModuleStatus
from app.models.feature_flags import FeatureFlag, FeatureFlagScope, FeatureFlagStatus
from app.models.user import User


async def seed_sic_codes(db: AsyncSession):
    """Seed UK SIC codes for supported sectors"""
    
    sic_codes_data = [
        {
            "code": "59140",
            "section": "J",
            "division": "59",
            "group": "59.1",
            "class_code": "59.14",
            "title": "Motion picture projection activities",
            "description": "This class includes: - motion picture or videotape projection in cinemas, in the open air or in other projection facilities; - activities of cine-clubs",
            "is_supported": True,
            "competitive_factors": {
                "pricing": {
                    "ticket_prices": {"weight": 0.9, "required": True},
                    "concession_prices": {"weight": 0.7, "required": False},
                    "membership_pricing": {"weight": 0.6, "required": False}
                },
                "experience": {
                    "screen_technology": {"weight": 0.8, "required": False},
                    "seating_comfort": {"weight": 0.7, "required": False},
                    "audio_quality": {"weight": 0.8, "required": False}
                },
                "location": {
                    "accessibility": {"weight": 0.9, "required": True},
                    "parking_availability": {"weight": 0.6, "required": False},
                    "transport_links": {"weight": 0.7, "required": False}
                }
            },
            "default_metrics": [
                "average_ticket_price",
                "peak_pricing",
                "concession_revenue_per_customer",
                "screen_utilization",
                "customer_satisfaction"
            ],
            "analytics_config": {
                "price_monitoring": {
                    "frequency": "hourly",
                    "products": ["standard_ticket", "premium_ticket", "imax_ticket", "concessions"]
                },
                "competitive_analysis": {
                    "radius_km": 10,
                    "key_competitors": 5
                }
            }
        },
        {
            "code": "55100",
            "section": "I",
            "division": "55",
            "group": "55.1",
            "class_code": "55.10",
            "title": "Hotels and similar accommodation",
            "description": "This class includes the provision of accommodation, typically on a daily or weekly basis, principally for short stays by visitors",
            "is_supported": True,
            "competitive_factors": {
                "pricing": {
                    "room_rates": {"weight": 0.9, "required": True},
                    "seasonal_pricing": {"weight": 0.8, "required": False},
                    "package_deals": {"weight": 0.7, "required": False}
                },
                "amenities": {
                    "room_quality": {"weight": 0.8, "required": True},
                    "facilities": {"weight": 0.7, "required": False},
                    "dining_options": {"weight": 0.6, "required": False}
                },
                "service": {
                    "staff_quality": {"weight": 0.8, "required": False},
                    "booking_flexibility": {"weight": 0.7, "required": False},
                    "customer_service": {"weight": 0.9, "required": True}
                }
            },
            "default_metrics": [
                "average_daily_rate",
                "occupancy_rate",
                "revenue_per_available_room",
                "guest_satisfaction_score",
                "booking_conversion_rate"
            ],
            "analytics_config": {
                "price_monitoring": {
                    "frequency": "daily",
                    "products": ["standard_room", "deluxe_room", "suite", "packages"]
                },
                "occupancy_tracking": {
                    "seasonal_analysis": True,
                    "demand_forecasting": True
                }
            }
        },
        {
            "code": "93130",
            "section": "R",
            "division": "93",
            "group": "93.1",
            "class_code": "93.13",
            "title": "Fitness facilities",
            "description": "This class includes the operation of fitness and bodybuilding clubs and facilities",
            "is_supported": True,
            "competitive_factors": {
                "pricing": {
                    "membership_fees": {"weight": 0.9, "required": True},
                    "class_pricing": {"weight": 0.7, "required": False},
                    "personal_training": {"weight": 0.6, "required": False}
                },
                "facilities": {
                    "equipment_quality": {"weight": 0.8, "required": True},
                    "facility_cleanliness": {"weight": 0.9, "required": True},
                    "class_variety": {"weight": 0.7, "required": False}
                },
                "convenience": {
                    "opening_hours": {"weight": 0.8, "required": False},
                    "location_accessibility": {"weight": 0.9, "required": True},
                    "booking_system": {"weight": 0.6, "required": False}
                }
            },
            "default_metrics": [
                "membership_pricing",
                "class_attendance_rates",
                "member_retention_rate",
                "facility_utilization",
                "customer_satisfaction"
            ],
            "analytics_config": {
                "price_monitoring": {
                    "frequency": "weekly",
                    "products": ["monthly_membership", "annual_membership", "day_pass", "classes"]
                },
                "utilization_tracking": {
                    "peak_hours_analysis": True,
                    "capacity_planning": True
                }
            }
        },
        {
            "code": "47520",
            "section": "G",
            "division": "47",
            "group": "47.5",
            "class_code": "47.52",
            "title": "Retail sale of hardware, paints and glass in specialised stores",
            "description": "This class includes retail sale in specialised stores of: hardware, paints, varnishes and lacquers, flat glass, other building materials",
            "is_supported": True,
            "competitive_factors": {
                "pricing": {
                    "product_pricing": {"weight": 0.9, "required": True},
                    "bulk_discounts": {"weight": 0.7, "required": False},
                    "seasonal_promotions": {"weight": 0.6, "required": False}
                },
                "inventory": {
                    "product_range": {"weight": 0.8, "required": True},
                    "stock_availability": {"weight": 0.9, "required": True},
                    "brand_variety": {"weight": 0.7, "required": False}
                },
                "service": {
                    "expert_advice": {"weight": 0.8, "required": False},
                    "delivery_options": {"weight": 0.7, "required": False},
                    "return_policy": {"weight": 0.6, "required": False}
                }
            },
            "default_metrics": [
                "average_product_price",
                "inventory_turnover",
                "price_competitiveness",
                "customer_footfall",
                "sales_conversion_rate"
            ],
            "analytics_config": {
                "price_monitoring": {
                    "frequency": "daily",
                    "products": ["tools", "paint", "hardware", "building_materials"]
                },
                "inventory_tracking": {
                    "stock_level_monitoring": True,
                    "demand_forecasting": True
                }
            }
        }
    ]
    
    for sic_data in sic_codes_data:
        # Check if SIC code already exists
        result = await db.execute(select(SICCode).where(SICCode.code == sic_data["code"]))
        existing = result.scalar_one_or_none()
        
        if not existing:
            sic_code = SICCode(**sic_data)
            db.add(sic_code)
    
    await db.commit()
    print(f"✅ Seeded {len(sic_codes_data)} SIC codes")


async def seed_analytics_modules(db: AsyncSession):
    """Seed initial analytics modules"""
    
    # Get first admin user for created_by
    result = await db.execute(select(User).where(User.role == "admin").limit(1))
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        print("❌ No admin user found, skipping modules seeding")
        return
    
    modules_data = [
        {
            "id": "market_edge_core",
            "name": "Market Edge Core",
            "description": "Core competitive intelligence functionality including market overview, competitor tracking, and basic analytics",
            "version": "1.1.0",
            "module_type": ModuleType.CORE,
            "status": ModuleStatus.ACTIVE,
            "is_core": True,
            "requires_license": False,
            "entry_point": "market_edge.core",
            "config_schema": {
                "type": "object",
                "properties": {
                    "update_frequency": {"type": "string", "enum": ["hourly", "daily", "weekly"]},
                    "data_retention_days": {"type": "integer", "minimum": 30, "maximum": 2555}
                }
            },
            "default_config": {
                "update_frequency": "daily",
                "data_retention_days": 365
            },
            "dependencies": [],
            "min_data_requirements": {
                "competitors": 2,
                "data_points": 100
            },
            "api_endpoints": [
                "/api/v1/market-edge/markets",
                "/api/v1/market-edge/markets/{id}/overview",
                "/api/v1/market-edge/markets/{id}/competitors"
            ],
            "frontend_components": [
                "MarketSelector",
                "CompetitorTable",
                "MarketOverview"
            ],
            "pricing_tier": "free",
            "created_by": admin_user.id
        },
        {
            "id": "pricing_intelligence",
            "name": "Pricing Intelligence",
            "description": "Advanced pricing analysis with trend detection, anomaly identification, and competitive positioning insights",
            "version": "1.0.0",
            "module_type": ModuleType.ANALYTICS,
            "status": ModuleStatus.ACTIVE,
            "is_core": False,
            "requires_license": True,
            "entry_point": "market_edge.pricing_intelligence",
            "config_schema": {
                "type": "object",
                "properties": {
                    "anomaly_threshold": {"type": "number", "minimum": 1.0, "maximum": 5.0},
                    "trend_analysis_days": {"type": "integer", "minimum": 7, "maximum": 365},
                    "price_alerts_enabled": {"type": "boolean"}
                }
            },
            "default_config": {
                "anomaly_threshold": 2.5,
                "trend_analysis_days": 90,
                "price_alerts_enabled": True
            },
            "dependencies": ["market_edge_core"],
            "min_data_requirements": {
                "pricing_data_points": 500,
                "competitors": 3
            },
            "api_endpoints": [
                "/api/v1/market-edge/markets/{id}/analysis",
                "/api/v1/market-edge/markets/{id}/trends",
                "/api/v1/market-edge/markets/{id}/comparison"
            ],
            "frontend_components": [
                "PricingChart",
                "PerformanceMetrics",
                "TrendAnalysis"
            ],
            "pricing_tier": "professional",
            "created_by": admin_user.id
        },
        {
            "id": "alert_system",
            "name": "Alert System",
            "description": "Real-time monitoring and alerting for price changes, market movements, and competitive actions",
            "version": "1.0.0",
            "module_type": ModuleType.ANALYTICS,
            "status": ModuleStatus.ACTIVE,
            "is_core": False,
            "requires_license": False,
            "entry_point": "market_edge.alerts",
            "config_schema": {
                "type": "object",
                "properties": {
                    "notification_channels": {"type": "array", "items": {"type": "string"}},
                    "alert_frequency": {"type": "string", "enum": ["immediate", "hourly", "daily"]},
                    "severity_threshold": {"type": "string", "enum": ["low", "medium", "high"]}
                }
            },
            "default_config": {
                "notification_channels": ["email"],
                "alert_frequency": "immediate",
                "severity_threshold": "medium"
            },
            "dependencies": ["market_edge_core"],
            "min_data_requirements": {
                "active_monitoring": True
            },
            "api_endpoints": [
                "/api/v1/market-edge/markets/{id}/alerts",
                "/api/v1/market-edge/alerts/{id}/mark-read"
            ],
            "frontend_components": [
                "AlertsPanel",
                "NotificationCenter"
            ],
            "pricing_tier": "basic",
            "created_by": admin_user.id
        },
        {
            "id": "data_visualization",
            "name": "Advanced Data Visualization",
            "description": "Enhanced charts, dashboards, and visual analytics for competitive intelligence data",
            "version": "1.0.0",
            "module_type": ModuleType.VISUALIZATION,
            "status": ModuleStatus.TESTING,
            "is_core": False,
            "requires_license": True,
            "entry_point": "market_edge.visualization",
            "config_schema": {
                "type": "object",
                "properties": {
                    "chart_themes": {"type": "array", "items": {"type": "string"}},
                    "interactive_features": {"type": "boolean"},
                    "export_formats": {"type": "array", "items": {"type": "string"}}
                }
            },
            "default_config": {
                "chart_themes": ["professional", "modern"],
                "interactive_features": True,
                "export_formats": ["png", "pdf", "svg"]
            },
            "dependencies": ["market_edge_core"],
            "min_data_requirements": {
                "data_points": 100
            },
            "api_endpoints": [
                "/api/v1/market-edge/visualizations",
                "/api/v1/market-edge/export"
            ],
            "frontend_components": [
                "AdvancedCharts",
                "InteractiveDashboard",
                "ExportTools"
            ],
            "pricing_tier": "premium",
            "created_by": admin_user.id
        }
    ]
    
    for module_data in modules_data:
        # Check if module already exists
        result = await db.execute(select(AnalyticsModule).where(AnalyticsModule.id == module_data["id"]))
        existing = result.scalar_one_or_none()
        
        if not existing:
            module = AnalyticsModule(**module_data)
            db.add(module)
    
    await db.commit()
    print(f"✅ Seeded {len(modules_data)} analytics modules")


async def seed_feature_flags(db: AsyncSession):
    """Seed initial feature flags"""
    
    # Get first admin user for created_by
    result = await db.execute(select(User).where(User.role == "admin").limit(1))
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        print("❌ No admin user found, skipping feature flags seeding")
        return
    
    feature_flags_data = [
        {
            "flag_key": "market_edge_v2",
            "name": "Market Edge V2 Features",
            "description": "Enable new Market Edge features including enhanced analytics and improved UI",
            "is_enabled": True,
            "rollout_percentage": 100,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "ui_improvements": True,
                "enhanced_charts": True,
                "new_metrics": True
            },
            "allowed_sectors": [],
            "blocked_sectors": [],
            "module_id": "market_edge_core",
            "created_by": admin_user.id
        },
        {
            "flag_key": "advanced_pricing_analytics",
            "name": "Advanced Pricing Analytics",
            "description": "Enable ML-powered pricing analytics and forecasting capabilities",
            "is_enabled": False,
            "rollout_percentage": 25,
            "scope": FeatureFlagScope.ORGANISATION,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "ml_forecasting": True,
                "anomaly_detection": True,
                "predictive_alerts": True
            },
            "allowed_sectors": ["59140", "55100"],  # Cinema and Hotels only
            "blocked_sectors": [],
            "module_id": "pricing_intelligence",
            "created_by": admin_user.id
        },
        {
            "flag_key": "sector_specific_insights",
            "name": "Sector-Specific Insights",
            "description": "Enable industry-specific competitive intelligence insights and metrics",
            "is_enabled": True,
            "rollout_percentage": 50,
            "scope": FeatureFlagScope.SECTOR,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "custom_metrics": True,
                "industry_benchmarks": True,
                "sector_reports": True
            },
            "allowed_sectors": ["59140", "55100", "93130", "47520"],
            "blocked_sectors": [],
            "module_id": None,
            "created_by": admin_user.id
        },
        {
            "flag_key": "real_time_monitoring",
            "name": "Real-Time Data Monitoring",
            "description": "Enable real-time data collection and monitoring capabilities",
            "is_enabled": False,
            "rollout_percentage": 10,
            "scope": FeatureFlagScope.ORGANISATION,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "live_data_feeds": True,
                "instant_alerts": True,
                "streaming_updates": True
            },
            "allowed_sectors": [],
            "blocked_sectors": [],
            "module_id": "alert_system",
            "created_by": admin_user.id
        },
        {
            "flag_key": "export_functionality",
            "name": "Data Export Functionality",
            "description": "Enable data export features for reports and analytics",
            "is_enabled": True,
            "rollout_percentage": 100,
            "scope": FeatureFlagScope.GLOBAL,
            "status": FeatureFlagStatus.ACTIVE,
            "config": {
                "csv_export": True,
                "pdf_reports": True,
                "api_export": True
            },
            "allowed_sectors": [],
            "blocked_sectors": [],
            "module_id": None,
            "created_by": admin_user.id
        }
    ]
    
    for flag_data in feature_flags_data:
        # Check if feature flag already exists
        result = await db.execute(select(FeatureFlag).where(FeatureFlag.flag_key == flag_data["flag_key"]))
        existing = result.scalar_one_or_none()
        
        if not existing:
            feature_flag = FeatureFlag(**flag_data)
            db.add(feature_flag)
    
    await db.commit()
    print(f"✅ Seeded {len(feature_flags_data)} feature flags")


async def seed_competitive_factors(db: AsyncSession):
    """Seed competitive factor templates for each SIC code"""
    
    # Get first admin user for created_by
    result = await db.execute(select(User).where(User.role == "admin").limit(1))
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        print("❌ No admin user found, skipping competitive factors seeding")
        return
    
    # Cinema competitive factors
    cinema_factors = [
        {
            "sic_code": "59140",
            "factor_name": "Ticket Pricing",
            "factor_key": "ticket_pricing",
            "description": "Standard adult ticket price for regular screenings",
            "data_type": "numeric",
            "is_required": True,
            "weight": 0.9,
            "validation_rules": {"min": 5.0, "max": 25.0, "currency": "GBP"},
            "display_order": 1,
            "is_visible": True,
            "created_by": admin_user.id
        },
        {
            "sic_code": "59140",
            "factor_name": "Screen Technology",
            "factor_key": "screen_technology",
            "description": "Available screen technologies (IMAX, Dolby, Standard)",
            "data_type": "categorical",
            "is_required": False,
            "weight": 0.8,
            "validation_rules": {"options": ["Standard", "Digital", "IMAX", "Dolby Cinema", "4DX"]},
            "display_order": 2,
            "is_visible": True,
            "created_by": admin_user.id
        },
        {
            "sic_code": "59140",
            "factor_name": "Seating Comfort",
            "factor_key": "seating_comfort",
            "description": "Quality and comfort of seating arrangements",
            "data_type": "categorical",
            "is_required": False,
            "weight": 0.7,
            "validation_rules": {"options": ["Basic", "Standard", "Premium", "Recliner", "Luxury"]},
            "display_order": 3,
            "is_visible": True,
            "created_by": admin_user.id
        },
        {
            "sic_code": "59140",
            "factor_name": "Location Accessibility",
            "factor_key": "location_accessibility",
            "description": "Ease of access including parking and public transport",
            "data_type": "numeric",
            "is_required": True,
            "weight": 0.85,
            "validation_rules": {"min": 1, "max": 10, "description": "1-10 scale"},
            "display_order": 4,
            "is_visible": True,
            "created_by": admin_user.id
        }
    ]
    
    # Hotel competitive factors
    hotel_factors = [
        {
            "sic_code": "55100",
            "factor_name": "Average Daily Rate",
            "factor_key": "average_daily_rate",
            "description": "Average room rate per night",
            "data_type": "numeric",
            "is_required": True,
            "weight": 0.9,
            "validation_rules": {"min": 30.0, "max": 500.0, "currency": "GBP"},
            "display_order": 1,
            "is_visible": True,
            "created_by": admin_user.id
        },
        {
            "sic_code": "55100",
            "factor_name": "Star Rating",
            "factor_key": "star_rating",
            "description": "Official hotel star rating",
            "data_type": "numeric",
            "is_required": True,
            "weight": 0.8,
            "validation_rules": {"min": 1, "max": 5, "type": "integer"},
            "display_order": 2,
            "is_visible": True,
            "created_by": admin_user.id
        },
        {
            "sic_code": "55100",
            "factor_name": "Amenities",
            "factor_key": "amenities",
            "description": "Available hotel amenities and facilities",
            "data_type": "categorical",
            "is_required": False,
            "weight": 0.7,
            "validation_rules": {"options": ["WiFi", "Gym", "Pool", "Spa", "Restaurant", "Bar", "Parking", "Business Center"]},
            "display_order": 3,
            "is_visible": True,
            "created_by": admin_user.id
        }
    ]
    
    all_factors = cinema_factors + hotel_factors
    
    for factor_data in all_factors:
        # Check if competitive factor already exists
        result = await db.execute(
            select(CompetitiveFactorTemplate)
            .where(
                CompetitiveFactorTemplate.sic_code == factor_data["sic_code"],
                CompetitiveFactorTemplate.factor_key == factor_data["factor_key"]
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            factor = CompetitiveFactorTemplate(**factor_data)
            db.add(factor)
    
    await db.commit()
    print(f"✅ Seeded {len(all_factors)} competitive factor templates")


async def main():
    """Main seeding function for Phase 3 data"""
    print("🌱 Seeding Phase 3 enhancement data...")
    
    async for db in get_async_db():
        try:
            await seed_sic_codes(db)
            await seed_analytics_modules(db)
            await seed_feature_flags(db)
            await seed_competitive_factors(db)
            print("✅ Phase 3 data seeding completed successfully!")
        except Exception as e:
            print(f"❌ Error seeding Phase 3 data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())