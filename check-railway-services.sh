#!/bin/bash

echo "=== Railway Service Analysis ==="
echo

echo "1. Current Railway Project:"
railway status
echo

echo "2. Current Service Variables:"
railway variables
echo

echo "3. Testing PostgreSQL Connection:"
echo "Database URL from variables:"
DATABASE_URL=$(railway variables | grep "DATABASE_URL" | cut -d'│' -f2 | xargs)
echo "$DATABASE_URL"
echo

echo "4. Checking if database has tables:"
if command -v psql &> /dev/null; then
    echo "Listing tables in database:"
    psql "$DATABASE_URL" -c "\dt" 2>/dev/null || echo "No tables found or connection failed"
else
    echo "psql not installed - cannot check database directly"
fi
echo

echo "5. GitHub Repository Status:"
echo "Remote URL:" $(git remote get-url origin 2>/dev/null || echo "Not a git repository")
echo "Current branch:" $(git branch --show-current 2>/dev/null || echo "Not a git repository")
echo "Status:" $(git status --porcelain 2>/dev/null | wc -l | xargs) "files changed"
echo

echo "6. Railway Configuration:"
if [ -f "railway.toml" ]; then
    echo "railway.toml exists - good!"
    echo "Build configuration:"
    grep -A 5 "\[build\]" railway.toml || echo "No build section found"
else
    echo "No railway.toml found"
fi
echo

echo "7. Docker Configuration:"
if [ -f "Dockerfile" ]; then
    echo "Dockerfile exists - good!"
    echo "Base image:" $(head -1 Dockerfile)
else
    echo "No Dockerfile found"
fi
echo

echo "=== Next Steps ==="
echo "1. Visit Railway Dashboard: https://railway.app/dashboard"
echo "2. Find your 'platform-wrapper-backend' project"
echo "3. Note all existing services"
echo "4. If PostgreSQL database is empty, run migrations"
echo "5. Set up GitHub deployment for backend service"
echo "6. Clean up any redundant services"
echo
echo "Run this command to see the detailed guide:"
echo "cat docs/2025_08_10/deployment/GitHubRailwayDeploymentGuide.md"