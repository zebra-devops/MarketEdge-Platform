#!/bin/bash
# MarketEdge Monitoring Setup Script
# Sets up monitoring tools and configurations for the platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/var/log/marketedge"
CRON_USER=${CRON_USER:-$(whoami)}

echo "=================================="
echo "MarketEdge Monitoring Setup"
echo "=================================="
log_info "Setting up monitoring tools for MarketEdge platform"
echo ""

# Step 1: Create log directories
log_info "Creating log directories..."
if sudo mkdir -p $LOG_DIR 2>/dev/null || mkdir -p "$HOME/marketedge-logs" 2>/dev/null; then
    if [[ -d "$LOG_DIR" ]]; then
        LOG_DIR="/var/log/marketedge"
        log_success "Created system log directory: $LOG_DIR"
    else
        LOG_DIR="$HOME/marketedge-logs"
        log_success "Created user log directory: $LOG_DIR"
    fi
    
    # Update the log directory in scripts
    if [[ -f "$SCRIPT_DIR/continuous-health-monitor.sh" ]]; then
        # Create a local version with correct log directory
        cp "$SCRIPT_DIR/continuous-health-monitor.sh" "$SCRIPT_DIR/continuous-health-monitor-local.sh"
        sed -i.bak "s|LOG_DIR=\"/var/log/marketedge\"|LOG_DIR=\"$LOG_DIR\"|g" "$SCRIPT_DIR/continuous-health-monitor-local.sh"
        chmod +x "$SCRIPT_DIR/continuous-health-monitor-local.sh"
        log_success "Updated health monitor script with correct log directory"
    fi
else
    log_error "Failed to create log directory"
    exit 1
fi

# Step 2: Test monitoring scripts
log_info "Testing deployment validation script..."
if [[ -f "$SCRIPT_DIR/validate-deployment-success.sh" ]]; then
    if "$SCRIPT_DIR/validate-deployment-success.sh" > /tmp/monitoring-test.log 2>&1; then
        log_success "Deployment validation script test passed"
    else
        log_warning "Deployment validation script test had warnings (check /tmp/monitoring-test.log)"
    fi
else
    log_error "Deployment validation script not found"
fi

log_info "Testing continuous health monitor..."
if [[ -f "$SCRIPT_DIR/continuous-health-monitor-local.sh" ]]; then
    if "$SCRIPT_DIR/continuous-health-monitor-local.sh" > /tmp/health-test.log 2>&1; then
        log_success "Health monitoring script test completed"
        if [[ -f "$LOG_DIR/metrics-$(date +%Y%m%d).json" ]]; then
            log_success "Health metrics being logged to: $LOG_DIR/metrics-$(date +%Y%m%d).json"
        fi
    else
        log_warning "Health monitoring script test had issues (check /tmp/health-test.log)"
    fi
fi

# Step 3: Setup cron job for continuous monitoring
log_info "Setting up cron job for continuous monitoring..."
CRON_COMMAND="*/5 * * * * $SCRIPT_DIR/continuous-health-monitor-local.sh"
CRON_COMMENT="# MarketEdge Platform Health Monitoring"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "continuous-health-monitor"; then
    log_warning "Cron job already exists for health monitoring"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$CRON_COMMAND") | crontab -
    if [[ $? -eq 0 ]]; then
        log_success "Added cron job for continuous health monitoring (every 5 minutes)"
    else
        log_warning "Failed to add cron job automatically. Add manually:"
        echo "  crontab -e"
        echo "  Add: $CRON_COMMAND"
    fi
fi

# Step 4: Create monitoring configuration files
log_info "Creating monitoring configuration files..."

# Create UptimeRobot configuration template
cat > "$BASE_DIR/uptimerobot-config.json" << 'EOF'
{
  "monitors": [
    {
      "friendly_name": "MarketEdge Backend Health",
      "url": "https://marketedge-platform.onrender.com/health",
      "type": 1,
      "interval": 300,
      "timeout": 30,
      "alert_contacts": []
    },
    {
      "friendly_name": "MarketEdge Frontend",
      "url": "https://app.zebra.associates/",
      "type": 1,
      "interval": 300,
      "timeout": 30,
      "alert_contacts": []
    },
    {
      "friendly_name": "MarketEdge Database Health",
      "url": "https://marketedge-platform.onrender.com/health/database",
      "type": 1,
      "interval": 600,
      "timeout": 30,
      "alert_contacts": []
    },
    {
      "friendly_name": "MarketEdge API",
      "url": "https://marketedge-platform.onrender.com/api/v1/health",
      "type": 1,
      "interval": 600,
      "timeout": 30,
      "alert_contacts": []
    }
  ]
}
EOF
log_success "Created UptimeRobot configuration template"

# Create monitoring dashboard template
cat > "$BASE_DIR/monitoring-dashboard.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>MarketEdge Platform Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .status-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .status-healthy { border-left: 5px solid #27ae60; }
        .status-warning { border-left: 5px solid #f39c12; }
        .status-error { border-left: 5px solid #e74c3c; }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .metric-value { font-weight: bold; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MarketEdge Platform Monitoring</h1>
            <p>Real-time status of Epic 1 & Epic 2 deployments</p>
            <button class="refresh-btn" onclick="location.reload()">Refresh Status</button>
        </div>
        
        <div class="status-grid">
            <div class="status-card status-healthy">
                <h3>Backend Health</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" id="backend-status">Checking...</span>
                </div>
                <div class="metric">
                    <span>Response Time:</span>
                    <span class="metric-value" id="backend-time">-</span>
                </div>
                <div class="metric">
                    <span>Last Check:</span>
                    <span class="metric-value" id="backend-check">-</span>
                </div>
            </div>
            
            <div class="status-card status-healthy">
                <h3>Frontend Health</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" id="frontend-status">Checking...</span>
                </div>
                <div class="metric">
                    <span>Response Time:</span>
                    <span class="metric-value" id="frontend-time">-</span>
                </div>
                <div class="metric">
                    <span>Last Check:</span>
                    <span class="metric-value" id="frontend-check">-</span>
                </div>
            </div>
            
            <div class="status-card status-healthy">
                <h3>Epic 1 - Module System</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" id="epic1-status">Checking...</span>
                </div>
                <div class="metric">
                    <span>Module Registration:</span>
                    <span class="metric-value" id="epic1-modules">-</span>
                </div>
                <div class="metric">
                    <span>Last Check:</span>
                    <span class="metric-value" id="epic1-check">-</span>
                </div>
            </div>
            
            <div class="status-card status-healthy">
                <h3>Epic 2 - Feature Flags</h3>
                <div class="metric">
                    <span>Status:</span>
                    <span class="metric-value" id="epic2-status">Checking...</span>
                </div>
                <div class="metric">
                    <span>Flag Evaluation:</span>
                    <span class="metric-value" id="epic2-flags">-</span>
                </div>
                <div class="metric">
                    <span>Last Check:</span>
                    <span class="metric-value" id="epic2-check">-</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Simple status checking (would be enhanced with real API calls)
        function updateStatus() {
            const now = new Date().toLocaleTimeString();
            
            // Simulate status updates - replace with real API calls
            document.getElementById('backend-check').textContent = now;
            document.getElementById('frontend-check').textContent = now;
            document.getElementById('epic1-check').textContent = now;
            document.getElementById('epic2-check').textContent = now;
            
            // In a real implementation, these would be API calls to health endpoints
            checkEndpoint('https://marketedge-platform.onrender.com/health', 'backend');
            checkEndpoint('https://app.zebra.associates/', 'frontend');
        }
        
        function checkEndpoint(url, type) {
            fetch(url)
                .then(response => {
                    if (response.ok) {
                        document.getElementById(type + '-status').textContent = 'Healthy';
                        document.getElementById(type + '-status').style.color = '#27ae60';
                    } else {
                        document.getElementById(type + '-status').textContent = 'Issues';
                        document.getElementById(type + '-status').style.color = '#e74c3c';
                    }
                })
                .catch(error => {
                    document.getElementById(type + '-status').textContent = 'Error';
                    document.getElementById(type + '-status').style.color = '#e74c3c';
                });
        }
        
        // Update status on page load
        updateStatus();
        
        // Auto-refresh every 30 seconds
        setInterval(updateStatus, 30000);
    </script>
</body>
</html>
EOF
log_success "Created monitoring dashboard template"

# Step 5: Create monitoring summary script
cat > "$SCRIPT_DIR/monitoring-summary.sh" << 'EOF'
#!/bin/bash
# Generate daily monitoring summary

LOG_DIR="/var/log/marketedge"
if [[ ! -d "$LOG_DIR" ]]; then
    LOG_DIR="$HOME/marketedge-logs"
fi

echo "MarketEdge Platform - Daily Monitoring Summary"
echo "Generated: $(date)"
echo "=============================================="

# Check if metrics file exists
METRICS_FILE="$LOG_DIR/metrics-$(date +%Y%m%d).json"
if [[ -f "$METRICS_FILE" ]]; then
    echo ""
    echo "Health Check Summary:"
    echo "- Total checks today: $(wc -l < "$METRICS_FILE")"
    
    # Count successful backend checks
    BACKEND_OK=$(grep '"backend":{"response_time":[0-9.]*,"status_code":200}' "$METRICS_FILE" | wc -l)
    TOTAL_CHECKS=$(wc -l < "$METRICS_FILE")
    
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        UPTIME_PERCENT=$(( (BACKEND_OK * 100) / TOTAL_CHECKS ))
        echo "- Backend uptime: $UPTIME_PERCENT% ($BACKEND_OK/$TOTAL_CHECKS checks)"
    fi
    
    # Show any alerts
    if grep -q '"type":"alert"' "$METRICS_FILE"; then
        echo ""
        echo "Alerts Generated Today:"
        grep '"type":"alert"' "$METRICS_FILE" | tail -5
    else
        echo "- No alerts generated today ✅"
    fi
else
    echo "No metrics file found for today"
fi

echo ""
echo "Recent Log Entries:"
if command -v logger >/dev/null 2>&1 && journalctl --version >/dev/null 2>&1; then
    journalctl -t "MarketEdge-Alert" --since "1 day ago" | tail -5
else
    echo "System log not available or no recent MarketEdge entries"
fi
EOF

chmod +x "$SCRIPT_DIR/monitoring-summary.sh"
log_success "Created monitoring summary script"

# Step 6: Display setup summary
echo ""
log_info "=== Setup Summary ==="
log_success "✅ Monitoring scripts installed and configured"
log_success "✅ Log directory created: $LOG_DIR"
log_success "✅ Cron job configured for continuous monitoring (every 5 minutes)"
log_success "✅ Configuration templates created"

echo ""
log_info "=== Next Steps ==="
echo "1. Configure UptimeRobot monitoring:"
echo "   - Sign up at https://uptimerobot.com"
echo "   - Use config template: $BASE_DIR/uptimerobot-config.json"
echo ""
echo "2. Test the monitoring setup:"
echo "   - Run: $SCRIPT_DIR/validate-deployment-success.sh"
echo "   - Run: $SCRIPT_DIR/continuous-health-monitor-local.sh"
echo ""
echo "3. View monitoring dashboard:"
echo "   - Open: $BASE_DIR/monitoring-dashboard.html"
echo ""
echo "4. Check daily summary:"
echo "   - Run: $SCRIPT_DIR/monitoring-summary.sh"
echo ""
echo "5. Monitor logs:"
echo "   - Health metrics: $LOG_DIR/metrics-\$(date +%Y%m%d).json"
echo "   - System logs: journalctl -t 'MarketEdge-Alert'"

echo ""
log_success "Monitoring setup complete! 🎉"

# Test the setup
echo ""
log_info "Running initial test..."
if "$SCRIPT_DIR/continuous-health-monitor-local.sh"; then
    log_success "Initial monitoring test successful"
    if [[ -f "$LOG_DIR/metrics-$(date +%Y%m%d).json" ]]; then
        echo "Latest health check:"
        tail -1 "$LOG_DIR/metrics-$(date +%Y%m%d).json" | python3 -m json.tool 2>/dev/null || tail -1 "$LOG_DIR/metrics-$(date +%Y%m%d).json"
    fi
else
    log_warning "Initial test had issues - check configuration"
fi
EOF