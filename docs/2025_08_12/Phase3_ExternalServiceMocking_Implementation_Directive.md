# Phase 3 External Service Mocking Implementation Directive
*Issue #7 - Test Pass Rate >85% Target*

## Current Status Analysis
- **Current**: 153/254 tests passing (60.2% pass rate)  
- **Target**: >85% pass rate (222+ tests passing)
- **Gap**: Need +69 tests to reach target

## Priority 1: Redis Service Mocking Fixes (12 tests - High Impact)

### Issues Identified:
1. **AsyncMock Problems**: `'async for' requires an object with __aiter__ method, got coroutine`
2. **Call Assertion Issues**: `Expected 'from_url' to have been called once. Called 3 times`  
3. **Mock Structure Mismatches**: Redis client mock not properly structured
4. **JSON Serialization**: Redis set method not being called in mocked environment

### Implementation Requirements:
- Fix AsyncMock patterns for Redis cache manager
- Correct mock assertion patterns for multi-connection Redis setup
- Implement proper async iteration mocking for `scan_iter` operations
- Fix JSON serialization mocking patterns

## Priority 2: Supabase Service Mocking Fixes (11 tests - High Impact)

### Issues Identified:
1. **Mock Return Structure**: `'dict' object has no attribute 'data'` errors
2. **Health Check Failures**: Mock response structure mismatches  
3. **Subscription Mocking**: Event subscription patterns not properly mocked
4. **Client Closure**: Mock client not properly reset to None on close

### Implementation Requirements:
- Create proper Supabase response object mocking with `.data` attribute
- Fix health check mock responses to return proper structure
- Implement subscription event mocking patterns
- Ensure proper client cleanup in mocked environment

## Priority 3: Database Compatibility Issues (9 tests - Medium Impact)

### Issues Identified:
1. **PostgreSQL RLS Tests**: Failing in SQLite test environment
2. **Connection Pool Issues**: BrokenPipeError during test execution
3. **RLS Policy Testing**: Row Level Security not supported in SQLite

### Implementation Requirements:
- Create PostgreSQL-specific test skippping patterns for SQLite environment
- Implement database-agnostic RLS testing where possible
- Fix connection pool cleanup in test environment
- Consider PostgreSQL test container for RLS-specific tests

## Technical Implementation Approach

### Redis Mocking Strategy:
```python
# Fix AsyncMock patterns
@pytest.fixture
def mock_redis_client():
    mock_client = AsyncMock()
    # Properly mock async iteration
    mock_client.scan_iter.return_value.__aiter__ = AsyncMock()
    mock_client.scan_iter.return_value.__anext__ = AsyncMock(side_effect=StopAsyncIteration)
    return mock_client
```

### Supabase Mocking Strategy:
```python
# Fix response structure
@pytest.fixture  
def mock_supabase_response():
    response = MagicMock()
    response.data = [{"id": 1, "name": "test"}]
    response.count = 1
    return response
```

### Database Testing Strategy:
```python
# Database-agnostic testing
@pytest.mark.skipif(
    "postgresql" not in os.environ.get("DATABASE_URL", ""),
    reason="PostgreSQL-specific test"
)
def test_rls_policy():
    # PostgreSQL RLS test
    pass
```

## Success Metrics:
- Redis tests: 12 failing → 0 failing (12 test improvement)
- Supabase tests: 11 failing → 0 failing (11 test improvement) 
- Database tests: 9 ERROR → 4 passing, 5 skipped (9 test improvement)
- **Total Expected**: ~32 test improvements
- **Projected Pass Rate**: 185/254 = 72.8% (significant progress toward >85%)

## Phase 3 Execution Workflow:
1. **Fix Redis AsyncMock patterns** (immediate high impact)
2. **Fix Supabase response structure mocking** (immediate high impact)  
3. **Implement database-agnostic testing patterns** (medium impact)
4. **Validate cumulative test pass rate improvement**
5. **Identify remaining gaps for >85% target**

## Quality Assurance Requirements:
- All fixes must maintain existing passing tests (no regressions)
- Mock implementations must accurately represent real service behavior
- Test isolation must be maintained across all service mocking
- Performance impact of mocking should be minimal

**Implementation Priority**: Start with Redis and Supabase mocking as these represent 23 potential test improvements and are the highest impact for reaching the >85% target.**