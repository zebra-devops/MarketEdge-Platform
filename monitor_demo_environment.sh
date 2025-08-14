#!/bin/bash
# Demo Environment Continuous Monitoring
# QA Orchestrator: Quincy
# Purpose: Monitor Railway production environment until demo completion
# Business Critical: Ensure zero downtime during client presentation

RAILWAY_BASE="https://platform-wrapper-backend-production.up.railway.app"
LOG_FILE="demo_monitoring_$(date +%Y%m%d_%H%M).log"
ALERT_FILE="demo_alerts_$(date +%Y%m%d).log"

# Demo date configuration (August 17, 2025)
DEMO_DATE="2025-08-17"
DEMO_TIME="10:00"

echo "=== DEMO ENVIRONMENT MONITORING STARTED: $(date) ===" >> $LOG_FILE
echo "Demo Target: $DEMO_DATE $DEMO_TIME" >> $LOG_FILE
echo "Monitoring URL: $RAILWAY_BASE" >> $LOG_FILE
echo "=========================================" >> $LOG_FILE

# Function to calculate hours until demo
calculate_demo_countdown() {
    demo_timestamp=$(date -d "$DEMO_DATE $DEMO_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M" "$DEMO_DATE $DEMO_TIME" +%s)
    current_timestamp=$(date +%s)
    hours_left=$(( (demo_timestamp - current_timestamp) / 3600 ))
    echo $hours_left
}

# Function to send critical alerts
send_critical_alert() {
    local message="$1"
    echo "🚨 CRITICAL ALERT: $message" >> $ALERT_FILE
    echo "🚨 CRITICAL ALERT: $message" >> $LOG_FILE
    echo "Time: $(date)" >> $ALERT_FILE
    echo "Hours to Demo: $(calculate_demo_countdown)" >> $ALERT_FILE
    echo "Action Required: IMMEDIATE INTERVENTION" >> $ALERT_FILE
    echo "=========================================" >> $ALERT_FILE
}

# Function to test endpoint with detailed response
test_endpoint_detailed() {
    local url="$1"
    local description="$2"
    local max_response_time="$3"
    
    # Test with timeout and detailed metrics
    response_data=$(curl -s -o /tmp/endpoint_response.json -w "%{http_code}|%{time_total}|%{time_connect}" --max-time 10 "$url" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        send_critical_alert "$description FAILED - Connection timeout or error"
        echo "❌ $description: CONNECTION FAILED" >> $LOG_FILE
        return 1
    fi
    
    IFS='|' read -r status_code response_time connect_time <<< "$response_data"
    
    # Validate status code
    if [ "$status_code" != "200" ]; then
        send_critical_alert "$description returned HTTP $status_code (Expected 200)"
        echo "❌ $description: HTTP $status_code (Expected 200)" >> $LOG_FILE
        return 1
    fi
    
    # Validate response time (convert to milliseconds for easier comparison)
    response_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null || echo "999")
    max_ms=$(echo "$max_response_time * 1000" | bc -l 2>/dev/null || echo "200")
    
    if (( $(echo "$response_ms > $max_ms" | bc -l 2>/dev/null || echo "0") )); then
        echo "⚠️  WARNING: $description slow response - ${response_time}s (Max: ${max_response_time}s)" >> $LOG_FILE
    else
        echo "✅ $description: HTTP $status_code (${response_time}s)" >> $LOG_FILE
    fi
    
    return 0
}

# Function to validate API response content
validate_api_content() {
    local url="$1"
    local description="$2"
    
    response_content=$(curl -s "$url" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        send_critical_alert "$description - Cannot retrieve response content"
        return 1
    fi
    
    # Check if response is valid JSON
    if echo "$response_content" | jq . >/dev/null 2>&1; then
        echo "✅ $description: Valid JSON response" >> $LOG_FILE
        
        # For Market Edge endpoints, validate business-critical content
        if [[ "$url" == *"market-edge"* ]]; then
            if echo "$response_content" | grep -q "mock\|placeholder\|todo\|fixme"; then
                echo "⚠️  WARNING: $description contains mock/placeholder data" >> $LOG_FILE
            else
                echo "✅ $description: Production-ready content" >> $LOG_FILE
            fi
        fi
    else
        echo "❌ $description: Invalid JSON response" >> $LOG_FILE
        echo "Response content: $response_content" >> $LOG_FILE
    fi
}

# Main monitoring loop
monitoring_cycle=0

while true; do
    monitoring_cycle=$((monitoring_cycle + 1))
    hours_to_demo=$(calculate_demo_countdown)
    
    echo "" >> $LOG_FILE
    echo "--- MONITORING CYCLE #$monitoring_cycle: $(date) ---" >> $LOG_FILE
    echo "Hours until demo: $hours_to_demo" >> $LOG_FILE
    
    # If demo has passed, stop monitoring
    if [ $hours_to_demo -lt 0 ]; then
        echo "🎉 Demo completed! Stopping monitoring." >> $LOG_FILE
        break
    fi
    
    # Increase monitoring frequency as demo approaches
    if [ $hours_to_demo -le 4 ]; then
        sleep_interval=300  # 5 minutes when demo is within 4 hours
    elif [ $hours_to_demo -le 12 ]; then
        sleep_interval=600  # 10 minutes when demo is within 12 hours  
    else
        sleep_interval=900  # 15 minutes for normal monitoring
    fi
    
    # Test critical endpoints
    echo "Testing critical endpoints..." >> $LOG_FILE
    
    # Health endpoints (most critical)
    test_endpoint_detailed "$RAILWAY_BASE/health" "Health Endpoint" 0.1
    test_endpoint_detailed "$RAILWAY_BASE/api/v1/health" "API Health Endpoint" 0.1
    
    # API Documentation (client technical evaluation)
    test_endpoint_detailed "$RAILWAY_BASE/docs" "API Documentation" 1.0
    
    # Market Edge endpoints (demo critical)
    test_endpoint_detailed "$RAILWAY_BASE/api/v1/market-edge/health" "Market Edge Health" 0.1
    test_endpoint_detailed "$RAILWAY_BASE/api/v1/market-edge/competitors" "Competitors API" 0.2
    test_endpoint_detailed "$RAILWAY_BASE/api/v1/market-edge/pricing-analysis" "Pricing Analysis API" 0.2
    test_endpoint_detailed "$RAILWAY_BASE/api/v1/market-edge/market-intelligence" "Market Intelligence API" 0.3
    
    # Validate API response content quality
    echo "Validating API response content..." >> $LOG_FILE
    validate_api_content "$RAILWAY_BASE/api/v1/market-edge/competitors" "Competitors Content"
    validate_api_content "$RAILWAY_BASE/api/v1/market-edge/pricing-analysis" "Pricing Analysis Content"
    
    # Generate status summary for this cycle
    echo "--- CYCLE SUMMARY ---" >> $LOG_FILE
    echo "Monitoring cycle: #$monitoring_cycle" >> $LOG_FILE
    echo "Hours to demo: $hours_to_demo" >> $LOG_FILE
    echo "Next check in: $sleep_interval seconds" >> $LOG_FILE
    echo "Status: $([ -f $ALERT_FILE ] && echo "🚨 ALERTS ACTIVE - CHECK $ALERT_FILE" || echo "✅ All systems operational")" >> $LOG_FILE
    
    # If within 24 hours of demo, provide detailed status
    if [ $hours_to_demo -le 24 ]; then
        echo "" >> $LOG_FILE
        echo "🎯 DEMO READINESS STATUS (T-${hours_to_demo}h):" >> $LOG_FILE
        echo "Production Environment: $(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_BASE/health" | grep -q "200" && echo "✅ Online" || echo "❌ Offline")" >> $LOG_FILE
        echo "API Documentation: $(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_BASE/docs" | grep -q "200" && echo "✅ Accessible" || echo "❌ Failed")" >> $LOG_FILE
        echo "Market Edge APIs: $(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_BASE/api/v1/market-edge/health" | grep -q "200" && echo "✅ Functional" || echo "❌ Failed")" >> $LOG_FILE
        echo "" >> $LOG_FILE
    fi
    
    # Sleep until next monitoring cycle
    sleep $sleep_interval
done

echo "=== DEMO ENVIRONMENT MONITORING COMPLETED: $(date) ===" >> $LOG_FILE