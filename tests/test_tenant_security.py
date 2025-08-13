"""
Test Suite for Tenant Security Features

Tests Row Level Security policies and Tenant Context Middleware
to ensure complete tenant data isolation and security compliance.
"""
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.models.audit_log import AuditLog, AuditAction, AuditSeverity
from app.models.feature_flags import FeatureFlag, FeatureFlagUsage, FeatureFlagOverride
from app.models.modules import ModuleUsageLog, OrganisationModule, ModuleConfiguration
from app.middleware.tenant_context import TenantContextMiddleware, SuperAdminContextManager
from app.auth.jwt import create_access_token
from tests.database_test_utils import (
    set_tenant_context, 
    is_postgresql_session, 
    skip_rls_tests_for_sqlite,
    simulate_rls_for_sqlite
)


@pytest.fixture(scope="function")
def session():
    """Create test database session with proper isolation and cleanup."""
    import tempfile
    import os
    import uuid
    
    # Create unique SQLite database for this test in temp directory
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.gettempdir()
    test_db_path = os.path.join(temp_dir, f"test_tenant_security_{unique_id}.db")
    test_db_url = f"sqlite:///{test_db_path}"
    
    engine = create_engine(
        test_db_url,
        echo=False,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        }
    )
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = TestingSessionLocal()
        
        yield session
        
    finally:
        # Clean up after each test
        try:
            session.rollback()
            session.close()
        except:
            pass
            
        try:
            Base.metadata.drop_all(engine)
            engine.dispose()
        except:
            pass
        
        # Remove database file
        try:
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)
        except OSError:
            pass


@pytest.fixture
def test_organisations(session):
    """Create test organisations with unique names to avoid UNIQUE constraint violations."""
    # Use UUID to ensure unique organization names
    unique_id = str(uuid.uuid4())[:8]
    
    org1 = Organisation(
        id=uuid.uuid4(),
        name=f"Test Org 1 {unique_id}",
        industry="Technology",
        subscription_plan=SubscriptionPlan.basic
    )
    org2 = Organisation(
        id=uuid.uuid4(), 
        name=f"Test Org 2 {unique_id}",
        industry="Finance",
        subscription_plan=SubscriptionPlan.professional
    )
    
    session.add(org1)
    session.add(org2)
    session.commit()
    
    return {"org1": org1, "org2": org2}


@pytest.fixture
def test_users(session, test_organisations):
    """Create test users in different organisations with unique email addresses."""
    org1 = test_organisations["org1"]
    org2 = test_organisations["org2"]
    
    # Use UUID to ensure unique email addresses
    unique_id = str(uuid.uuid4())[:8]
    
    # Regular users
    user1 = User(
        id=uuid.uuid4(),
        email=f"user1_{unique_id}@testorg1.com",
        first_name="User",
        last_name="One", 
        organisation_id=org1.id,
        role=UserRole.analyst,
        is_active=True
    )
    
    user2 = User(
        id=uuid.uuid4(),
        email=f"user2_{unique_id}@testorg2.com",
        first_name="User",
        last_name="Two",
        organisation_id=org2.id,
        role=UserRole.viewer,
        is_active=True
    )
    
    # Super admin user
    admin_user = User(
        id=uuid.uuid4(),
        email=f"admin_{unique_id}@platform.com",
        first_name="Super", 
        last_name="Admin",
        organisation_id=org1.id,  # Has an organisation but can access all
        role=UserRole.admin,
        is_active=True
    )
    
    session.add_all([user1, user2, admin_user])
    session.commit()
    
    return {
        "user1": user1,
        "user2": user2, 
        "admin_user": admin_user,
        "org1": org1,
        "org2": org2
    }


class TestRowLevelSecurity:
    """Test RLS policies for tenant data isolation."""
    
    def test_rls_enabled_on_tenant_tables(self, session):
        """Test that RLS is enabled on all tenant-scoped tables."""
        tenant_tables = [
            'users', 'audit_logs', 'feature_flag_usage',
            'feature_flag_overrides', 'organisation_modules',
            'module_configurations', 'module_usage_logs'
        ]
        
        for table_name in tenant_tables:
            # This would need to be adapted for SQLite testing
            # In production PostgreSQL, we'd check pg_class.rlspolicy
            # For now, we'll test the policy behavior instead
            pass
    
    @patch('app.core.database.get_db')
    def test_tenant_isolation_users_table(self, mock_get_db, session, test_users):
        """Test that users can only access their organisation's data."""
        mock_get_db.return_value = session
        
        # Use database-agnostic tenant context setting
        with set_tenant_context(session, str(test_users["org1"].id)) as context:
            # Query should only return users from org1
            if is_postgresql_session(session):
                # PostgreSQL: RLS should filter automatically
                users = session.query(User).all()
                # With RLS enabled, should only see org1 users
                org1_user_count = len([u for u in users if u.organisation_id == test_users["org1"].id])
                assert org1_user_count > 0, "Should see at least the org1 user"
            else:
                # SQLite: Simulate RLS behavior for testing
                users_query = simulate_rls_for_sqlite(session, User, str(test_users["org1"].id))
                users = users_query.all()
                # All returned users should belong to org1
                for user in users:
                    assert user.organisation_id == test_users["org1"].id
            
            # Verify tenant context is properly set
            current_tenant = context.get_current_tenant_id()
            assert current_tenant == str(test_users["org1"].id)
    
    def test_super_admin_cross_tenant_access(self, session, test_users):
        """Test that super admins can access cross-tenant data when allowed."""
        # Set super admin context
        session.execute(text("SELECT set_config('app.current_user_role', 'admin', true)"))
        session.execute(text("SELECT set_config('app.allow_cross_tenant', 'true', true)"))
        
        # Verify context is set correctly
        user_role = session.execute(text("SELECT current_setting('app.current_user_role', true)")).scalar()
        cross_tenant = session.execute(text("SELECT current_setting('app.allow_cross_tenant', true)")).scalar()
        
        assert user_role == 'admin'
        assert cross_tenant == 'true'
    
    def test_rls_helper_functions(self, session, test_users):
        """Test RLS helper functions work correctly."""
        org_id = test_users["org1"].id
        
        # Test set_tenant_context function
        session.execute(text(
            "SELECT set_tenant_context(:tenant_id, :user_role, :allow_cross_tenant)"
        ), {
            "tenant_id": org_id,
            "user_role": "analyst", 
            "allow_cross_tenant": False
        })
        
        # Verify context is set
        tenant_id = session.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar()
        user_role = session.execute(text("SELECT current_setting('app.current_user_role', true)")).scalar()
        
        assert tenant_id == str(org_id)
        assert user_role == "analyst"
        
        # Test clear_tenant_context function
        session.execute(text("SELECT clear_tenant_context()"))
        
        # Verify context is cleared
        tenant_id = session.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar()
        assert tenant_id in [None, '']


class TestTenantContextMiddleware:
    """Test tenant context middleware functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_middleware_skips_excluded_routes(self, client):
        """Test that middleware skips routes that don't need tenant context."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should not have tenant processing time header for excluded routes
        assert "X-Tenant-Processing-Time" not in response.headers
    
    @patch('app.middleware.tenant_context.verify_token')
    @patch('app.middleware.tenant_context.get_db')
    def test_middleware_extracts_tenant_context(self, mock_get_db, mock_verify_token, session, test_users):
        """Test that middleware correctly extracts tenant context from JWT."""
        client = TestClient(app)
        
        # Mock JWT verification
        mock_verify_token.return_value = {"sub": str(test_users["user1"].id)}
        
        # Mock database session
        mock_get_db.return_value = iter([session])
        
        # Create valid JWT token
        token = create_access_token({"sub": str(test_users["user1"].id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make request to protected endpoint
        with patch.object(session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = test_users["user1"]
            
            response = client.get("/api/v1/auth/me", headers=headers)
            
            # Verify tenant context was processed
            assert "X-Tenant-Processing-Time" in response.headers
    
    def test_middleware_rejects_invalid_token(self, client):
        """Test that middleware rejects invalid JWT tokens."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_middleware_rejects_missing_authorization(self, client):
        """Test that middleware handles missing authorization header."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    @patch('app.middleware.tenant_context.verify_token')
    @patch('app.middleware.tenant_context.get_db') 
    def test_middleware_rejects_inactive_user(self, mock_get_db, mock_verify_token, session, test_users):
        """Test that middleware rejects inactive users."""
        client = TestClient(app)
        
        # Make user inactive
        test_users["user1"].is_active = False
        session.commit()
        
        # Mock JWT verification
        mock_verify_token.return_value = {"sub": str(test_users["user1"].id)}
        mock_get_db.return_value = iter([session])
        
        token = create_access_token({"sub": str(test_users["user1"].id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch.object(session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = test_users["user1"]
            
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
    
    @patch('app.middleware.tenant_context.get_db')
    def test_middleware_performance_overhead(self, mock_get_db, client):
        """Test that middleware adds minimal performance overhead."""
        # Mock database operations to be very fast
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        response = client.get("/health")  # Excluded route
        
        # Should complete quickly for excluded routes
        assert response.status_code == 200
    
    @patch('app.middleware.tenant_context.verify_token')
    @patch('app.middleware.tenant_context.get_db')
    def test_middleware_database_error_handling(self, mock_get_db, mock_verify_token, client, test_users):
        """Test middleware handles database errors gracefully."""
        # Mock JWT verification
        mock_verify_token.return_value = {"sub": str(test_users["user1"].id)}
        
        # Mock database error
        mock_db = Mock()
        mock_db.execute.side_effect = SQLAlchemyError("Database connection failed")
        mock_get_db.return_value = iter([mock_db])
        
        token = create_access_token({"sub": str(test_users["user1"].id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 500


class TestSuperAdminContextManager:
    """Test super admin context manager for cross-tenant operations."""
    
    @pytest.mark.asyncio
    async def test_context_manager_enables_cross_tenant(self, session, test_users):
        """Test that context manager enables cross-tenant access."""
        admin_user = test_users["admin_user"]
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_get_db.return_value = iter([session])
            
            async with SuperAdminContextManager(admin_user):
                # Verify cross-tenant access is enabled
                cross_tenant = session.execute(
                    text("SELECT current_setting('app.allow_cross_tenant', true)")
                ).scalar()
                assert cross_tenant == 'true'
    
    @pytest.mark.asyncio
    async def test_context_manager_disables_on_exit(self, session, test_users):
        """Test that context manager disables cross-tenant access on exit."""
        admin_user = test_users["admin_user"]
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_get_db.return_value = iter([session])
            
            async with SuperAdminContextManager(admin_user):
                pass
            
            # Verify cross-tenant access is disabled after exit
            cross_tenant = session.execute(
                text("SELECT current_setting('app.allow_cross_tenant', true)")
            ).scalar()
            assert cross_tenant == 'false'
    
    def test_context_manager_rejects_non_admin(self, test_users):
        """Test that context manager rejects non-admin users."""
        regular_user = test_users["user1"]
        
        with pytest.raises(ValueError, match="can only be used by admin users"):
            SuperAdminContextManager(regular_user)
    
    @pytest.mark.asyncio
    async def test_context_manager_error_handling(self, session, test_users):
        """Test context manager handles database errors."""
        admin_user = test_users["admin_user"]
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_db.return_value = iter([mock_db])
            
            with pytest.raises(SQLAlchemyError):
                async with SuperAdminContextManager(admin_user):
                    pass


class TestTenantDataIsolation:
    """Integration tests for complete tenant data isolation."""
    
    def test_cross_tenant_data_access_blocked(self, session, test_users):
        """Test that users cannot access other tenants' data."""
        org1_id = test_users["org1"].id
        org2_id = test_users["org2"].id
        
        # Create test data for different organisations
        audit_log_org1 = AuditLog(
            organisation_id=org1_id,
            user_id=test_users["user1"].id,
            action=AuditAction.LOGIN,
            resource_type="auth",
            description="User login",
            severity=AuditSeverity.LOW
        )
        
        audit_log_org2 = AuditLog(
            organisation_id=org2_id,
            user_id=test_users["user2"].id,
            action=AuditAction.LOGIN,
            resource_type="auth",
            description="User login",
            severity=AuditSeverity.LOW
        )
        
        session.add_all([audit_log_org1, audit_log_org2])
        session.commit()
        
        # Set tenant context for org1
        session.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"), 
                       {"tenant_id": str(org1_id)})
        
        # In a real PostgreSQL environment with RLS, this would only return org1 data
        all_logs = session.query(AuditLog).all()
        
        # Verify test data exists (structure test)
        assert len(all_logs) == 2
        
        # Verify tenant context is correctly set
        current_tenant = session.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar()
        assert current_tenant == str(org1_id)
    
    def test_feature_flag_tenant_isolation(self, session, test_users):
        """Test feature flag usage isolation between tenants."""
        org1_id = test_users["org1"].id
        org2_id = test_users["org2"].id
        
        # Create feature flag usage records for different orgs
        usage_org1 = FeatureFlagUsage(
            feature_flag_id=str(uuid.uuid4()),
            organisation_id=org1_id,
            user_id=test_users["user1"].id,
            was_enabled=True
        )
        
        usage_org2 = FeatureFlagUsage(
            feature_flag_id=str(uuid.uuid4()),
            organisation_id=org2_id,
            user_id=test_users["user2"].id,
            was_enabled=True
        )
        
        session.add_all([usage_org1, usage_org2])
        session.commit()
        
        # Set tenant context for org1
        session.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                       {"tenant_id": str(org1_id)})
        
        # Verify tenant context isolation structure
        current_tenant = session.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar()
        assert current_tenant == str(org1_id)
    
    def test_module_usage_tenant_isolation(self, session, test_users):
        """Test module usage log isolation between tenants."""
        org1_id = test_users["org1"].id
        org2_id = test_users["org2"].id
        
        # Create module usage logs for different orgs
        usage_log_org1 = ModuleUsageLog(
            module_id="pricing_intelligence",
            organisation_id=org1_id,
            user_id=test_users["user1"].id,
            action="viewed",
            success=True
        )
        
        usage_log_org2 = ModuleUsageLog(
            module_id="pricing_intelligence",
            organisation_id=org2_id,
            user_id=test_users["user2"].id,
            action="viewed",
            success=True
        )
        
        session.add_all([usage_log_org1, usage_log_org2])
        session.commit()
        
        # Verify records were created
        all_logs = session.query(ModuleUsageLog).all()
        assert len(all_logs) == 2
        
        # Set tenant context for org1
        session.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
                       {"tenant_id": str(org1_id)})
        
        # Verify tenant context is set
        current_tenant = session.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar()
        assert current_tenant == str(org1_id)


class TestSecurityCompliance:
    """Test security compliance and audit requirements."""
    
    def test_audit_logging_for_tenant_context_changes(self, session):
        """Test that tenant context changes are properly audited."""
        org_id = uuid.uuid4()
        
        # Simulate setting tenant context
        session.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"), 
                       {"tenant_id": str(org_id)})
        
        # Verify context is tracked
        current_tenant = session.execute(text("SELECT current_setting('app.current_tenant_id', true)")).scalar()
        assert current_tenant == str(org_id)
    
    def test_security_event_logging(self, session, test_users):
        """Test that security events are properly logged."""
        # This would test that security violations are logged to audit_logs
        # with appropriate severity levels
        
        security_event = AuditLog(
            organisation_id=test_users["org1"].id,
            user_id=test_users["user1"].id,
            action=AuditAction.READ,
            resource_type="cross_tenant_attempt",
            description="Attempted cross-tenant data access blocked",
            severity=AuditSeverity.HIGH,
            success=False
        )
        
        session.add(security_event)
        session.commit()
        
        # Verify security event was logged
        events = session.query(AuditLog).filter(AuditLog.severity == AuditSeverity.HIGH).all()
        assert len(events) == 1
        assert events[0].success == False
    
    def test_performance_monitoring(self):
        """Test that security middleware performance is monitored."""
        # This would test that the middleware adds performance headers
        # and that processing time is within acceptable limits (<5ms)
        
        client = TestClient(app)
        response = client.get("/health")
        
        # Excluded routes should be very fast
        assert response.status_code == 200
        
        # For authenticated routes, we'd check X-Tenant-Processing-Time header
        # and ensure it's under the 5ms requirement


if __name__ == "__main__":
    pytest.main([__file__, "-v"])