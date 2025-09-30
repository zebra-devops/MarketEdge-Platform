#!/bin/bash

# Setup GitHub Secrets for US-0 Zebra Associates Protection
# This script adds the required Auth0 secrets to GitHub repository

set -e

echo "================================================"
echo "🔐 GitHub Secrets Setup for US-0"
echo "================================================"
echo ""
echo "Repository: zebra-devops/MarketEdge-Platform"
echo "Purpose: Zebra Associates Protection Smoke Test"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ ERROR: GitHub CLI (gh) is not installed"
    echo "Install: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ ERROR: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI authenticated"
echo ""

# Auth0 credentials from .env
AUTH0_DOMAIN="dev-g8trhgbfdq2sk2m8.us.auth0.com"
AUTH0_CLIENT_ID="wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6"
AUTH0_CLIENT_SECRET="78293nvrWP0gnj27AZ51mRetNJ-hAomPVqTI5F77SGXxkjOvl6jAG8xB2c2c_alN"
ZEBRA_TEST_EMAIL="devops@zebra.associates"

# Generate a secure JWT secret key
JWT_SECRET_KEY=$(openssl rand -hex 32)

echo "📋 Secrets to be added:"
echo "  - AUTH0_DOMAIN"
echo "  - AUTH0_CLIENT_ID"
echo "  - AUTH0_CLIENT_SECRET"
echo "  - JWT_SECRET_KEY"
echo "  - ZEBRA_TEST_EMAIL"
echo "  - ZEBRA_TEST_PASSWORD"
echo ""

# Prompt for test password
echo "🔑 Enter the Auth0 password for devops@zebra.associates:"
read -s ZEBRA_TEST_PASSWORD
echo ""

if [ -z "$ZEBRA_TEST_PASSWORD" ]; then
    echo "❌ ERROR: Password cannot be empty"
    exit 1
fi

echo ""
echo "📤 Adding secrets to GitHub repository..."
echo ""

# Add secrets one by one
echo "1/6 Adding AUTH0_DOMAIN..."
echo "$AUTH0_DOMAIN" | gh secret set AUTH0_DOMAIN --repo zebra-devops/MarketEdge-Platform

echo "2/6 Adding AUTH0_CLIENT_ID..."
echo "$AUTH0_CLIENT_ID" | gh secret set AUTH0_CLIENT_ID --repo zebra-devops/MarketEdge-Platform

echo "3/6 Adding AUTH0_CLIENT_SECRET..."
echo "$AUTH0_CLIENT_SECRET" | gh secret set AUTH0_CLIENT_SECRET --repo zebra-devops/MarketEdge-Platform

echo "4/6 Adding JWT_SECRET_KEY..."
echo "$JWT_SECRET_KEY" | gh secret set JWT_SECRET_KEY --repo zebra-devops/MarketEdge-Platform

echo "5/6 Adding ZEBRA_TEST_EMAIL..."
echo "$ZEBRA_TEST_EMAIL" | gh secret set ZEBRA_TEST_EMAIL --repo zebra-devops/MarketEdge-Platform

echo "6/6 Adding ZEBRA_TEST_PASSWORD..."
echo "$ZEBRA_TEST_PASSWORD" | gh secret set ZEBRA_TEST_PASSWORD --repo zebra-devops/MarketEdge-Platform

echo ""
echo "================================================"
echo "✅ All secrets added successfully!"
echo "================================================"
echo ""
echo "📋 Verification:"
echo "Run: gh secret list --repo zebra-devops/MarketEdge-Platform"
echo ""
echo "🧪 Next Steps:"
echo "1. Verify secrets: gh secret list"
echo "2. Configure branch protection to require 'Zebra Protection Gate'"
echo "3. Create a test PR to verify workflow runs"
echo ""
echo "🦓 £925K Zebra Associates Opportunity: PROTECTED"
echo ""