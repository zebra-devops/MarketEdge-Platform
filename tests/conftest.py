import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from app.data.config.data_layer_config import create_test_config
from app.data.platform_data_layer import PlatformDataLayer
from app.data.interfaces.base import DataSourceType, QueryParams, DataResponse


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration for data layer"""
    return create_test_config()


@pytest.fixture
def mock_supabase_response() -> Dict[str, Any]:
    """Mock Supabase response data"""
    return {
        "data": [
            {
                "id": 1,
                "org_id": "test-org-123",
                "market": "manchester",
                "competitor_name": "vue",
                "date": "2024-01-15",
                "price": 12.50,
                "availability": True,
                "created_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": 2,
                "org_id": "test-org-123",
                "market": "manchester",
                "competitor_name": "cineworld",
                "date": "2024-01-15",
                "price": 11.99,
                "availability": True,
                "created_at": "2024-01-15T10:00:00Z"
            }
        ],
        "count": 2,
        "error": None
    }


@pytest.fixture
def mock_reference_data() -> Dict[str, Any]:
    """Mock reference data"""
    return {
        "data": [
            {"id": 1, "name": "manchester", "region": "north-west", "active": True},
            {"id": 2, "name": "london", "region": "south-east", "active": True},
            {"id": 3, "name": "birmingham", "region": "west-midlands", "active": True}
        ],
        "count": 3,
        "error": None
    }


@pytest.fixture
def sample_query_params() -> QueryParams:
    """Sample query parameters for testing"""
    return QueryParams(
        filters={"competitors": ["vue", "cineworld"]},
        limit=10,
        offset=0,
        order_by=["-date", "competitor_name"]
    )


@pytest.fixture
def sample_data_response() -> DataResponse:
    """Sample data response for testing"""
    return DataResponse(
        data=[{"id": 1, "name": "test"}],
        source=DataSourceType.SUPABASE,
        cached=False,
        total_count=1,
        execution_time_ms=50.0
    )


@pytest.fixture
async def data_layer(test_config) -> PlatformDataLayer:
    """Platform data layer instance for testing"""
    layer = PlatformDataLayer(test_config)
    # Don't initialize automatically - let tests control initialization
    yield layer
    if layer.is_initialized:
        await layer.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = 0
    return mock_redis


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    return mock_client, mock_table


# Test database cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_databases():
    """Auto-cleanup fixture to remove test database files after each test"""
    yield
    # Cleanup any remaining test database files
    import glob
    import os
    
    test_db_pattern = "./test_tenant_security*.db"
    for db_file in glob.glob(test_db_pattern):
        try:
            os.unlink(db_file)
        except OSError:
            pass  # File might be in use, ignore


@pytest.fixture
def isolated_database_session():
    """Create an isolated database session for each test with complete data isolation"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    import uuid
    import os
    import tempfile
    
    # Create unique SQLite database for this test in temp directory
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = tempfile.gettempdir()
    test_db_path = os.path.join(temp_dir, f"test_isolated_{unique_id}.db")
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
        # Cleanup
        try:
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
            pass  # File might be in use, ignore


# Async test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL with proper configuration for multi-tenant testing"""
    from app.core.config import settings
    return settings.get_test_database_url()


@pytest.fixture
def database_engine(test_database_url):
    """Create database engine for testing with proper isolation and cleanup"""
    from sqlalchemy import create_engine, text
    from app.models.base import Base
    import os
    import tempfile
    
    # Force SQLite for testing to avoid PostgreSQL hostname resolution issues
    is_sqlite = test_database_url.startswith('sqlite')
    
    # If PostgreSQL URL provided, convert to SQLite for better test isolation
    if not is_sqlite:
        # Create unique SQLite database for this test session
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        test_database_url = f"sqlite:///./test_tenant_security_{unique_id}.db"
        is_sqlite = True
    
    if is_sqlite:
        # Ensure database file is writable by creating in temp directory
        if test_database_url.startswith('sqlite:///'):
            db_path = test_database_url.replace('sqlite:///', '')
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        
        engine = create_engine(
            test_database_url,
            echo=False,
            connect_args={
                "check_same_thread": False,
                "timeout": 20,
                # Remove isolation_level=None to avoid autocommit issues
            }
        )
    else:
        # Fallback to PostgreSQL if somehow still needed
        engine = create_engine(
            test_database_url,
            echo=False,
            connect_args={
                "application_name": "platform_wrapper_test"
            }
        )
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Enable RLS for multi-tenant testing (only for PostgreSQL)
    if not is_sqlite:
        with engine.connect() as conn:
            # Enable RLS on all tenant-specific tables
            rls_tables = [
                'organisations', 'users', 'audit_logs', 'feature_flag_usage',
                'feature_flag_overrides', 'organisation_modules', 'module_configurations',
                'module_usage_logs', 'organisation_tool_access'
            ]
            
            for table_name in rls_tables:
                try:
                    # Enable RLS
                    conn.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
                    
                    # Create tenant isolation policy
                    conn.execute(text(f"""
                        CREATE POLICY IF NOT EXISTS tenant_isolation_{table_name} ON {table_name}
                        FOR ALL TO PUBLIC
                        USING (organisation_id::text = current_setting('rls.tenant_id', true))
                    """))
                    
                    # Create super admin access policy
                    conn.execute(text(f"""
                        CREATE POLICY IF NOT EXISTS super_admin_access_{table_name} ON {table_name}
                        FOR ALL TO PUBLIC
                        USING (current_setting('rls.bypass_tenant_isolation', true)::boolean = true)
                    """))
                    
                except Exception as e:
                    # Some tables might not exist or policies might already exist
                    continue
                    
            conn.commit()
    
    yield engine
    
    # Comprehensive cleanup
    try:
        Base.metadata.drop_all(engine)
        engine.dispose()
        
        # Remove SQLite file if it exists
        if is_sqlite and test_database_url.startswith('sqlite:///'):
            db_file = test_database_url.replace('sqlite:///', '')
            if os.path.exists(db_file):
                try:
                    os.unlink(db_file)
                except OSError:
                    pass  # File might be in use, ignore
                    
    except Exception:
        pass  # Cleanup errors shouldn't fail tests 