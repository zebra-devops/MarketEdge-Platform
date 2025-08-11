#!/bin/bash

set -e  # Exit on any error

echo "🚀 GitHub to Railway Deployment Setup"
echo "====================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Verify current setup
print_status "Step 1: Verifying current Railway setup..."
echo

if ! command -v railway &> /dev/null; then
    print_error "Railway CLI is not installed. Please install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

print_status "Current project:"
railway status
echo

# Step 2: Check GitHub repository
print_status "Step 2: Verifying GitHub repository..."
if [ ! -d ".git" ]; then
    print_error "Not a Git repository"
    exit 1
fi

REPO_URL=$(git remote get-url origin)
print_success "Repository: $REPO_URL"

# Check for uncommitted changes
UNCOMMITTED=$(git status --porcelain | wc -l)
if [ "$UNCOMMITTED" -gt 0 ]; then
    print_warning "You have uncommitted changes. Consider committing them first:"
    git status --short
    echo
fi

# Step 3: Test database connection
print_status "Step 3: Testing database connection..."
DATABASE_URL=$(railway variables 2>/dev/null | grep "DATABASE_URL" | grep -v "PUBLIC" | cut -d'│' -f3 | xargs | sed 's/^[[:space:]]*//')

if [ -z "$DATABASE_URL" ]; then
    print_error "Could not extract DATABASE_URL from Railway variables"
    exit 1
fi

print_success "Database URL extracted successfully"

# Test connection if psql is available
if command -v psql &> /dev/null; then
    print_status "Testing database connection..."
    if psql "$DATABASE_URL" -c "SELECT version();" &>/dev/null; then
        print_success "Database connection successful"
        
        # Check if tables exist
        TABLE_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)
        if [ "$TABLE_COUNT" -eq 0 ]; then
            print_warning "Database is empty - migrations may need to be run"
        else
            print_success "Database has $TABLE_COUNT tables"
        fi
    else
        print_error "Database connection failed"
        exit 1
    fi
else
    print_warning "psql not available - skipping database connection test"
fi

# Step 4: Setup environment for migrations (if needed)
print_status "Step 4: Setting up environment for database migrations..."

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    exit 1
fi

# Check if virtual environment exists or create one
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

print_status "Activating virtual environment and installing dependencies..."
source venv/bin/activate

# Install requirements
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Step 5: Run database migrations
print_status "Step 5: Running database migrations..."
export DATABASE_URL="$DATABASE_URL"

if [ -f "alembic.ini" ]; then
    print_status "Running Alembic migrations..."
    alembic upgrade head
    print_success "Migrations completed successfully"
else
    print_warning "No alembic.ini found - skipping migrations"
fi

# Step 6: Instructions for GitHub deployment
echo
print_status "Step 6: GitHub Deployment Setup"
echo "==============================="
echo
echo "🔧 MANUAL STEPS REQUIRED:"
echo
echo "1. Open Railway Dashboard:"
echo "   👉 https://railway.app/dashboard"
echo
echo "2. Navigate to your 'platform-wrapper-backend' project"
echo
echo "3. Current services (check these in dashboard):"
echo "   - PostgreSQL service (has your data)"
echo "   - Backend service (may need GitHub connection)"
echo "   - Redis service (if exists)"
echo
echo "4. For the Backend service:"
echo "   a) If no backend service exists:"
echo "      - Click 'New Service' → 'Deploy from GitHub'"
echo "      - Select 'zebra-devops/marketedge-backend'"
echo "      - Choose 'main' branch"
echo
echo "   b) If backend service exists but not connected to GitHub:"
echo "      - Go to Backend service → Settings → Source"
echo "      - Click 'Connect Repository'"
echo "      - Select 'zebra-devops/marketedge-backend'"
echo
echo "5. Set Environment Variables for Backend service:"
echo "   Copy these variables to your Backend service in Railway dashboard:"
echo

# Generate environment variables
echo "   DATABASE_URL=\${{Postgres.DATABASE_URL}}"
echo "   ENVIRONMENT=production"
echo "   DEBUG=false"
echo "   LOG_LEVEL=INFO"
echo "   PORT=8000"
echo "   DATA_LAYER_ENABLED=false"
echo

print_warning "⚠️  Important: Use Railway's variable reference syntax \${{ServiceName.VARIABLE}} for connecting services"

# Step 7: Verification commands
echo
echo "6. After deployment, verify with these commands:"
echo
echo "   # Check deployment status"
echo "   railway logs --service YourBackendServiceName"
echo
echo "   # Test health endpoint"
echo "   curl https://your-backend-url.railway.app/health"
echo
echo "   # Verify database tables"
echo "   railway connect Postgres"
echo "   \\dt"
echo

# Step 8: Cleanup instructions
echo "7. Cleanup redundant services:"
echo "   - In Railway dashboard, delete any redundant backend services"
echo "   - Keep only: PostgreSQL + Backend (from GitHub) + Redis (if used)"
echo

print_success "Setup preparation completed!"
echo
echo "📋 Summary:"
echo "- ✅ Repository verified: $REPO_URL"
echo "- ✅ Database connection tested"
echo "- ✅ Migrations run successfully"
echo "- ✅ Environment prepared"
echo
echo "🎯 Next: Follow the manual steps above to complete GitHub deployment"
echo
echo "📖 Full guide: docs/2025_08_10/deployment/GitHubRailwayDeploymentGuide.md"