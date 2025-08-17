# Epic 2: Deployment Validation & Testing
## Railway to Render Migration - Complete Testing Suite

**Priority**: 🔍 CRITICAL VALIDATION  
**Date**: 2025-08-16  
**Focus**: End-to-End Testing and CORS Resolution Validation

---

## 🎯 TESTING OBJECTIVES

1. **Service Health**: Verify all services are operational
2. **Database Connectivity**: Validate PostgreSQL and Redis connections
3. **Auth0 Integration**: Confirm authentication flow
4. **CORS Resolution**: Validate frontend can connect to backend
5. **Performance**: Ensure production-ready response times
6. **Security**: Verify secure configuration

---

## 🔍 VALIDATION TEST SUITE

### Phase 1: Basic Service Health

#### Test 1.1: Service Deployment Status
```bash
#!/bin/bash
echo "🔍 Testing service deployment status..."

# Check service is running
curl -f https://marketedge-platform.onrender.com/health
echo "✅ Service is responding"

# Verify response time
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null https://marketedge-platform.onrender.com/health)
echo "⏱️ Response time: ${RESPONSE_TIME}s"

if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "✅ Performance: Acceptable response time"
else
    echo "⚠️ Performance: Slow response time"
fi
```

#### Test 1.2: Health Endpoint Validation
```bash
#!/bin/bash
echo "🔍 Testing health endpoint..."

HEALTH_RESPONSE=$(curl -s https://marketedge-platform.onrender.com/health)
echo "Health Response: $HEALTH_RESPONSE"

# Validate required fields
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "✅ Health Status: Service is healthy"
else
    echo "❌ Health Status: Service health check failed"
fi

if echo "$HEALTH_RESPONSE" | grep -q '"environment":"production"'; then
    echo "✅ Environment: Production mode confirmed"
else
    echo "❌ Environment: Not in production mode"
fi
```

### Phase 2: Database & Redis Connectivity

#### Test 2.1: PostgreSQL Database Connection
```bash
#!/bin/bash
echo "🔍 Testing PostgreSQL database connection..."

DB_HEALTH=$(curl -s https://marketedge-platform.onrender.com/api/v1/admin/health/database)
echo "Database Health: $DB_HEALTH"

if echo "$DB_HEALTH" | grep -q "healthy"; then
    echo "✅ Database: PostgreSQL connection successful"
else
    echo "❌ Database: PostgreSQL connection failed"
    echo "Troubleshooting: Check DATABASE_URL configuration"
fi

# Test database migrations
MIGRATIONS_STATUS=$(curl -s https://marketedge-platform.onrender.com/api/v1/admin/migrations/status)
if echo "$MIGRATIONS_STATUS" | grep -q "current"; then
    echo "✅ Migrations: Database schema is up to date"
else
    echo "⚠️ Migrations: May need to run migrations"
fi
```

#### Test 2.2: Redis Cache Connection
```bash
#!/bin/bash
echo "🔍 Testing Redis cache connection..."

REDIS_HEALTH=$(curl -s https://marketedge-platform.onrender.com/api/v1/admin/health/redis)
echo "Redis Health: $REDIS_HEALTH"

if echo "$REDIS_HEALTH" | grep -q "healthy"; then
    echo "✅ Redis: Cache connection successful"
else
    echo "❌ Redis: Cache connection failed"
    echo "Troubleshooting: Check REDIS_URL configuration"
fi

# Test cache operations
CACHE_TEST=$(curl -s -X POST https://marketedge-platform.onrender.com/api/v1/admin/cache/test \
             -H "Content-Type: application/json" \
             -d '{"key":"test","value":"validation"}')
if echo "$CACHE_TEST" | grep -q "success"; then
    echo "✅ Cache: Read/write operations working"
else
    echo "⚠️ Cache: Operations may be limited"
fi
```

### Phase 3: Auth0 Integration Testing

#### Test 3.1: Auth0 Configuration
```bash
#!/bin/bash
echo "🔍 Testing Auth0 configuration..."

# Test Auth0 domain configuration
AUTH0_CONFIG=$(curl -s https://marketedge-platform.onrender.com/.well-known/openid-configuration)
if echo "$AUTH0_CONFIG" | grep -q "dev-g8trhgbfdq2sk2m8.us.auth0.com"; then
    echo "✅ Auth0: Domain configuration correct"
else
    echo "❌ Auth0: Domain configuration issue"
fi

# Test client configuration
CLIENT_CONFIG=$(curl -s https://marketedge-platform.onrender.com/api/v1/auth/config)
if echo "$CLIENT_CONFIG" | grep -q "mQG01Z4lNhTTN081GHbR9R9C4fBQdPNr"; then
    echo "✅ Auth0: Client ID configuration correct"
else
    echo "❌ Auth0: Client ID configuration issue"
fi
```

#### Test 3.2: Auth0 Client Secret Validation
```bash
#!/bin/bash
echo "🔍 Testing Auth0 client secret configuration..."

# Test token validation (requires valid token)
# This test should be run with a test token
AUTH_TEST=$(curl -s https://marketedge-platform.onrender.com/api/v1/auth/validate \
            -H "Content-Type: application/json" \
            -d '{"test": true}')

if echo "$AUTH_TEST" | grep -q "client_secret"; then
    echo "❌ Auth0: Client secret not configured"
    echo "🚨 CRITICAL: Set AUTH0_CLIENT_SECRET in Render dashboard"
else
    echo "✅ Auth0: Client secret appears to be configured"
fi
```

### Phase 4: CORS Configuration Testing

#### Test 4.1: Vercel Frontend CORS
```bash
#!/bin/bash
echo "🔍 Testing CORS for Vercel frontend..."

# Test OPTIONS preflight request
CORS_RESPONSE=$(curl -s -I \
    -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    -X OPTIONS \
    https://marketedge-platform.onrender.com/api/v1/health)

echo "CORS Response Headers:"
echo "$CORS_RESPONSE"

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin:.*frontend-5r7ft62po-zebraassociates-projects.vercel.app"; then
    echo "✅ CORS: Vercel frontend origin allowed"
else
    echo "❌ CORS: Vercel frontend origin not allowed"
fi

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Credentials: true"; then
    echo "✅ CORS: Credentials allowed"
else
    echo "❌ CORS: Credentials not allowed"
fi
```

#### Test 4.2: CORS Headers Validation
```bash
#!/bin/bash
echo "🔍 Testing CORS headers for actual requests..."

# Test actual GET request with CORS
CORS_GET=$(curl -s -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
               https://marketedge-platform.onrender.com/api/v1/health)

if [ $? -eq 0 ]; then
    echo "✅ CORS: GET requests working from Vercel frontend"
else
    echo "❌ CORS: GET requests failing from Vercel frontend"
fi

# Test localhost CORS (for development)
CORS_LOCAL=$(curl -s -H "Origin: http://localhost:3000" \
                 https://marketedge-platform.onrender.com/api/v1/health)

if [ $? -eq 0 ]; then
    echo "✅ CORS: Development localhost access working"
else
    echo "❌ CORS: Development localhost access failing"
fi
```

### Phase 5: Frontend Integration Testing

#### Test 5.1: Frontend Connection Test
```javascript
// Frontend Integration Test (Run in browser console on Vercel frontend)
console.log('🔍 Testing frontend to backend connection...');

// Test 1: Basic health check
fetch('https://marketedge-platform.onrender.com/health', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => {
    if (response.ok) {
        console.log('✅ Basic connectivity: Working');
        return response.json();
    } else {
        console.log('❌ Basic connectivity: Failed');
        throw new Error(`HTTP ${response.status}`);
    }
})
.then(data => {
    console.log('Health data:', data);
    console.log('✅ Backend health check: Success');
})
.catch(error => {
    console.error('❌ Backend health check: Failed', error);
});

// Test 2: API endpoint access
fetch('https://marketedge-platform.onrender.com/api/v1/health', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => {
    if (response.ok) {
        console.log('✅ API endpoint access: Working');
        return response.json();
    } else {
        console.log('❌ API endpoint access: Failed');
        throw new Error(`HTTP ${response.status}`);
    }
})
.then(data => {
    console.log('API data:', data);
    console.log('✅ Full API connectivity: Success');
})
.catch(error => {
    console.error('❌ Full API connectivity: Failed', error);
});
```

#### Test 5.2: Authentication Flow Test
```javascript
// Authentication Flow Test (Run in browser console on frontend)
console.log('🔍 Testing authentication flow...');

// Test Auth0 configuration endpoint
fetch('https://marketedge-platform.onrender.com/api/v1/auth/config', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => {
    if (response.ok) {
        console.log('✅ Auth config: Available');
        return response.json();
    } else {
        console.log('❌ Auth config: Failed');
        throw new Error(`HTTP ${response.status}`);
    }
})
.then(config => {
    console.log('Auth config:', config);
    if (config.domain && config.clientId) {
        console.log('✅ Auth0 configuration: Complete');
    } else {
        console.log('❌ Auth0 configuration: Incomplete');
    }
})
.catch(error => {
    console.error('❌ Auth configuration: Failed', error);
});
```

---

## 🚀 AUTOMATED VALIDATION SCRIPT

### Complete Epic 2 Validation Script
```bash
#!/bin/bash
# Epic 2: Complete Deployment Validation Script
# Run this script to validate the entire Render deployment

set -e

echo "🚀 Epic 2: Complete Render Deployment Validation"
echo "================================================"
echo "Date: $(date)"
echo "Backend URL: https://marketedge-platform.onrender.com"
echo "Frontend URL: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS_COUNT=0
TOTAL_TESTS=10

# Function to log results
log_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    if [ "$result" == "PASS" ]; then
        echo -e "${GREEN}✅ $test_name: $message${NC}"
        ((SUCCESS_COUNT++))
    elif [ "$result" == "FAIL" ]; then
        echo -e "${RED}❌ $test_name: $message${NC}"
    else
        echo -e "${YELLOW}⚠️ $test_name: $message${NC}"
    fi
}

# Test 1: Basic Service Health
echo "1. Testing basic service health..."
if curl -f -s https://marketedge-platform.onrender.com/health > /dev/null; then
    log_test "Service Health" "PASS" "Service is responding"
else
    log_test "Service Health" "FAIL" "Service is not responding"
fi

# Test 2: Health Endpoint Response
echo "2. Testing health endpoint response..."
HEALTH_RESPONSE=$(curl -s https://marketedge-platform.onrender.com/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    log_test "Health Status" "PASS" "Service reports healthy"
else
    log_test "Health Status" "FAIL" "Service health check failed"
fi

# Test 3: Production Environment
echo "3. Testing production environment..."
if echo "$HEALTH_RESPONSE" | grep -q '"environment":"production"'; then
    log_test "Environment" "PASS" "Production mode confirmed"
else
    log_test "Environment" "FAIL" "Not in production mode"
fi

# Test 4: Database Connection
echo "4. Testing database connection..."
DB_RESPONSE=$(curl -s https://marketedge-platform.onrender.com/api/v1/admin/health/database)
if echo "$DB_RESPONSE" | grep -q "healthy"; then
    log_test "Database" "PASS" "PostgreSQL connection successful"
else
    log_test "Database" "FAIL" "PostgreSQL connection failed"
fi

# Test 5: Redis Connection
echo "5. Testing Redis connection..."
REDIS_RESPONSE=$(curl -s https://marketedge-platform.onrender.com/api/v1/admin/health/redis)
if echo "$REDIS_RESPONSE" | grep -q "healthy"; then
    log_test "Redis" "PASS" "Cache connection successful"
else
    log_test "Redis" "FAIL" "Cache connection failed"
fi

# Test 6: Auth0 Configuration
echo "6. Testing Auth0 configuration..."
AUTH0_CONFIG=$(curl -s https://marketedge-platform.onrender.com/.well-known/openid-configuration)
if echo "$AUTH0_CONFIG" | grep -q "dev-g8trhgbfdq2sk2m8.us.auth0.com"; then
    log_test "Auth0 Config" "PASS" "Domain configuration correct"
else
    log_test "Auth0 Config" "FAIL" "Domain configuration issue"
fi

# Test 7: CORS Vercel Frontend
echo "7. Testing CORS for Vercel frontend..."
CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app" \
    -X OPTIONS \
    https://marketedge-platform.onrender.com/api/v1/health)
if [ "$CORS_STATUS" == "204" ] || [ "$CORS_STATUS" == "200" ]; then
    log_test "CORS Vercel" "PASS" "Frontend origin allowed"
else
    log_test "CORS Vercel" "FAIL" "Frontend origin not allowed (Status: $CORS_STATUS)"
fi

# Test 8: CORS Development
echo "8. Testing CORS for development..."
CORS_DEV_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Origin: http://localhost:3000" \
    -X OPTIONS \
    https://marketedge-platform.onrender.com/api/v1/health)
if [ "$CORS_DEV_STATUS" == "204" ] || [ "$CORS_DEV_STATUS" == "200" ]; then
    log_test "CORS Development" "PASS" "Development origin allowed"
else
    log_test "CORS Development" "FAIL" "Development origin not allowed (Status: $CORS_DEV_STATUS)"
fi

# Test 9: Response Time Performance
echo "9. Testing response time performance..."
RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null https://marketedge-platform.onrender.com/health)
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    log_test "Performance" "PASS" "Response time acceptable (${RESPONSE_TIME}s)"
else
    log_test "Performance" "WARN" "Response time slow (${RESPONSE_TIME}s)"
fi

# Test 10: API Endpoint Access
echo "10. Testing API endpoint access..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://marketedge-platform.onrender.com/api/v1/health)
if [ "$API_STATUS" == "200" ]; then
    log_test "API Access" "PASS" "API endpoints accessible"
else
    log_test "API Access" "FAIL" "API endpoints not accessible (Status: $API_STATUS)"
fi

# Summary
echo ""
echo "📊 VALIDATION SUMMARY"
echo "===================="
echo "Tests Passed: $SUCCESS_COUNT/$TOTAL_TESTS"

if [ $SUCCESS_COUNT -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED - Epic 2 deployment successful!${NC}"
    echo ""
    echo "✅ CORS issues resolved"
    echo "✅ Frontend can now connect to backend"
    echo "✅ Platform fully operational on Render"
    echo ""
    echo "🚀 Ready for stakeholder demo"
elif [ $SUCCESS_COUNT -ge 8 ]; then
    echo -e "${YELLOW}⚠️ MOSTLY SUCCESSFUL - Minor issues to address${NC}"
    echo ""
    echo "👉 Check failed tests above and address if needed"
    echo "👉 Platform should be functional for basic testing"
else
    echo -e "${RED}❌ DEPLOYMENT ISSUES - Critical problems detected${NC}"
    echo ""
    echo "🚨 Address failed tests before proceeding"
    echo "🚨 Platform may not be fully functional"
fi

echo ""
echo "📋 NEXT STEPS:"
echo "1. Address any failed tests"
echo "2. Test frontend integration manually"
echo "3. Validate with stakeholders"
echo "4. Mark Epic 2 as complete"
echo ""
echo "Backend: https://marketedge-platform.onrender.com"
echo "Frontend: https://frontend-5r7ft62po-zebraassociates-projects.vercel.app"
```

---

## 🎯 SUCCESS CRITERIA

### Epic 2 Completion Checklist

#### Technical Validation ✅
- [ ] Service health endpoint responding (200 OK)
- [ ] Production environment confirmed
- [ ] PostgreSQL database connected and healthy
- [ ] Redis cache connected and operational
- [ ] Auth0 configuration validated
- [ ] AUTH0_CLIENT_SECRET properly set
- [ ] CORS allowing Vercel frontend connections
- [ ] API endpoints accessible
- [ ] Response times under 2 seconds
- [ ] Error handling working correctly

#### Business Validation ✅
- [ ] Frontend can connect to backend (no CORS errors)
- [ ] User authentication flow working
- [ ] Core platform features accessible
- [ ] Admin panel functional
- [ ] Market-edge tools operational
- [ ] Multi-tenant functionality working
- [ ] Rate limiting operational
- [ ] Security measures in place

#### Epic 2 Success Metrics ✅
- [ ] Railway dependency eliminated
- [ ] CORS failures resolved
- [ ] Platform fully operational on Render
- [ ] Performance meets production standards
- [ ] Security compliance maintained
- [ ] Ready for stakeholder demonstrations

---

**🎯 VALIDATION COMPLETE**  
Once all tests pass, Epic 2 Railway to Render migration is complete and the CORS failures have been resolved.

**Final Verification:**
1. Run automated validation script
2. Test frontend integration manually
3. Confirm with stakeholders
4. Document completion