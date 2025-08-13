"""
Security Load Testing

Tests the security middleware and RLS policies under load conditions
to ensure performance requirements are met under realistic usage.
"""
import pytest
import time
import uuid
import asyncio
import concurrent.futures
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole
from app.models.organisation import Organisation, SubscriptionPlan
from app.auth.jwt import create_access_token
from app.middleware.tenant_context import TenantContextMiddleware


class TestSecurityLoadPerformance:
    """Test security middleware performance under load."""
    
    @pytest.fixture
    def mock_test_setup(self):
        """Set up mocked components for load testing."""
        # Create test data
        org1 = Organisation(
            id=uuid.uuid4(),
            name="Load Test Org 1",
            industry="Technology", 
            subscription_plan=SubscriptionPlan.professional
        )
        
        user1 = User(
            id=uuid.uuid4(),
            email="loadtest@org1.com",
            first_name="Load",
            last_name="Test",
            organisation_id=org1.id,
            role=UserRole.analyst,
            is_active=True
        )
        
        return {"org1": org1, "user1": user1}
    
    @patch('app.middleware.tenant_context.get_db')
    @patch('app.middleware.tenant_context.verify_token')
    def test_concurrent_requests_performance(self, mock_verify_token, mock_get_db, mock_test_setup):
        """Test middleware performance with concurrent requests."""
        # Set up mocks for fast operation
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_test_setup["user1"]
        mock_db.execute.return_value = None
        mock_db.commit.return_value = None
        mock_db.close.return_value = None
        mock_get_db.return_value = iter([mock_db])
        
        mock_verify_token.return_value = {"sub": str(mock_test_setup["user1"].id)}
        
        client = TestClient(app)
        token = create_access_token({"sub": str(mock_test_setup["user1"].id)})
        headers = {"Authorization": f"Bearer {token}"}
        
        def make_request():
            """Make a single authenticated request."""
            start_time = time.time()
            response = client.get("/api/v1/auth/me", headers=headers)
            request_time = (time.time() - start_time) * 1000
            
            # Extract middleware processing time
            middleware_time = 0.0
            if "X-Tenant-Processing-Time" in response.headers:
                middleware_time = float(
                    response.headers["X-Tenant-Processing-Time"].replace("ms", "")
                )
            
            return {
                "status_code": response.status_code,
                "total_time": request_time,
                "middleware_time": middleware_time
            }
        
        # Test with 20 concurrent requests
        num_concurrent = 20
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            start_time = time.time()
            
            # Submit all requests
            futures = [executor.submit(make_request) for _ in range(num_concurrent)]
            
            # Collect results
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            total_time = (time.time() - start_time) * 1000
        
        # Analyze results
        successful_requests = [r for r in results if r["status_code"] == 200]
        middleware_times = [r["middleware_time"] for r in successful_requests if r["middleware_time"] > 0]
        total_times = [r["total_time"] for r in successful_requests]
        
        # Performance assertions
        assert len(successful_requests) == num_concurrent, f"Expected {num_concurrent} successful requests"
        
        # All middleware processing should be under 5ms
        if middleware_times:
            max_middleware_time = max(middleware_times)
            avg_middleware_time = sum(middleware_times) / len(middleware_times)
            
            assert max_middleware_time < 5.0, f"Max middleware time {max_middleware_time}ms exceeds 5ms limit"
            assert avg_middleware_time < 3.0, f"Avg middleware time {avg_middleware_time}ms too high"
        
        # Total request processing should be reasonable
        max_total_time = max(total_times)
        avg_total_time = sum(total_times) / len(total_times)
        
        assert max_total_time < 200.0, f"Max total time {max_total_time}ms too slow"
        assert avg_total_time < 100.0, f"Avg total time {avg_total_time}ms too slow"
        
        # All requests should complete within reasonable time
        assert total_time < 2000.0, f"Total time for {num_concurrent} requests {total_time}ms too slow"
    
    @patch('app.middleware.tenant_context.get_db')
    @patch('app.middleware.tenant_context.verify_token')
    def test_rapid_context_switching_performance(self, mock_verify_token, mock_get_db):
        """Test performance with rapid tenant context switching."""
        # Create multiple test users for different orgs
        orgs = []
        users = []
        
        for i in range(5):
            org = Organisation(
                id=uuid.uuid4(),
                name=f"Context Test Org {i}",
                industry="Technology",
                subscription_plan=SubscriptionPlan.basic
            )
            user = User(
                id=uuid.uuid4(),
                email=f"contexttest{i}@org{i}.com",
                first_name=f"Context{i}",
                last_name="Test",
                organisation_id=org.id,
                role=UserRole.analyst,
                is_active=True
            )
            orgs.append(org)
            users.append(user)
        
        # Mock database to return different users
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        def mock_query_filter_first(user_id):
            # Return the appropriate user based on user_id
            for user in users:
                if str(user.id) == user_id:
                    return user
            return None
        
        client = TestClient(app)
        
        def test_context_switch(user_index, iterations=10):
            """Test rapid switching for a specific user."""
            user = users[user_index]
            
            # Set up mocks for this user
            mock_verify_token.return_value = {"sub": str(user.id)}
            mock_db.query.return_value.filter.return_value.first.return_value = user
            mock_db.execute.return_value = None
            mock_db.commit.return_value = None
            mock_db.close.return_value = None
            
            token = create_access_token({"sub": str(user.id)})
            headers = {"Authorization": f"Bearer {token}"}
            
            times = []
            for _ in range(iterations):
                start_time = time.time()
                response = client.get("/api/v1/auth/me", headers=headers)
                elapsed = (time.time() - start_time) * 1000
                
                times.append({
                    "time": elapsed,
                    "status": response.status_code,
                    "middleware_time": float(
                        response.headers.get("X-Tenant-Processing-Time", "0ms").replace("ms", "")
                    ) if "X-Tenant-Processing-Time" in response.headers else 0.0
                })
            
            return times
        
        # Test rapid switching between different tenant contexts
        all_results = []
        
        for user_index in range(len(users)):
            results = test_context_switch(user_index, 5)
            all_results.extend(results)
        
        # Analyze performance across all context switches
        successful_requests = [r for r in all_results if r["status"] == 200]
        middleware_times = [r["middleware_time"] for r in successful_requests if r["middleware_time"] > 0]
        total_times = [r["time"] for r in successful_requests]
        
        # Performance requirements for context switching
        assert len(successful_requests) == len(all_results), "All requests should succeed"
        
        if middleware_times:
            max_middleware = max(middleware_times)
            avg_middleware = sum(middleware_times) / len(middleware_times)
            
            assert max_middleware < 5.0, f"Max middleware time during switching {max_middleware}ms > 5ms"
            assert avg_middleware < 3.0, f"Avg middleware time during switching {avg_middleware}ms > 3ms"
        
        max_total = max(total_times)
        avg_total = sum(total_times) / len(total_times)
        
        assert max_total < 200.0, f"Max total time during switching {max_total}ms too slow"
        assert avg_total < 100.0, f"Avg total time during switching {avg_total}ms too slow"
    
    def test_middleware_memory_efficiency(self):
        """Test that middleware doesn't leak memory under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        middleware = TenantContextMiddleware(app)
        
        # Simulate many tenant context operations
        tenant_contexts = []
        for i in range(1000):
            tenant_contexts.append({
                "tenant_id": uuid.uuid4(),
                "user_role": "analyst",
                "user_id": uuid.uuid4()
            })
        
        # Memory usage should not grow significantly
        memory_samples = []
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_db.commit.return_value = None
            mock_db.close.return_value = None
            mock_get_db.return_value = iter([mock_db])
            
            # Process many tenant contexts
            for i, context in enumerate(tenant_contexts):
                asyncio.run(middleware._set_database_context(context))
                asyncio.run(middleware._clear_database_context())
                
                # Sample memory every 100 operations
                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (< 10MB for 1000 operations)
        assert memory_growth < 10.0, f"Memory grew by {memory_growth}MB - possible memory leak"
        
        # Memory usage should be stable (not continuously growing)
        if len(memory_samples) > 2:
            # Check that memory doesn't continuously grow
            memory_trend = memory_samples[-1] - memory_samples[0]
            assert memory_trend < 5.0, f"Memory shows growing trend of {memory_trend}MB"
    
    def test_error_handling_under_load(self):
        """Test that error handling works correctly under load conditions."""
        from app.middleware.tenant_context import TenantContextMiddleware
        
        middleware = TenantContextMiddleware(app)
        
        # Test with database errors
        error_count = 0
        success_count = 0
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            # Mix successful and failing database operations
            def mock_db_generator():
                mock_db = Mock()
                if error_count < 100:  # First 100 operations fail
                    mock_db.execute.side_effect = Exception("Database error")
                else:  # Next operations succeed
                    mock_db.execute.return_value = None
                    mock_db.commit.return_value = None
                mock_db.close.return_value = None
                return mock_db
            
            mock_get_db.return_value = iter([mock_db_generator()])
            
            # Process many operations with mixed success/failure
            for i in range(200):
                tenant_context = {
                    "tenant_id": uuid.uuid4(),
                    "user_role": "analyst", 
                    "user_id": uuid.uuid4()
                }
                
                try:
                    asyncio.run(middleware._set_database_context(tenant_context))
                    success_count += 1
                except Exception:
                    error_count += 1
                
                # Always try to clear context
                try:
                    asyncio.run(middleware._clear_database_context())
                except Exception:
                    pass
        
        # Should handle errors gracefully without crashing
        assert error_count > 0, "Should have encountered some errors"
        assert success_count > 0, "Should have some successful operations"
        
        # Error handling shouldn't prevent the process from continuing
        total_operations = error_count + success_count
        assert total_operations == 200, f"Expected 200 operations, got {total_operations}"


class TestSecurityUnderLoad:
    """Test that security properties hold under load conditions."""
    
    def test_tenant_isolation_under_concurrent_access(self):
        """Test that tenant isolation is maintained under concurrent access."""
        from app.middleware.tenant_context import TenantContextMiddleware
        
        # Create test tenant contexts
        tenant_contexts = []
        for i in range(10):
            tenant_contexts.append({
                "tenant_id": uuid.uuid4(),
                "user_role": "analyst",
                "user_id": uuid.uuid4()
            })
        
        middleware = TenantContextMiddleware(app)
        context_violations = []
        
        def process_tenant_context(context, iterations=20):
            """Process operations for a specific tenant context."""
            violations = []
            
            with patch('app.middleware.tenant_context.get_db') as mock_get_db:
                mock_db = Mock()
                
                # Track what tenant context was set
                set_contexts = []
                
                def track_set_config(query, params=None):
                    if params and 'tenant_id' in params:
                        set_contexts.append(params['tenant_id'])
                
                mock_db.execute.side_effect = track_set_config
                mock_db.commit.return_value = None
                mock_db.close.return_value = None
                mock_get_db.return_value = iter([mock_db])
                
                for _ in range(iterations):
                    try:
                        asyncio.run(middleware._set_database_context(context))
                        
                        # Verify that only the correct tenant ID was set
                        if set_contexts:
                            last_set_tenant = set_contexts[-1]
                            if last_set_tenant != str(context["tenant_id"]):
                                violations.append({
                                    "expected": str(context["tenant_id"]),
                                    "actual": last_set_tenant
                                })
                        
                        asyncio.run(middleware._clear_database_context())
                        
                    except Exception as e:
                        # Errors are OK, but context corruption is not
                        pass
            
            return violations
        
        # Run concurrent tenant context processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(process_tenant_context, context, 10)
                for context in tenant_contexts[:5]  # Test with 5 concurrent tenants
            ]
            
            all_violations = []
            for future in concurrent.futures.as_completed(futures):
                violations = future.result()
                all_violations.extend(violations)
        
        # Should have no tenant context violations
        assert len(all_violations) == 0, f"Found {len(all_violations)} tenant isolation violations: {all_violations}"
    
    def test_role_validation_under_load(self):
        """Test that role validation works correctly under load."""
        from app.middleware.tenant_context import TenantContextMiddleware
        
        middleware = TenantContextMiddleware(app)
        
        # Test with various roles including invalid ones
        test_roles = [
            "admin", "analyst", "viewer",  # Valid roles
            "invalid_role", "hacker", "", None  # Invalid roles
        ]
        
        validation_results = []
        
        with patch('app.middleware.tenant_context.get_db') as mock_get_db:
            mock_db = Mock()
            mock_db.commit.return_value = None
            mock_db.close.return_value = None
            mock_get_db.return_value = iter([mock_db])
            
            # Track role validation
            def track_role_config(query, params=None):
                if params and 'user_role' in params:
                    role = params['user_role']
                    validation_results.append({
                        "role": role,
                        "valid": role in ["admin", "analyst", "viewer"]
                    })
            
            mock_db.execute.side_effect = track_role_config
            
            # Test role validation under load
            for _ in range(100):
                for role in test_roles:
                    tenant_context = {
                        "tenant_id": uuid.uuid4(),
                        "user_role": role,
                        "user_id": uuid.uuid4()
                    }
                    
                    try:
                        asyncio.run(middleware._set_database_context(tenant_context))
                    except Exception:
                        # Exceptions are expected for invalid roles
                        pass
        
        # Analyze role validation results
        valid_role_sets = [r for r in validation_results if r["valid"]]
        invalid_role_attempts = [r for r in validation_results if not r["valid"]]
        
        # All valid roles should be processed
        assert len(valid_role_sets) > 0, "Should process valid roles"
        
        # Invalid roles should be rejected (not appear in results)
        assert len(invalid_role_attempts) == 0, f"Invalid roles were processed: {invalid_role_attempts}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])