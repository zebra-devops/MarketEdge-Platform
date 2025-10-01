#!/bin/bash
# Enable CSRF Protection After Smoke Test
#
# Usage: ./scripts/deployment/csrf-enable.sh [env-file]
#
# This script:
# 1. Updates .env to set CSRF_ENABLED=True
# 2. Restarts the backend service
# 3. Monitors logs for CSRF validation

set -e

ENV_FILE="${1:-.env}"
LOG_FILE="${2:-/var/log/marketedge/app.log}"

echo "🔒 Enabling CSRF Protection"
echo "==========================="
echo "Env file: ${ENV_FILE}"
echo ""

# Check if .env exists
if [ ! -f "${ENV_FILE}" ]; then
    echo "❌ Error: ${ENV_FILE} not found"
    exit 1
fi

# Check current CSRF status
CURRENT_STATUS=$(grep CSRF_ENABLED "${ENV_FILE}" | cut -d= -f2)
echo "Current CSRF_ENABLED: ${CURRENT_STATUS}"

# Confirm with user
echo ""
read -p "Enable CSRF protection? (yes/no): " CONFIRM
if [ "${CONFIRM}" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

# Update .env
echo ""
echo "Updating ${ENV_FILE}..."
sed -i.bak 's/CSRF_ENABLED=False/CSRF_ENABLED=True/' "${ENV_FILE}"
echo "✅ Updated CSRF_ENABLED=True"

# Restart service (adjust for your deployment)
echo ""
echo "Restarting backend service..."
# Uncomment appropriate restart command:
# systemctl restart marketedge-backend
# supervisorctl restart marketedge
# pm2 restart marketedge
# docker-compose restart backend
echo "⚠️  Manual restart required (adjust script for your deployment)"

# Monitor logs
echo ""
echo "Monitor CSRF validation logs:"
echo "tail -f ${LOG_FILE} | grep csrf"
echo ""
echo "✅ CSRF protection enabled"
echo "   Watch logs for 5 minutes to ensure no false positives"
