import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.organisation import Organisation, SubscriptionPlan
from app.models.user import User, UserRole
from app.models.tool import Tool
from app.models.organisation_tool_access import OrganisationToolAccess


def seed_database():
    db: Session = SessionLocal()
    
    try:
        # Create sample organisations
        org1 = Organisation(
            name="TechCorp Inc",
            industry="Technology",
            subscription_plan=SubscriptionPlan.ENTERPRISE,
            is_active=True
        )
        
        org2 = Organisation(
            name="Marketing Solutions Ltd",
            industry="Marketing",
            subscription_plan=SubscriptionPlan.PROFESSIONAL,
            is_active=True
        )
        
        org3 = Organisation(
            name="Default",
            industry="General",
            subscription_plan=SubscriptionPlan.BASIC,
            is_active=True
        )
        
        db.add_all([org1, org2, org3])
        db.commit()
        
        # Create sample users
        user1 = User(
            email="admin@techcorp.com",
            first_name="John",
            last_name="Admin",
            organisation_id=org1.id,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        user2 = User(
            email="analyst@techcorp.com",
            first_name="Jane",
            last_name="Analyst",
            organisation_id=org1.id,
            role=UserRole.ANALYST,
            is_active=True
        )
        
        user3 = User(
            email="manager@marketing.com",
            first_name="Bob",
            last_name="Manager",
            organisation_id=org2.id,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add_all([user1, user2, user3])
        db.commit()
        
        # Create sample tools
        market_edge = Tool(
            name="Market Edge",
            description="Competitive intelligence and market analysis tool",
            version="1.0.0",
            is_active=True,
            config_schema={
                "features": ["competitor_tracking", "market_reports", "price_monitoring"],
                "limits": {
                    "basic": {"reports_per_month": 10, "competitors": 5},
                    "professional": {"reports_per_month": 50, "competitors": 20},
                    "enterprise": {"reports_per_month": -1, "competitors": -1}
                }
            },
            pricing_config={
                "basic": {"monthly": 99, "yearly": 990},
                "professional": {"monthly": 299, "yearly": 2990},
                "enterprise": {"monthly": 999, "yearly": 9990}
            }
        )
        
        sales_intelligence = Tool(
            name="Sales Intelligence",
            description="Sales lead generation and CRM analytics",
            version="1.2.0",
            is_active=True,
            config_schema={
                "features": ["lead_scoring", "pipeline_analytics", "email_automation"],
                "limits": {
                    "basic": {"leads_per_month": 100, "email_sends": 1000},
                    "professional": {"leads_per_month": 500, "email_sends": 5000},
                    "enterprise": {"leads_per_month": -1, "email_sends": -1}
                }
            },
            pricing_config={
                "basic": {"monthly": 149, "yearly": 1490},
                "professional": {"monthly": 399, "yearly": 3990},
                "enterprise": {"monthly": 1299, "yearly": 12990}
            }
        )
        
        content_optimizer = Tool(
            name="Content Optimizer",
            description="AI-powered content creation and optimization",
            version="2.1.0",
            is_active=True,
            config_schema={
                "features": ["seo_optimization", "content_generation", "performance_tracking"],
                "limits": {
                    "basic": {"content_pieces": 20, "optimizations": 50},
                    "professional": {"content_pieces": 100, "optimizations": 200},
                    "enterprise": {"content_pieces": -1, "optimizations": -1}
                }
            },
            pricing_config={
                "basic": {"monthly": 79, "yearly": 790},
                "professional": {"monthly": 199, "yearly": 1990},
                "enterprise": {"monthly": 599, "yearly": 5990}
            }
        )
        
        db.add_all([market_edge, sales_intelligence, content_optimizer])
        db.commit()
        
        # Create organisation tool access
        # TechCorp (Enterprise) gets access to all tools
        techcorp_market_edge = OrganisationToolAccess(
            organisation_id=org1.id,
            tool_id=market_edge.id,
            subscription_tier="enterprise",
            features_enabled=["competitor_tracking", "market_reports", "price_monitoring"],
            usage_limits={"reports_per_month": -1, "competitors": -1}
        )
        
        techcorp_sales = OrganisationToolAccess(
            organisation_id=org1.id,
            tool_id=sales_intelligence.id,
            subscription_tier="professional",
            features_enabled=["lead_scoring", "pipeline_analytics"],
            usage_limits={"leads_per_month": 500, "email_sends": 5000}
        )
        
        # Marketing Solutions (Professional) gets access to content and market tools
        marketing_market_edge = OrganisationToolAccess(
            organisation_id=org2.id,
            tool_id=market_edge.id,
            subscription_tier="professional",
            features_enabled=["competitor_tracking", "market_reports"],
            usage_limits={"reports_per_month": 50, "competitors": 20}
        )
        
        marketing_content = OrganisationToolAccess(
            organisation_id=org2.id,
            tool_id=content_optimizer.id,
            subscription_tier="professional",
            features_enabled=["seo_optimization", "content_generation", "performance_tracking"],
            usage_limits={"content_pieces": 100, "optimizations": 200}
        )
        
        db.add_all([techcorp_market_edge, techcorp_sales, marketing_market_edge, marketing_content])
        db.commit()
        
        print("✅ Database seeded successfully!")
        print(f"Created {len([org1, org2, org3])} organisations")
        print(f"Created {len([user1, user2, user3])} users")
        print(f"Created {len([market_edge, sales_intelligence, content_optimizer])} tools")
        print(f"Created {len([techcorp_market_edge, techcorp_sales, marketing_market_edge, marketing_content])} tool access records")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()