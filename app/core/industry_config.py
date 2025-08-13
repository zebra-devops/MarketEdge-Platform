"""
Industry-Specific Configuration Module

Provides industry-specific configurations for rate limiting, feature flags,
and other business logic customizations based on SIC codes and industry types.
"""
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import json

from .logging import logger
from .rate_limit_config import Industry, RateLimitRule, RateLimitType
from datetime import timedelta


@dataclass
class IndustryProfile:
    """Profile defining industry-specific characteristics and configurations."""
    industry: Industry
    display_name: str
    description: str
    sic_codes: List[str]  # Standard Industrial Classification codes
    typical_usage_patterns: Dict[str, Any]
    security_requirements: Dict[str, Any]
    performance_requirements: Dict[str, Any]
    compliance_requirements: List[str]


class IndustryMapper:
    """
    Maps SIC codes and business characteristics to industry types.
    
    This enables automatic industry detection and configuration
    based on organization setup.
    """
    
    def __init__(self):
        self.sic_to_industry_map = self._initialize_sic_mappings()
        self.industry_profiles = self._initialize_industry_profiles()
    
    def _initialize_sic_mappings(self) -> Dict[str, Industry]:
        """Initialize SIC code to industry mappings."""
        return {
            # Cinema / Entertainment
            "59140": Industry.CINEMA,  # Cinema exhibition and operation
            "7832": Industry.CINEMA,  # Motion picture theaters, except drive-in
            "7833": Industry.CINEMA,  # Drive-in motion picture theaters
            "7841": Industry.CINEMA,  # Video tape rental
            "5735": Industry.CINEMA,  # Record and prerecorded tape stores
            
            # Hotels / Hospitality
            "7011": Industry.HOTEL,   # Hotels and motels
            "7021": Industry.HOTEL,   # Rooming and boarding houses
            "7041": Industry.HOTEL,   # Organization hotels and lodging houses
            "7213": Industry.HOTEL,   # Linen supply
            "7231": Industry.HOTEL,   # Beauty shops
            "7991": Industry.HOTEL,   # Physical fitness facilities
            
            # Gym / Fitness
            "7991": Industry.GYM,     # Physical fitness facilities
            "7997": Industry.GYM,     # Membership sports and recreation clubs
            "7999": Industry.GYM,     # Amusement and recreation services
            "5941": Industry.GYM,     # Sporting goods stores and bicycle shops
            
            # B2B Services
            "7389": Industry.B2B,     # Business services
            "7372": Industry.B2B,     # Prepackaged software
            "7373": Industry.B2B,     # Computer integrated systems design
            "7374": Industry.B2B,     # Computer processing and data preparation
            "8742": Industry.B2B,     # Management consulting services
            "8748": Industry.B2B,     # Business consulting services
            
            # Retail
            "5399": Industry.RETAIL,  # Miscellaneous general merchandise stores
            "5411": Industry.RETAIL,  # Grocery stores
            "5531": Industry.RETAIL,  # Auto and home supply stores
            "5661": Industry.RETAIL,  # Shoe stores
            "5699": Industry.RETAIL,  # Miscellaneous apparel stores
            "5712": Industry.RETAIL,  # Furniture stores
            "5734": Industry.RETAIL,  # Computer and software stores
            "5944": Industry.RETAIL,  # Jewelry stores
            "5945": Industry.RETAIL,  # Hobby, toy, and game shops
        }
    
    def _initialize_industry_profiles(self) -> Dict[Industry, IndustryProfile]:
        """Initialize detailed industry profiles."""
        return {
            Industry.CINEMA: IndustryProfile(
                industry=Industry.CINEMA,
                display_name="Cinema & Entertainment",
                description="Movie theaters, entertainment venues, and related services",
                sic_codes=["59140", "7832", "7833", "7841", "5735"],
                typical_usage_patterns={
                    "peak_hours": ["18:00-23:00", "12:00-14:00"],
                    "seasonal_peaks": ["summer", "holiday_season"],
                    "burst_events": ["movie_premieres", "special_screenings"],
                    "avg_session_duration": "2-3 hours",
                    "typical_capacity": "100-500 seats"
                },
                security_requirements={
                    "pci_compliance": True,
                    "data_retention_days": 90,
                    "audit_logging": True,
                    "fraud_detection": True
                },
                performance_requirements={
                    "response_time_ms": 500,
                    "uptime_sla": 0.995,
                    "concurrent_bookings": 200,
                    "peak_multiplier": 5.0
                },
                compliance_requirements=[
                    "PCI_DSS", "GDPR", "CCPA", "accessibility_compliance"
                ]
            ),
            
            Industry.HOTEL: IndustryProfile(
                industry=Industry.HOTEL,
                display_name="Hospitality & Hotels",
                description="Hotels, motels, and hospitality services",
                sic_codes=["7011", "7021", "7041", "7213", "7231"],
                typical_usage_patterns={
                    "peak_hours": ["09:00-11:00", "15:00-17:00", "20:00-22:00"],
                    "seasonal_peaks": ["summer", "business_travel_seasons"],
                    "burst_events": ["conferences", "events", "holidays"],
                    "avg_session_duration": "5-10 minutes",
                    "typical_capacity": "50-1000 rooms"
                },
                security_requirements={
                    "pci_compliance": True,
                    "data_retention_days": 365,  # Longer for hospitality
                    "audit_logging": True,
                    "guest_privacy": True
                },
                performance_requirements={
                    "response_time_ms": 300,
                    "uptime_sla": 0.999,  # Higher SLA for hospitality
                    "concurrent_bookings": 100,
                    "peak_multiplier": 3.0
                },
                compliance_requirements=[
                    "PCI_DSS", "GDPR", "CCPA", "hospitality_regulations"
                ]
            ),
            
            Industry.GYM: IndustryProfile(
                industry=Industry.GYM,
                display_name="Fitness & Recreation",
                description="Gyms, fitness centers, and recreational facilities",
                sic_codes=["7991", "7997", "7999", "5941"],
                typical_usage_patterns={
                    "peak_hours": ["06:00-09:00", "17:00-20:00"],
                    "seasonal_peaks": ["january", "summer_prep"],
                    "burst_events": ["new_year", "membership_drives"],
                    "avg_session_duration": "30-90 minutes",
                    "typical_capacity": "50-500 members"
                },
                security_requirements={
                    "pci_compliance": True,
                    "data_retention_days": 180,
                    "audit_logging": False,
                    "health_data_protection": True
                },
                performance_requirements={
                    "response_time_ms": 200,  # Quick check-ins
                    "uptime_sla": 0.99,
                    "concurrent_checkins": 50,
                    "peak_multiplier": 4.0
                },
                compliance_requirements=[
                    "PCI_DSS", "HIPAA", "GDPR", "health_regulations"
                ]
            ),
            
            Industry.B2B: IndustryProfile(
                industry=Industry.B2B,
                display_name="Business Services",
                description="B2B services, consulting, and professional services",
                sic_codes=["7389", "7372", "7373", "7374", "8742", "8748"],
                typical_usage_patterns={
                    "peak_hours": ["09:00-17:00"],
                    "seasonal_peaks": ["quarter_ends", "fiscal_year_end"],
                    "burst_events": ["reporting_periods", "integration_updates"],
                    "avg_session_duration": "15-45 minutes",
                    "typical_capacity": "10-1000 users"
                },
                security_requirements={
                    "pci_compliance": False,
                    "data_retention_days": 2555,  # 7 years for business records
                    "audit_logging": True,
                    "enterprise_security": True
                },
                performance_requirements={
                    "response_time_ms": 100,  # Professional SLA
                    "uptime_sla": 0.999,
                    "concurrent_users": 500,
                    "peak_multiplier": 2.0
                },
                compliance_requirements=[
                    "SOX", "GDPR", "CCPA", "industry_specific"
                ]
            ),
            
            Industry.RETAIL: IndustryProfile(
                industry=Industry.RETAIL,
                display_name="Retail & E-commerce",
                description="Retail stores, e-commerce, and consumer services",
                sic_codes=["5399", "5411", "5531", "5661", "5699", "5712", "5734", "5944", "5945"],
                typical_usage_patterns={
                    "peak_hours": ["10:00-14:00", "18:00-21:00"],
                    "seasonal_peaks": ["black_friday", "holiday_season", "back_to_school"],
                    "burst_events": ["sales", "product_launches", "flash_deals"],
                    "avg_session_duration": "5-20 minutes",
                    "typical_capacity": "100-10000 customers"
                },
                security_requirements={
                    "pci_compliance": True,
                    "data_retention_days": 90,
                    "audit_logging": True,
                    "fraud_detection": True
                },
                performance_requirements={
                    "response_time_ms": 200,
                    "uptime_sla": 0.995,
                    "concurrent_transactions": 1000,
                    "peak_multiplier": 10.0  # Highest peak multiplier
                },
                compliance_requirements=[
                    "PCI_DSS", "GDPR", "CCPA", "consumer_protection"
                ]
            ),
            
            Industry.DEFAULT: IndustryProfile(
                industry=Industry.DEFAULT,
                display_name="General Business",
                description="General business operations and services",
                sic_codes=[],
                typical_usage_patterns={
                    "peak_hours": ["09:00-17:00"],
                    "seasonal_peaks": [],
                    "burst_events": [],
                    "avg_session_duration": "10-30 minutes",
                    "typical_capacity": "10-100 users"
                },
                security_requirements={
                    "pci_compliance": False,
                    "data_retention_days": 90,
                    "audit_logging": False,
                    "basic_security": True
                },
                performance_requirements={
                    "response_time_ms": 1000,
                    "uptime_sla": 0.99,
                    "concurrent_users": 50,
                    "peak_multiplier": 2.0
                },
                compliance_requirements=["GDPR", "basic_compliance"]
            )
        }
    
    def get_industry_from_sic(self, sic_code: str) -> Industry:
        """Map SIC code to industry type."""
        return self.sic_to_industry_map.get(sic_code, Industry.DEFAULT)
    
    def get_industry_profile(self, industry: Industry) -> IndustryProfile:
        """Get detailed profile for an industry."""
        return self.industry_profiles.get(industry, self.industry_profiles[Industry.DEFAULT])
    
    def detect_industry_from_organization(self, org_data: Dict[str, Any]) -> Industry:
        """
        Detect industry from organization data.
        
        Uses multiple signals to determine the most appropriate industry classification.
        """
        try:
            # Primary: SIC code
            sic_code = org_data.get("sic_code")
            if sic_code:
                industry = self.get_industry_from_sic(sic_code)
                if industry != Industry.DEFAULT:
                    return industry
            
            # Secondary: Business name keywords
            business_name = org_data.get("name", "").lower()
            business_keywords = {
                Industry.CINEMA: ["cinema", "theater", "theatre", "movie", "film", "entertainment"],
                Industry.HOTEL: ["hotel", "motel", "inn", "lodge", "resort", "hospitality"],
                Industry.GYM: ["gym", "fitness", "health", "recreation", "sports", "wellness"],
                Industry.B2B: ["consulting", "services", "software", "technology", "solutions"],
                Industry.RETAIL: ["store", "shop", "retail", "market", "boutique", "outlet"]
            }
            
            for industry, keywords in business_keywords.items():
                if any(keyword in business_name for keyword in keywords):
                    return industry
            
            # Tertiary: Business description
            description = org_data.get("description", "").lower()
            for industry, keywords in business_keywords.items():
                if any(keyword in description for keyword in keywords):
                    return industry
            
            # Default fallback
            return Industry.DEFAULT
            
        except Exception as e:
            logger.warning(f"Error detecting industry from organization data: {e}")
            return Industry.DEFAULT


class IndustryConfigManager:
    """
    Manages industry-specific configurations and provides configuration
    values based on detected or assigned industry types.
    """
    
    def __init__(self):
        self.industry_mapper = IndustryMapper()
        self._config_cache = {}
    
    def get_rate_limit_config(self, industry: Industry) -> Dict[str, RateLimitRule]:
        """Get industry-specific rate limiting configuration."""
        profile = self.industry_mapper.get_industry_profile(industry)
        
        # Convert profile requirements to rate limit rules
        perf_req = profile.performance_requirements
        
        base_rpm = 100  # Base requests per minute
        if industry == Industry.CINEMA:
            base_rpm = 300
        elif industry == Industry.HOTEL:
            base_rpm = 200
        elif industry == Industry.GYM:
            base_rpm = 150
        elif industry == Industry.B2B:
            base_rpm = 500
        elif industry == Industry.RETAIL:
            base_rpm = 400
        
        return {
            "api_calls": RateLimitRule(
                limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                limit=base_rpm,
                window=timedelta(minutes=1),
                burst_limit=int(base_rpm * profile.performance_requirements.get("peak_multiplier", 2.0)),
                recovery_rate=base_rpm / 60.0
            ),
            "concurrent": RateLimitRule(
                limit_type=RateLimitType.CONCURRENT_REQUESTS,
                limit=perf_req.get("concurrent_users", 50),
                window=timedelta(seconds=1)
            )
        }
    
    def get_security_config(self, industry: Industry) -> Dict[str, Any]:
        """Get industry-specific security configuration."""
        profile = self.industry_mapper.get_industry_profile(industry)
        return profile.security_requirements
    
    def get_performance_config(self, industry: Industry) -> Dict[str, Any]:
        """Get industry-specific performance configuration."""
        profile = self.industry_mapper.get_industry_profile(industry)
        return profile.performance_requirements
    
    def get_compliance_requirements(self, industry: Industry) -> List[str]:
        """Get industry-specific compliance requirements."""
        profile = self.industry_mapper.get_industry_profile(industry)
        return profile.compliance_requirements
    
    def get_feature_flags_config(self, industry: Industry) -> Dict[str, Any]:
        """Get industry-specific feature flag configuration."""
        profile = self.industry_mapper.get_industry_profile(industry)
        
        # Define feature availability by industry
        feature_config = {
            "advanced_analytics": industry in [Industry.B2B, Industry.HOTEL],
            "real_time_notifications": industry != Industry.DEFAULT,
            "mobile_app_support": True,  # All industries
            "api_access": industry in [Industry.B2B, Industry.RETAIL, Industry.HOTEL],
            "custom_branding": industry != Industry.DEFAULT,
            "multi_location_support": industry in [Industry.RETAIL, Industry.GYM, Industry.HOTEL],
            "integration_marketplace": industry == Industry.B2B,
            "advanced_reporting": industry in [Industry.B2B, Industry.RETAIL],
        }
        
        return feature_config
    
    def get_tier_recommendations(self, industry: Industry, user_count: int) -> str:
        """Recommend subscription tier based on industry and usage."""
        profile = self.industry_mapper.get_industry_profile(industry)
        
        if industry == Industry.B2B and user_count > 50:
            return "enterprise"
        elif industry in [Industry.RETAIL, Industry.HOTEL] and user_count > 20:
            return "premium"
        elif user_count > 100:
            return "enterprise"
        elif user_count > 10:
            return "premium"
        else:
            return "standard"
    
    def validate_industry_config(self, industry: Industry, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that a configuration is appropriate for the industry."""
        errors = []
        profile = self.industry_mapper.get_industry_profile(industry)
        
        # Validate security requirements
        security_req = profile.security_requirements
        if security_req.get("pci_compliance") and not config.get("pci_enabled"):
            errors.append("PCI compliance is required for this industry")
        
        # Validate performance requirements
        perf_req = profile.performance_requirements
        if config.get("response_time_sla") and config["response_time_sla"] > perf_req["response_time_ms"]:
            errors.append(f"Response time SLA exceeds industry requirement ({perf_req['response_time_ms']}ms)")
        
        # Validate compliance requirements
        required_compliance = set(profile.compliance_requirements)
        enabled_compliance = set(config.get("compliance", []))
        missing_compliance = required_compliance - enabled_compliance
        
        if missing_compliance:
            errors.append(f"Missing required compliance: {', '.join(missing_compliance)}")
        
        return len(errors) == 0, errors


# Global industry configuration manager
industry_config_manager = IndustryConfigManager()


def get_industry_from_sic_code(sic_code: str) -> Industry:
    """Convenience function to get industry from SIC code."""
    return industry_config_manager.industry_mapper.get_industry_from_sic(sic_code)


def detect_organization_industry(org_data: Dict[str, Any]) -> Industry:
    """Convenience function to detect industry from organization data."""
    return industry_config_manager.industry_mapper.detect_industry_from_organization(org_data)


def get_industry_rate_limits(industry: Industry) -> Dict[str, RateLimitRule]:
    """Convenience function to get rate limits for an industry."""
    return industry_config_manager.get_rate_limit_config(industry)