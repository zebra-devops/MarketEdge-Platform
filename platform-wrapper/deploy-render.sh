#!/bin/bash

# Epic 2: Render Deployment Wrapper Script
# This script can be run from the project root directory

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to project root
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "backend/render.yaml" ]; then
    echo "❌ Error: backend/render.yaml not found!"
    echo "Make sure you're running this from the platform-wrapper root directory"
    exit 1
fi

echo "🚀 MarketEdge Platform - Epic 2 Render Deployment"
echo "================================================="
echo "Project Root: $SCRIPT_DIR"
echo "Render Config: backend/render.yaml"
echo ""

# Run the main deployment script
exec "./frontend/scripts/deploy-to-render.sh" "$@"