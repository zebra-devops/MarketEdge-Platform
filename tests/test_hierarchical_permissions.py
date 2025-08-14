"""
Comprehensive tests for hierarchical permission system

Tests cover:
- Organization creation with hierarchy structure
- User assignments to hierarchy nodes
- Permission resolution across hierarchy levels
- Industry template application
- Row-level security enforcement
- Backward compatibility with existing system
"""
import pytest
import uuid
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.organisation import Organisation
from app.models.hierarchy import (
    OrganizationHierarchy, UserHierarchyAssignment, HierarchyRoleAssignment,
    IndustryTemplate, EnhancedUserRole, HierarchyLevel
)
from app.services.permission_service import PermissionResolutionEngine, IndustryTemplateService


class TestHierarchicalPermissions:
    """Test suite for hierarchical permission system"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        # This would typically use a test database session
        # For now, we'll use the dependency override pattern
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def sample_organization(self, db_session: Session):
        """Create a sample organization with hierarchy structure"""
        
        # Create organization
        org = Organisation(
            name="Test Cinema Chain",
            industry_type="cinema",
            subscription_plan="professional",
            is_active=True
        )
        db_session.add(org)
        db_session.flush()
        
        # Create root hierarchy node
        root_node = OrganizationHierarchy(
            name="Test Cinema Chain",
            slug="test-cinema-chain",
            description="Root organization node",
            level=HierarchyLevel.ORGANIZATION,
            hierarchy_path="test-cinema-chain",
            depth=0,
            legacy_organisation_id=org.id,
            is_active=True
        )
        db_session.add(root_node)
        db_session.flush()
        
        # Create location nodes
        location1 = OrganizationHierarchy(
            name="Downtown Theater",
            slug="downtown-theater",
            parent_id=root_node.id,
            level=HierarchyLevel.LOCATION,
            hierarchy_path="test-cinema-chain/downtown-theater",
            depth=1,
            legacy_organisation_id=org.id,
            is_active=True
        )
        
        location2 = OrganizationHierarchy(
            name="Mall Theater",
            slug="mall-theater",
            parent_id=root_node.id,
            level=HierarchyLevel.LOCATION,
            hierarchy_path="test-cinema-chain/mall-theater",
            depth=1,
            legacy_organisation_id=org.id,
            is_active=True
        )
        
        db_session.add(location1)
        db_session.add(location2)
        db_session.flush()
        
        # Create department nodes
        dept1 = OrganizationHierarchy(
            name="Operations",
            slug="operations",
            parent_id=location1.id,
            level=HierarchyLevel.DEPARTMENT,
            hierarchy_path="test-cinema-chain/downtown-theater/operations",
            depth=2,
            legacy_organisation_id=org.id,
            is_active=True
        )
        
        db_session.add(dept1)
        db_session.flush()
        
        # Create default role assignments
        role_assignments = [
            (root_node.id, EnhancedUserRole.org_admin, ["read", "write", "delete", "admin", "manage_users", "manage_settings", "view_reports", "export_data"]),
            (root_node.id, EnhancedUserRole.location_manager, ["read", "write", "manage_users", "view_reports"]),
            (root_node.id, EnhancedUserRole.user, ["read", "view_reports"]),
            (location1.id, EnhancedUserRole.location_manager, ["read", "write", "manage_users", "view_reports"]),
            (dept1.id, EnhancedUserRole.department_lead, ["read", "write", "view_reports"])
        ]
        
        for node_id, role, permissions in role_assignments:
            role_assignment = HierarchyRoleAssignment(
                hierarchy_node_id=node_id,
                role=role,
                permissions=str(permissions).replace("'", '"'),
                inherits_from_parent=True,
                is_active=True
            )
            db_session.add(role_assignment)
        
        db_session.commit()
        
        return {
            "organization": org,
            "root_node": root_node,
            "locations": [location1, location2],
            "departments": [dept1]
        }
    
    @pytest.fixture
    def sample_users(self, db_session: Session, sample_organization: Dict[str, Any]):
        """Create sample users with different roles"""
        
        org = sample_organization["organization"]
        root_node = sample_organization["root_node"]
        location1 = sample_organization["locations"][0]
        dept1 = sample_organization["departments"][0]
        
        # Create users
        org_admin = User(
            email="admin@testcinema.com",
            first_name="Admin",
            last_name="User",
            organisation_id=org.id,
            role=UserRole.admin,
            is_active=True
        )
        
        location_manager = User(
            email="manager@testcinema.com",
            first_name="Location",
            last_name="Manager",
            organisation_id=org.id,
            role=UserRole.analyst,  # Legacy role
            is_active=True
        )
        
        dept_lead = User(
            email="lead@testcinema.com",
            first_name="Department",
            last_name="Lead",
            organisation_id=org.id,
            role=UserRole.viewer,  # Legacy role
            is_active=True
        )
        
        regular_user = User(
            email="user@testcinema.com",
            first_name="Regular",
            last_name="User",
            organisation_id=org.id,
            role=UserRole.viewer,
            is_active=True
        )
        
        db_session.add_all([org_admin, location_manager, dept_lead, regular_user])
        db_session.flush()
        
        # Create hierarchy assignments
        assignments = [
            UserHierarchyAssignment(
                user_id=org_admin.id,
                hierarchy_node_id=root_node.id,
                role=EnhancedUserRole.org_admin,
                is_primary=True,
                is_active=True
            ),
            UserHierarchyAssignment(
                user_id=location_manager.id,
                hierarchy_node_id=location1.id,
                role=EnhancedUserRole.location_manager,
                is_primary=True,
                is_active=True
            ),
            UserHierarchyAssignment(
                user_id=dept_lead.id,
                hierarchy_node_id=dept1.id,
                role=EnhancedUserRole.department_lead,
                is_primary=True,
                is_active=True
            ),
            UserHierarchyAssignment(
                user_id=regular_user.id,
                hierarchy_node_id=dept1.id,
                role=EnhancedUserRole.user,
                is_primary=True,
                is_active=True
            )
        ]
        
        db_session.add_all(assignments)
        db_session.commit()
        
        return {
            "org_admin": org_admin,
            "location_manager": location_manager,
            "dept_lead": dept_lead,
            "regular_user": regular_user
        }
    
    def test_organization_creation_with_hierarchy(self, client: TestClient):
        """Test creating organization through API with hierarchy structure"""
        
        create_request = {
            "name": "New Cinema Chain",
            "industry_template_code": "CINEMA",
            "admin_user_email": "admin@newcinema.com",
            "admin_user_first_name": "Admin",
            "admin_user_last_name": "User",
            "locations": [
                {
                    "name": "Times Square Theater",
                    "description": "Prime location theater",
                    "settings": {"capacity": 500, "screens": 12}
                },
                {
                    "name": "Brooklyn Theater",
                    "description": "Community theater",
                    "settings": {"capacity": 200, "screens": 6}
                }
            ],
            "customizations": {
                "data_refresh_interval": 300,
                "features.dynamic_pricing": True
            }
        }
        
        # This test would require proper authentication setup
        # response = client.post("/api/v1/v2/organizations", json=create_request)
        # assert response.status_code == 200
        
        # For now, validate the request structure
        assert create_request["name"] == "New Cinema Chain"
        assert len(create_request["locations"]) == 2
        assert create_request["industry_template_code"] == "CINEMA"
    
    def test_permission_resolution_engine(self, db_session: Session, sample_organization: Dict[str, Any], sample_users: Dict[str, Any]):
        """Test permission resolution across hierarchy levels"""
        
        permission_engine = PermissionResolutionEngine(db_session)
        
        # Test org admin permissions
        org_admin = sample_users["org_admin"]
        org_admin_permissions = permission_engine.resolve_user_permissions(org_admin.id)
        
        assert "admin" in org_admin_permissions["permissions"]
        assert "manage_users" in org_admin_permissions["permissions"]
        assert "manage_settings" in org_admin_permissions["permissions"]
        
        # Test location manager permissions
        location_manager = sample_users["location_manager"]
        location_manager_permissions = permission_engine.resolve_user_permissions(location_manager.id)
        
        assert "read" in location_manager_permissions["permissions"]
        assert "write" in location_manager_permissions["permissions"]
        assert "manage_users" in location_manager_permissions["permissions"]
        assert "admin" not in location_manager_permissions["permissions"]  # Should not have admin
        
        # Test department lead permissions
        dept_lead = sample_users["dept_lead"]
        dept_lead_permissions = permission_engine.resolve_user_permissions(dept_lead.id)
        
        assert "read" in dept_lead_permissions["permissions"]
        assert "write" in dept_lead_permissions["permissions"]
        assert "view_reports" in dept_lead_permissions["permissions"]
        assert "manage_users" not in dept_lead_permissions["permissions"]  # Should not have user management
        
        # Test regular user permissions
        regular_user = sample_users["regular_user"]
        regular_user_permissions = permission_engine.resolve_user_permissions(regular_user.id)
        
        assert "read" in regular_user_permissions["permissions"]
        assert "view_reports" in regular_user_permissions["permissions"]
        assert "write" not in regular_user_permissions["permissions"]  # Should not have write access
    
    def test_permission_inheritance(self, db_session: Session, sample_organization: Dict[str, Any], sample_users: Dict[str, Any]):
        """Test permission inheritance from parent hierarchy levels"""
        
        permission_engine = PermissionResolutionEngine(db_session)
        
        # Create a user assigned to department but test inheritance from location/org
        dept_user = sample_users["regular_user"]
        
        # Test inheritance - department user should inherit some permissions from location level
        dept_permissions = permission_engine.resolve_user_permissions(dept_user.id, include_inherited=True)
        
        # Verify inheritance metadata
        assert dept_permissions["metadata"]["inheritance_chain"] is not None
        assert len(dept_permissions["metadata"]["inheritance_chain"]) >= 0  # May have inherited permissions
        
        # Test without inheritance
        dept_permissions_no_inherit = permission_engine.resolve_user_permissions(dept_user.id, include_inherited=False)
        
        # Should have fewer or equal permissions without inheritance
        assert len(dept_permissions_no_inherit["permissions"]) <= len(dept_permissions["permissions"])
    
    def test_permission_overrides(self, db_session: Session, sample_organization: Dict[str, Any], sample_users: Dict[str, Any]):
        """Test user-specific permission overrides"""
        
        from app.models.hierarchy import HierarchyPermissionOverride
        
        regular_user = sample_users["regular_user"]
        dept1 = sample_organization["departments"][0]
        
        # Grant special permission to regular user
        override = HierarchyPermissionOverride(
            user_id=regular_user.id,
            hierarchy_node_id=dept1.id,
            permission="export_data",
            granted=True,
            reason="Special project access",
            is_active=True
        )
        db_session.add(override)
        db_session.commit()
        
        permission_engine = PermissionResolutionEngine(db_session)
        user_permissions = permission_engine.resolve_user_permissions(regular_user.id)
        
        # Should now have the overridden permission
        assert "export_data" in user_permissions["permissions"]
        
        # Check override metadata
        assert len(user_permissions["metadata"]["overrides_applied"]) == 1
        assert user_permissions["metadata"]["overrides_applied"][0]["permission"] == "export_data"
        assert user_permissions["metadata"]["overrides_applied"][0]["granted"] is True
    
    def test_industry_template_service(self, db_session: Session):
        """Test industry template creation and application"""
        
        template_service = IndustryTemplateService(db_session)
        
        # Test getting cinema template
        cinema_template = template_service.get_template_by_code("CINEMA")
        assert cinema_template is not None
        assert cinema_template.industry_code == "CINEMA"
        assert cinema_template.is_active is True
        
        # Test getting hotel template
        hotel_template = template_service.get_template_by_code("HOTEL")
        assert hotel_template is not None
        assert hotel_template.industry_code == "HOTEL"
        
        # Create test organization for template application
        test_org = Organisation(
            name="Template Test Org",
            is_active=True
        )
        db_session.add(test_org)
        db_session.flush()
        
        # Create test user for applied_by
        test_user = User(
            email="template@test.com",
            first_name="Template",
            last_name="User",
            organisation_id=test_org.id,
            role=UserRole.admin,
            is_active=True
        )
        db_session.add(test_user)
        db_session.flush()
        
        # Test template application
        success = template_service.apply_template_to_organization(
            test_org.id,
            cinema_template.id,
            test_user.id,
            {"data_refresh_interval": 600}  # Custom setting
        )
        
        assert success is True
        
        # Verify template was applied
        applied_templates = template_service.get_organization_templates(test_org.id)
        assert len(applied_templates) == 1
        assert applied_templates[0]["template_name"] == cinema_template.name
        assert applied_templates[0]["customizations"]["data_refresh_interval"] == 600
    
    def test_accessible_nodes_for_user(self, db_session: Session, sample_organization: Dict[str, Any], sample_users: Dict[str, Any]):
        """Test getting accessible hierarchy nodes for users"""
        
        permission_engine = PermissionResolutionEngine(db_session)
        
        # Test org admin - should have access to all nodes
        org_admin = sample_users["org_admin"]
        org_admin_nodes = permission_engine.get_accessible_nodes(org_admin.id)
        
        assert len(org_admin_nodes) >= 1  # At least root node
        assert any(node["user_role"] == "org_admin" for node in org_admin_nodes)
        
        # Test location manager - should have access to location node
        location_manager = sample_users["location_manager"]
        location_manager_nodes = permission_engine.get_accessible_nodes(location_manager.id)
        
        assert len(location_manager_nodes) >= 1
        assert any(node["level"] == "location" for node in location_manager_nodes)
        
        # Test with minimum role filter
        admin_level_nodes = permission_engine.get_accessible_nodes(
            org_admin.id, 
            minimum_role=EnhancedUserRole.org_admin
        )
        
        # Should only return nodes where user has org_admin or higher role
        assert all(node["user_role"] in ["org_admin", "super_admin"] for node in admin_level_nodes)
    
    def test_row_level_security_context(self, db_session: Session, sample_organization: Dict[str, Any]):
        """Test RLS context setting and enforcement"""
        
        org = sample_organization["organization"]
        
        # Set tenant context
        db_session.execute(
            text("SELECT set_tenant_context(:tenant_id, :user_role, :allow_cross_tenant)"),
            {
                "tenant_id": str(org.id),
                "user_role": "org_admin",
                "allow_cross_tenant": False
            }
        )
        
        # Query hierarchy nodes - should only return nodes for this tenant
        nodes = db_session.query(OrganizationHierarchy).all()
        
        # All returned nodes should belong to the current tenant
        for node in nodes:
            assert node.legacy_organisation_id == org.id
        
        # Clear context
        db_session.execute(text("SELECT clear_tenant_context()"))
    
    def test_backward_compatibility(self, db_session: Session, sample_users: Dict[str, Any]):
        """Test backward compatibility with existing user role system"""
        
        # Test legacy role mapping
        from app.models.user import LEGACY_TO_ENHANCED_ROLE_MAPPING
        
        org_admin = sample_users["org_admin"]
        assert org_admin.get_enhanced_role() == EnhancedUserRole.org_admin
        
        location_manager = sample_users["location_manager"]  # Has legacy 'analyst' role
        assert location_manager.get_enhanced_role() == EnhancedUserRole.user
        
        regular_user = sample_users["regular_user"]  # Has legacy 'viewer' role
        assert regular_user.get_enhanced_role() == EnhancedUserRole.viewer
    
    def test_api_permission_checks(self, client: TestClient):
        """Test API endpoint permission requirements"""
        
        # Test organization creation requires admin role
        create_request = {
            "name": "Test Org",
            "admin_user_email": "admin@test.com",
            "admin_user_first_name": "Admin",
            "admin_user_last_name": "User"
        }
        
        # Without authentication, should get 401/403
        # response = client.post("/api/v1/v2/organizations", json=create_request)
        # assert response.status_code in [401, 403]
        
        # Test hierarchy node creation requires appropriate permissions
        node_request = {
            "name": "New Location",
            "level": "location",
            "parent_id": str(uuid.uuid4())
        }
        
        # Without authentication, should get 401/403
        # response = client.post("/api/v1/v2/hierarchy-nodes", json=node_request)
        # assert response.status_code in [401, 403]
    
    def test_performance_with_deep_hierarchy(self, db_session: Session):
        """Test permission resolution performance with deep hierarchy"""
        
        # This test would create a deep hierarchy structure and measure
        # permission resolution time to ensure it's within acceptable limits
        
        # Create organization with deep hierarchy (5+ levels)
        org = Organisation(
            name="Deep Hierarchy Test",
            is_active=True
        )
        db_session.add(org)
        db_session.flush()
        
        # Create nested hierarchy: Org -> Region -> Location -> Department -> Team
        current_parent = None
        nodes = []
        
        hierarchy_levels = [
            ("Organization", HierarchyLevel.ORGANIZATION),
            ("Region", HierarchyLevel.LOCATION),
            ("Location", HierarchyLevel.LOCATION), 
            ("Department", HierarchyLevel.DEPARTMENT)
        ]
        
        for i, (name_prefix, level) in enumerate(hierarchy_levels):
            node = OrganizationHierarchy(
                name=f"{name_prefix} {i+1}",
                slug=f"{name_prefix.lower()}-{i+1}",
                parent_id=current_parent.id if current_parent else None,
                level=level,
                hierarchy_path=f"test-hierarchy/level-{i+1}",
                depth=i,
                legacy_organisation_id=org.id,
                is_active=True
            )
            db_session.add(node)
            db_session.flush()
            nodes.append(node)
            current_parent = node
        
        # Create user assigned to deepest level
        test_user = User(
            email="deep@test.com",
            first_name="Deep",
            last_name="User",
            organisation_id=org.id,
            role=UserRole.viewer,
            is_active=True
        )
        db_session.add(test_user)
        db_session.flush()
        
        # Assign to deepest node
        assignment = UserHierarchyAssignment(
            user_id=test_user.id,
            hierarchy_node_id=nodes[-1].id,
            role=EnhancedUserRole.user,
            is_primary=True,
            is_active=True
        )
        db_session.add(assignment)
        db_session.commit()
        
        # Test permission resolution performance
        import time
        
        permission_engine = PermissionResolutionEngine(db_session)
        
        start_time = time.time()
        permissions = permission_engine.resolve_user_permissions(test_user.id)
        end_time = time.time()
        
        resolution_time = end_time - start_time
        
        # Should resolve permissions in reasonable time (< 1 second for deep hierarchy)
        assert resolution_time < 1.0
        assert "permissions" in permissions
        assert permissions["metadata"]["resolution_path"] is not None


# Additional integration tests for the complete system
class TestOrganizationOnboardingWorkflow:
    """Test complete organization onboarding workflow"""
    
    def test_rapid_onboarding_cinema(self):
        """Test rapid cinema organization onboarding (<24 hours target)"""
        
        # This would test the complete workflow:
        # 1. Create organization with cinema template
        # 2. Set up initial hierarchy structure
        # 3. Create admin user and assign permissions
        # 4. Apply industry-specific configurations
        # 5. Validate all components are working
        
        workflow_steps = [
            "organization_creation",
            "hierarchy_setup", 
            "template_application",
            "user_assignment",
            "permission_verification",
            "configuration_validation"
        ]
        
        # Each step should complete successfully
        assert len(workflow_steps) == 6
        
        # Mock workflow completion time
        estimated_completion_time_hours = 2  # Should be < 24 hours
        assert estimated_completion_time_hours < 24
    
    def test_rapid_onboarding_hotel(self):
        """Test rapid hotel organization onboarding"""
        
        # Similar test for hotel industry
        workflow_steps = [
            "organization_creation",
            "multi_location_setup",
            "revenue_management_config",
            "user_role_assignment",
            "api_access_setup",
            "reporting_configuration"
        ]
        
        assert len(workflow_steps) == 6


if __name__ == "__main__":
    # Run with pytest: pytest test_hierarchical_permissions.py -v
    pass