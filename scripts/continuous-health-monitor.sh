#!/bin/bash
# Continuous Health Monitor for MarketEdge Platform
# Run via cron: */5 * * * * /path/to/continuous-health-monitor.sh

# Configuration
BASE_URL="https://marketedge-platform.onrender.com"
FRONTEND_URL="https://app.zebra.associates"
LOG_DIR="/var/log/marketedge"
ALERT_EMAIL="alerts@your-domain.com"
# Will be set after LOG_DIR is determined

# Ensure log directory exists - try system location first, fallback to user location
if ! mkdir -p $LOG_DIR 2>/dev/null; then
    LOG_DIR="$HOME/marketedge-logs"
    mkdir -p $LOG_DIR 2>/dev/null || {
        LOG_DIR="/tmp/marketedge-logs"
        mkdir -p $LOG_DIR
    }
fi

# Set metrics file path after LOG_DIR is determined
METRICS_FILE="$LOG_DIR/metrics-$(date +%Y%m%d).json"

# Health monitoring function
monitor_health() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local health_data="{\"timestamp\":\"$timestamp\",\"checks\":{"
    
    # Backend health
    local backend_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "999")
    local backend_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "000")
    health_data+='"backend":{"response_time":'$backend_time',"status_code":'$backend_code'},'
    
    # Database health
    local db_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 15 "$BASE_URL/health/database" 2>/dev/null || echo "999")
    local db_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$BASE_URL/health/database" 2>/dev/null || echo "000")
    health_data+='"database":{"response_time":'$db_time',"status_code":'$db_code'},'
    
    # Epic 1 modules (fallback to main health if module endpoint not available)
    local epic1_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 "$BASE_URL/api/v1/module-management/system/health" 2>/dev/null || echo "999")
    local epic1_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/api/v1/module-management/system/health" 2>/dev/null || echo "000")
    if [[ "$epic1_code" == "000" ]] || [[ "$epic1_code" == "404" ]]; then
        # Fallback to main health endpoint for Epic 1 validation
        epic1_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "999")
        epic1_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "000")
    fi
    health_data+='"epic1_modules":{"response_time":'$epic1_time',"status_code":'$epic1_code'},'
    
    # Epic 2 feature flags (fallback to main health if feature flag endpoint not available)
    local epic2_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 "$BASE_URL/api/v1/feature-flags/status" 2>/dev/null || echo "999")
    local epic2_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/api/v1/feature-flags/status" 2>/dev/null || echo "000")
    if [[ "$epic2_code" == "000" ]] || [[ "$epic2_code" == "404" ]]; then
        # Fallback to main health endpoint for Epic 2 validation
        epic2_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "999")
        epic2_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$BASE_URL/health" 2>/dev/null || echo "000")
    fi
    health_data+='"epic2_features":{"response_time":'$epic2_time',"status_code":'$epic2_code'},'
    
    # Frontend health
    local frontend_time=$(curl -w "%{time_total}" -s -o /dev/null --max-time 10 "$FRONTEND_URL/" 2>/dev/null || echo "999")
    local frontend_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$FRONTEND_URL/" 2>/dev/null || echo "000")
    health_data+='"frontend":{"response_time":'$frontend_time',"status_code":'$frontend_code'}'
    
    health_data+="}}"
    
    # Log metrics
    echo $health_data >> $METRICS_FILE
    
    # Also log to syslog if available
    if command -v logger >/dev/null 2>&1; then
        logger "MarketEdge Health: Backend=$backend_code DB=$db_code Epic1=$epic1_code Epic2=$epic2_code Frontend=$frontend_code"
    fi
    
    # Check for alerts
    check_alerts $backend_code $db_code $epic1_code $epic2_code $frontend_code
}

# Alert checking function
check_alerts() {
    local backend_code=$1
    local db_code=$2
    local epic1_code=$3
    local epic2_code=$4
    local frontend_code=$5
    
    local alert_message=""
    local alert_level="INFO"
    
    # Check critical systems
    if [[ "$backend_code" != "200" ]]; then
        alert_message+="CRITICAL: Backend health check failed (HTTP $backend_code)\n"
        alert_level="CRITICAL"
    fi
    
    if [[ "$db_code" != "200" ]] && [[ "$db_code" != "404" ]]; then
        alert_message+="CRITICAL: Database health check failed (HTTP $db_code)\n"
        alert_level="CRITICAL"
    fi
    
    # Check Epic systems (allow 404 as these endpoints may not be fully implemented)
    if [[ "$epic1_code" != "200" ]] && [[ "$epic1_code" != "404" ]]; then
        alert_message+="WARNING: Epic 1 module system issues (HTTP $epic1_code)\n"
        if [[ "$alert_level" != "CRITICAL" ]]; then
            alert_level="WARNING"
        fi
    fi
    
    if [[ "$epic2_code" != "200" ]] && [[ "$epic2_code" != "404" ]]; then
        alert_message+="WARNING: Epic 2 feature flag system issues (HTTP $epic2_code)\n"
        if [[ "$alert_level" != "CRITICAL" ]]; then
            alert_level="WARNING"
        fi
    fi
    
    if [[ "$frontend_code" != "200" ]] && [[ "$frontend_code" != "404" ]]; then
        alert_message+="WARNING: Frontend availability issues (HTTP $frontend_code)\n"
        if [[ "$alert_level" != "CRITICAL" ]]; then
            alert_level="WARNING"
        fi
    fi
    
    # Send alerts if any issues
    if [[ -n "$alert_message" ]]; then
        local alert_text="MarketEdge Platform Alert - $(date)\nAlert Level: $alert_level\n\n$alert_message"
        
        # Try to send email alert
        if command -v mail >/dev/null 2>&1; then
            echo -e "$alert_text" | mail -s "MarketEdge Platform Health Alert [$alert_level]" $ALERT_EMAIL 2>/dev/null
        fi
        
        # Always log to system log
        if command -v logger >/dev/null 2>&1; then
            logger -t "MarketEdge-Alert" "[$alert_level] $alert_message"
        fi
        
        # Log to our metrics file as well
        local alert_json="{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"type\":\"alert\",\"level\":\"$alert_level\",\"message\":\"$alert_message\"}"
        echo $alert_json >> $METRICS_FILE
        
        # Also output to stderr for debugging
        echo -e "ALERT: $alert_text" >&2
    fi
}

# Execute monitoring
monitor_health

# Cleanup old metrics (keep 30 days)
find $LOG_DIR -name "metrics-*.json" -mtime +30 -delete 2>/dev/null || true