"""
Organisation Service

Handles business logic for organisation management including industry-specific
validation, feature flag configuration, and tenant boundary management.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.organisation import Organisation, SubscriptionPlan
from ..models.user import User
from ..core.rate_limit_config import Industry
from ..core.industry_config import industry_config_manager
from ..core.logging import logger


class OrganisationValidationError(Exception):
    """Custom exception for organisation validation errors."""
    pass


class OrganisationService:
    """Service for organisation management operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.industry_config = industry_config_manager
    
    def create_organisation(
        self,
        name: str,
        industry_type: Industry,
        subscription_plan: SubscriptionPlan = SubscriptionPlan.basic,
        sic_code: Optional[str] = None,
        admin_user_data: Optional[Dict[str, str]] = None
    ) -> Organisation:
        """
        Create a new organisation with industry-specific configuration.
        
        Args:
            name: Organisation name (must be unique)
            industry_type: Industry type enum
            subscription_plan: Subscription plan
            sic_code: Optional SIC code for more specific industry classification
            admin_user_data: Optional admin user data (email, first_name, last_name)
        
        Returns:
            Created Organisation instance
            
        Raises:
            OrganisationValidationError: If validation fails
        """
        try:
            # Validate industry-specific requirements
            self._validate_industry_requirements(industry_type, sic_code)
            
            # Apply industry-specific defaults
            rate_limits = self.industry_config.get_rate_limit_config(industry_type)
            default_rate_limit = rate_limits.get('api_calls')
            
            # Create organisation
            organisation = Organisation(
                name=name,
                industry_type=industry_type,
                subscription_plan=subscription_plan,
                sic_code=sic_code,
                # Apply industry-specific rate limits
                rate_limit_per_hour=default_rate_limit.limit * 60 if default_rate_limit else 1000,
                burst_limit=default_rate_limit.burst_limit if default_rate_limit else 100,
                rate_limit_enabled=True
            )
            
            self.db.add(organisation)
            self.db.flush()  # Get ID without committing
            
            # Create admin user if provided
            if admin_user_data:
                admin_user = User(
                    email=admin_user_data['email'],
                    first_name=admin_user_data['first_name'],
                    last_name=admin_user_data['last_name'],
                    organisation_id=organisation.id,
                    role='admin'
                )
                self.db.add(admin_user)
            
            self.db.commit()
            self.db.refresh(organisation)
            
            logger.info(f"Created organisation '{name}' with industry type '{industry_type.value}'")
            return organisation
            
        except IntegrityError as e:
            self.db.rollback()
            if 'unique constraint' in str(e).lower():
                raise OrganisationValidationError(f"Organisation name '{name}' already exists")
            raise OrganisationValidationError(f"Database error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating organisation: {str(e)}")
            raise OrganisationValidationError(f"Failed to create organisation: {str(e)}")
    
    def update_organisation(
        self,
        organisation_id: str,
        name: Optional[str] = None,
        industry_type: Optional[Industry] = None,
        subscription_plan: Optional[SubscriptionPlan] = None,
        sic_code: Optional[str] = None
    ) -> Organisation:
        """
        Update an existing organisation with validation.
        
        Args:
            organisation_id: Organisation ID
            name: New name (optional)
            industry_type: New industry type (optional)
            subscription_plan: New subscription plan (optional)
            sic_code: New SIC code (optional)
            
        Returns:
            Updated Organisation instance
            
        Raises:
            OrganisationValidationError: If validation fails or organisation not found
        """
        try:
            organisation = self.db.query(Organisation).filter(
                Organisation.id == organisation_id
            ).first()
            
            if not organisation:
                raise OrganisationValidationError(f"Organisation with ID '{organisation_id}' not found")
            
            # Store original values for rollback if needed
            original_industry = organisation.industry_type
            
            # Apply updates
            if name is not None:
                organisation.name = name
            
            if industry_type is not None:
                # Validate new industry type
                self._validate_industry_requirements(industry_type, sic_code or organisation.sic_code)
                
                # Update industry-specific configuration if industry changed
                if industry_type != original_industry:
                    rate_limits = self.industry_config.get_rate_limit_config(industry_type)
                    default_rate_limit = rate_limits.get('api_calls')
                    
                    organisation.industry_type = industry_type
                    organisation.rate_limit_per_hour = default_rate_limit.limit * 60 if default_rate_limit else 1000
                    organisation.burst_limit = default_rate_limit.burst_limit if default_rate_limit else 100
            
            if subscription_plan is not None:
                organisation.subscription_plan = subscription_plan
            
            if sic_code is not None:
                organisation.sic_code = sic_code
            
            self.db.commit()
            self.db.refresh(organisation)
            
            logger.info(f"Updated organisation '{organisation.name}' (ID: {organisation_id})")
            return organisation
            
        except IntegrityError as e:
            self.db.rollback()
            if 'unique constraint' in str(e).lower():
                raise OrganisationValidationError(f"Organisation name '{name}' already exists")
            raise OrganisationValidationError(f"Database error: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating organisation {organisation_id}: {str(e)}")
            raise OrganisationValidationError(f"Failed to update organisation: {str(e)}")
    
    def get_organisation(self, organisation_id: str) -> Optional[Organisation]:
        """Get organisation by ID with tenant boundary validation."""
        try:
            # Validate UUID format to prevent injection
            import uuid
            uuid.UUID(organisation_id)
        except ValueError:
            raise OrganisationValidationError(f"Invalid organisation ID format: {organisation_id}")
        
        return self.db.query(Organisation).filter(
            Organisation.id == organisation_id
        ).first()
    
    def get_organisation_by_name(self, name: str) -> Optional[Organisation]:
        """Get organisation by name with input validation."""
        # Validate name input to prevent injection
        if not name or len(name.strip()) == 0:
            raise OrganisationValidationError("Organisation name cannot be empty")
        if len(name) > 255:
            raise OrganisationValidationError("Organisation name exceeds maximum length of 255 characters")
        
        return self.db.query(Organisation).filter(
            Organisation.name == name.strip()
        ).first()
    
    def delete_organisation(self, organisation_id: str, force: bool = False) -> bool:
        """
        Delete an organisation with proper cleanup.
        
        Args:
            organisation_id: Organisation ID
            force: If True, force deletion even with active users
            
        Returns:
            True if deleted successfully
            
        Raises:
            OrganisationValidationError: If validation fails or organisation has dependencies
        """
        try:
            organisation = self.get_organisation(organisation_id)
            if not organisation:
                raise OrganisationValidationError(f"Organisation with ID '{organisation_id}' not found")
            
            # Check for active users
            active_users = self.db.query(User).filter(
                User.organisation_id == organisation_id,
                User.is_active == True
            ).count()
            
            if active_users > 0 and not force:
                raise OrganisationValidationError(
                    f"Cannot delete organisation with {active_users} active users. Use force=True to override."
                )
            
            # Soft delete by marking as inactive first
            organisation.is_active = False
            
            if force:
                # Hard delete: Remove all related data
                self.db.query(User).filter(User.organisation_id == organisation_id).delete()
                self.db.delete(organisation)
                logger.warning(f"Force deleted organisation '{organisation.name}' and all related data")
            else:
                logger.info(f"Soft deleted organisation '{organisation.name}'")
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting organisation {organisation_id}: {str(e)}")
            raise OrganisationValidationError(f"Failed to delete organisation: {str(e)}")
    
    def get_industry_specific_config(self, organisation_id: str, requesting_user_org_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get industry-specific configuration for an organisation with tenant boundary validation.
        
        Args:
            organisation_id: Organisation ID to get config for
            requesting_user_org_id: Organisation ID of the requesting user (for tenant boundary validation)
        
        Returns:
            Dictionary containing industry-specific settings
        """
        organisation = self.get_organisation(organisation_id)
        if not organisation:
            raise OrganisationValidationError(f"Organisation with ID '{organisation_id}' not found")
        
        # Tenant boundary validation: Users can only access their own organization's config
        if requesting_user_org_id and str(organisation.id) != str(requesting_user_org_id):
            raise OrganisationValidationError("Access denied: Cannot access configuration for different organisation")
        
        industry_type = organisation.industry_type
        
        # Serialize rate limits for JSON compatibility
        rate_limits_config = self.industry_config.get_rate_limit_config(industry_type)
        serialized_rate_limits = {}
        for key, rule in rate_limits_config.items():
            serialized_rate_limits[key] = {
                'limit_type': rule.limit_type.value,
                'limit': rule.limit,
                'window_seconds': int(rule.window.total_seconds()),
                'burst_limit': getattr(rule, 'burst_limit', None),
                'recovery_rate': getattr(rule, 'recovery_rate', None)
            }
        
        # Get profile and serialize it
        profile = self.industry_config.industry_mapper.get_industry_profile(industry_type)
        serialized_profile = {
            'industry': profile.industry.value,
            'display_name': profile.display_name,
            'description': profile.description,
            'sic_codes': profile.sic_codes,
            'typical_usage_patterns': profile.typical_usage_patterns,
            'security_requirements': profile.security_requirements,
            'performance_requirements': profile.performance_requirements,
            'compliance_requirements': profile.compliance_requirements
        }
        
        return {
            'industry_type': industry_type.value,
            'rate_limits': serialized_rate_limits,
            'security_config': self.industry_config.get_security_config(industry_type),
            'performance_config': self.industry_config.get_performance_config(industry_type),
            'compliance_requirements': self.industry_config.get_compliance_requirements(industry_type),
            'feature_flags': self.industry_config.get_feature_flags_config(industry_type),
            'profile': serialized_profile
        }
    
    def _validate_industry_requirements(self, industry_type: Industry, sic_code: Optional[str] = None):
        """
        Validate industry-specific requirements.
        
        Args:
            industry_type: Industry type to validate
            sic_code: Optional SIC code for additional validation
            
        Raises:
            OrganisationValidationError: If validation fails
        """
        try:
            # Get industry profile
            profile = self.industry_config.industry_mapper.get_industry_profile(industry_type)
            
            # Validate SIC code if provided - STRICT ENFORCEMENT
            if sic_code and profile.sic_codes:
                if sic_code not in profile.sic_codes:
                    raise OrganisationValidationError(
                        f"SIC code '{sic_code}' is not valid for industry '{industry_type.value}'. "
                        f"Valid codes: {', '.join(profile.sic_codes)}"
                    )
            
            # Validate industry type is supported - STRICT ENFORCEMENT
            valid_industries = [Industry.CINEMA, Industry.HOTEL, Industry.GYM, Industry.B2B, Industry.RETAIL, Industry.DEFAULT]
            if industry_type not in valid_industries:
                raise OrganisationValidationError(
                    f"Unsupported industry type: {industry_type}. "
                    f"Valid types: {', '.join([i.value for i in valid_industries])}"
                )
            
            # Additional validation: Ensure enum value is not None or invalid
            if not isinstance(industry_type, Industry):
                raise OrganisationValidationError(
                    f"Industry type must be a valid Industry enum, got: {type(industry_type)}"
                )
                
        except Exception as e:
            logger.error(f"Industry validation error: {str(e)}")
            raise OrganisationValidationError(f"Industry validation failed: {str(e)}")
    
    def get_all_organisations(self) -> List[Organisation]:
        """Get all organisations (Super Admin only)."""
        return self.db.query(Organisation).order_by(Organisation.created_at.desc()).all()

    def get_organisations_by_industry(self, industry_type: Industry) -> List[Organisation]:
        """Get all organisations of a specific industry type."""
        return self.db.query(Organisation).filter(
            Organisation.industry_type == industry_type,
            Organisation.is_active == True
        ).all()
    
    def get_organisation_stats(self) -> Dict[str, Any]:
        """Get organisation statistics by industry."""
        stats = {}
        
        for industry in Industry:
            count = self.db.query(Organisation).filter(
                Organisation.industry_type == industry,
                Organisation.is_active == True
            ).count()
            stats[industry.value] = count
        
        total = self.db.query(Organisation).filter(Organisation.is_active == True).count()
        stats['total'] = total
        
        return stats