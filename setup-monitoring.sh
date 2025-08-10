#!/bin/bash

# Railway Production Monitoring Setup Script
# Configures monitoring, alerting, and health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get service information
log_info "Getting Railway service information..."
SERVICE_URL=$(railway url 2>/dev/null || echo "")
PROJECT_ID=$(railway status 2>/dev/null | grep "Project" | awk '{print $2}' || echo "")

if [ -z "$SERVICE_URL" ]; then
    log_error "Could not get service URL. Make sure the service is deployed."
    exit 1
fi

log_success "Service URL: $SERVICE_URL"

# Test health endpoints
log_info "Testing health endpoints..."

# Test health endpoint
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    log_success "Health endpoint is working"
    HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health")
    echo "Health response: $HEALTH_RESPONSE"
else
    log_error "Health endpoint is not responding"
fi

# Test readiness endpoint
if curl -f -s "$SERVICE_URL/ready" > /dev/null; then
    log_success "Readiness endpoint is working"
    READY_RESPONSE=$(curl -s "$SERVICE_URL/ready")
    echo "Readiness response: $READY_RESPONSE"
else
    log_warning "Readiness endpoint is not responding (may be expected if not yet implemented)"
fi

# Test API documentation (if in debug mode)
if curl -f -s "$SERVICE_URL/api/v1/docs" > /dev/null; then
    log_success "API documentation is accessible: $SERVICE_URL/api/v1/docs"
else
    log_info "API documentation is not accessible (expected in production)"
fi

# Create monitoring script
log_info "Creating local monitoring script..."

cat > monitor-service.sh << 'EOF'
#!/bin/bash

# Local monitoring script for Railway service
# Run this script periodically to check service health

SERVICE_URL="$1"
if [ -z "$SERVICE_URL" ]; then
    echo "Usage: $0 <service_url>"
    exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Health check
HEALTH_STATUS=$(curl -f -s "$SERVICE_URL/health" || echo "FAILED")
if [[ "$HEALTH_STATUS" == "FAILED" ]]; then
    echo "[$TIMESTAMP] ALERT: Health check failed"
    exit 1
else
    echo "[$TIMESTAMP] Health check passed"
fi

# Check response time
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$SERVICE_URL/health")
echo "[$TIMESTAMP] Response time: ${RESPONSE_TIME}s"

# Check if response time is too high (>2 seconds)
if (( $(echo "$RESPONSE_TIME > 2.0" | bc -l) )); then
    echo "[$TIMESTAMP] WARNING: Response time is high (${RESPONSE_TIME}s)"
fi

# Check memory and CPU usage via Railway logs (if available)
echo "[$TIMESTAMP] Monitoring check completed"
EOF

chmod +x monitor-service.sh

log_success "Created monitor-service.sh"
echo "Usage: ./monitor-service.sh $SERVICE_URL"

# Create performance test script
log_info "Creating performance test script..."

cat > performance-test.sh << 'EOF'
#!/bin/bash

# Performance test script for Railway service
# Tests load and response times

SERVICE_URL="$1"
if [ -z "$SERVICE_URL" ]; then
    echo "Usage: $0 <service_url>"
    exit 1
fi

echo "Starting performance test for: $SERVICE_URL"
echo "Test started at: $(date)"

# Test 1: Basic load test (10 concurrent requests)
echo "Test 1: Basic load test (10 concurrent for 30 seconds)..."
ab -n 300 -c 10 -g results.tsv "$SERVICE_URL/health" > load_test_results.txt

echo "Test 1 completed. Results saved to load_test_results.txt"

# Test 2: Response time test
echo "Test 2: Response time test (100 sequential requests)..."
for i in {1..100}; do
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$SERVICE_URL/health")
    echo "$i,$RESPONSE_TIME" >> response_times.csv
done

echo "Test 2 completed. Results saved to response_times.csv"

# Calculate average response time
AVG_TIME=$(awk -F',' '{sum+=$2; count++} END {print sum/count}' response_times.csv)
echo "Average response time: ${AVG_TIME}s"

# Test 3: Rate limiting test
echo "Test 3: Rate limiting test..."
echo "Sending 100 requests rapidly to test rate limiting..."

for i in {1..100}; do
    HTTP_CODE=$(curl -o /dev/null -s -w '%{http_code}' "$SERVICE_URL/health")
    echo "$i,$HTTP_CODE" >> rate_limit_test.csv
    if [ "$HTTP_CODE" = "429" ]; then
        echo "Rate limiting activated at request $i"
        break
    fi
done

echo "Test 3 completed. Results saved to rate_limit_test.csv"

echo "Performance testing completed at: $(date)"
echo "Files generated:"
echo "- load_test_results.txt"
echo "- response_times.csv"
echo "- rate_limit_test.csv"
EOF

chmod +x performance-test.sh

log_success "Created performance-test.sh"
echo "Usage: ./performance-test.sh $SERVICE_URL"

# Create database monitoring script
log_info "Creating database monitoring script..."

cat > monitor-database.sh << 'EOF'
#!/bin/bash

# Database monitoring script
# Requires Railway CLI to be authenticated

echo "Database Monitoring Report - $(date)"
echo "=================================="

# Connect to database and run monitoring queries
railway shell << 'DBEOF'
python3 << 'PYEOF'
import os
import asyncio
import asyncpg

async def monitor_database():
    try:
        # Get database URL from environment
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("ERROR: DATABASE_URL not found")
            return
        
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Check active connections
        active_connections = await conn.fetchval(
            "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
        )
        print(f"Active connections: {active_connections}")
        
        # Check database size
        db_size = await conn.fetchval(
            "SELECT pg_size_pretty(pg_database_size(current_database()))"
        )
        print(f"Database size: {db_size}")
        
        # Check table sizes
        table_sizes = await conn.fetch("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """)
        
        print("\nTop 10 largest tables:")
        for row in table_sizes:
            print(f"  {row['tablename']}: {row['size']}")
        
        # Check for slow queries (if pg_stat_statements is available)
        try:
            slow_queries = await conn.fetch("""
                SELECT query, calls, mean_time, total_time
                FROM pg_stat_statements 
                ORDER BY mean_time DESC 
                LIMIT 5
            """)
            
            print("\nTop 5 slowest queries:")
            for row in slow_queries:
                print(f"  Calls: {row['calls']}, Mean: {row['mean_time']:.2f}ms")
                print(f"  Query: {row['query'][:100]}...")
        except:
            print("\nNote: pg_stat_statements extension not available")
        
        await conn.close()
        print("\nDatabase monitoring completed successfully")
        
    except Exception as e:
        print(f"Database monitoring error: {e}")

asyncio.run(monitor_database())
PYEOF
DBEOF
EOF

chmod +x monitor-database.sh

log_success "Created monitor-database.sh"

# Create comprehensive status check script
log_info "Creating comprehensive status check script..."

cat > status-check.sh << 'EOF'
#!/bin/bash

# Comprehensive status check for Railway deployment

SERVICE_URL="$1"
if [ -z "$SERVICE_URL" ]; then
    SERVICE_URL=$(railway url 2>/dev/null || echo "")
fi

if [ -z "$SERVICE_URL" ]; then
    echo "ERROR: Could not determine service URL"
    echo "Usage: $0 <service_url>"
    exit 1
fi

echo "Comprehensive Status Check"
echo "========================="
echo "Service URL: $SERVICE_URL"
echo "Timestamp: $(date)"
echo ""

# 1. Basic connectivity
echo "1. Basic Connectivity Test:"
if curl -f -s "$SERVICE_URL/health" > /dev/null; then
    echo "   ✅ Service is reachable"
else
    echo "   ❌ Service is not reachable"
fi

# 2. Health endpoint detailed check
echo ""
echo "2. Health Endpoint Details:"
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health" 2>/dev/null || echo "FAILED")
if [[ "$HEALTH_RESPONSE" != "FAILED" ]]; then
    echo "   ✅ Health endpoint responding"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ❌ Health endpoint not responding"
fi

# 3. Response time check
echo ""
echo "3. Response Time Test:"
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$SERVICE_URL/health" 2>/dev/null || echo "FAILED")
if [[ "$RESPONSE_TIME" != "FAILED" ]]; then
    echo "   ⏱️  Response time: ${RESPONSE_TIME}s"
    if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l 2>/dev/null || echo "0") )); then
        echo "   ✅ Response time is good"
    else
        echo "   ⚠️  Response time is slow"
    fi
else
    echo "   ❌ Could not measure response time"
fi

# 4. Railway service status
echo ""
echo "4. Railway Service Status:"
RAILWAY_STATUS=$(railway status 2>/dev/null || echo "FAILED")
if [[ "$RAILWAY_STATUS" != "FAILED" ]]; then
    echo "   ✅ Railway CLI connected"
    echo "$RAILWAY_STATUS" | head -5
else
    echo "   ❌ Railway CLI not available"
fi

# 5. Environment check
echo ""
echo "5. Environment Configuration:"
railway variables list 2>/dev/null | head -10 || echo "   ❌ Could not retrieve environment variables"

# 6. Recent logs check
echo ""
echo "6. Recent Logs (last 10 lines):"
railway logs --lines 10 2>/dev/null || echo "   ❌ Could not retrieve logs"

echo ""
echo "Status check completed at $(date)"
EOF

chmod +x status-check.sh

log_success "Created status-check.sh"
echo "Usage: ./status-check.sh [$SERVICE_URL]"

# Create alerting configuration
log_info "Creating alerting configuration..."

cat > setup-alerts.md << 'EOF'
# Railway Alerting Setup Guide

## Built-in Railway Monitoring

Railway provides built-in monitoring and alerting. Configure these in your Railway dashboard:

### 1. Service Monitoring
- Go to your project dashboard
- Click on your backend service
- Navigate to "Metrics" tab
- Set up alerts for:
  - CPU usage > 80%
  - Memory usage > 80%
  - Response time > 2000ms
  - Error rate > 5%

### 2. Health Check Monitoring
Railway automatically monitors your health check endpoint at `/health`

### 3. Custom Alerts (via external services)

#### Uptime Robot Setup
1. Create account at uptimerobot.com
2. Add HTTP(s) monitor for your service URL + /health
3. Set check interval to 5 minutes
4. Configure email/SMS alerts for downtime

#### Example configuration:
- Monitor URL: https://your-service.railway.app/health
- Monitor Type: HTTP(s)
- Check Interval: 5 minutes
- Alert When: Down for 2 consecutive checks

#### Pingdom Setup
1. Create account at pingdom.com
2. Add uptime check for /health endpoint
3. Configure notification preferences

### 4. Log Monitoring
Use Railway logs with external services:

```bash
# Stream logs to external service
railway logs --follow | your-log-processor
```

### 5. Performance Monitoring
Set up performance monitoring:

```bash
# Regular performance checks
echo "0 */6 * * * /path/to/performance-test.sh" | crontab -
```

### 6. Database Monitoring
Regular database health checks:

```bash
# Daily database monitoring
echo "0 9 * * * /path/to/monitor-database.sh" | crontab -
```
EOF

log_success "Created setup-alerts.md"

# Summary
echo ""
log_success "Monitoring setup completed!"
echo ""
echo "Created files:"
echo "- monitor-service.sh        - Basic service monitoring"
echo "- performance-test.sh       - Load and performance testing"
echo "- monitor-database.sh       - Database monitoring"
echo "- status-check.sh          - Comprehensive status check"
echo "- setup-alerts.md          - Alerting configuration guide"
echo ""
echo "Quick tests:"
echo "1. Run health check:        ./status-check.sh"
echo "2. Monitor service:         ./monitor-service.sh $SERVICE_URL"
echo "3. Performance test:        ./performance-test.sh $SERVICE_URL"
echo "4. Database monitoring:     ./monitor-database.sh"
echo ""
log_info "Set up external monitoring services as described in setup-alerts.md"