#!/bin/bash
# ============================================================================
# Execute super_admin Grant for matt.lindop@zebra.associates on Staging
# ============================================================================
# This script provides an automated way to grant super_admin role
# Database: marketedge-staging-db (staging environment)
# Target User: matt.lindop@zebra.associates
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/grant_super_admin_staging.sql"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Grant super_admin Role - Staging Environment${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}Target User:${NC} matt.lindop@zebra.associates"
echo -e "${YELLOW}Database:${NC} marketedge-staging-db (staging)"
echo -e "${YELLOW}Desired Role:${NC} super_admin"
echo ""

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${RED}ERROR: Render CLI not found${NC}"
    echo -e "${YELLOW}Install with:${NC} brew install render"
    exit 1
fi

echo -e "${GREEN}✓ Render CLI found${NC}"
echo ""

# Check if SQL file exists
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}ERROR: SQL file not found at ${SQL_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ SQL file found${NC}"
echo ""

# Provide execution options
echo -e "${BLUE}Execution Options:${NC}"
echo -e "  ${GREEN}1)${NC} Interactive SQL (recommended) - Opens psql shell for manual execution"
echo -e "  ${GREEN}2)${NC} Automated SQL - Executes SQL script automatically"
echo -e "  ${GREEN}3)${NC} View SQL only - Display SQL without executing"
echo -e "  ${GREEN}4)${NC} Cancel"
echo ""
read -p "Select option (1-4): " option

case $option in
    1)
        echo ""
        echo -e "${BLUE}Opening interactive PostgreSQL shell...${NC}"
        echo -e "${YELLOW}Note: You'll need to manually run the SQL commands${NC}"
        echo -e "${YELLOW}Tip: Copy commands from ${SQL_FILE}${NC}"
        echo ""
        echo -e "${GREEN}Connecting to marketedge-staging-db...${NC}"
        echo ""
        render psql marketedge-staging-db
        ;;
    2)
        echo ""
        echo -e "${YELLOW}WARNING: This will execute SQL script automatically${NC}"
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo ""
            echo -e "${BLUE}Executing SQL script...${NC}"
            render psql marketedge-staging-db < "$SQL_FILE"
            echo ""
            echo -e "${GREEN}✓ SQL script executed${NC}"
            echo -e "${YELLOW}Please verify the results above${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
            exit 0
        fi
        ;;
    3)
        echo ""
        echo -e "${BLUE}SQL Script Contents:${NC}"
        echo -e "${BLUE}============================================================================${NC}"
        cat "$SQL_FILE"
        echo -e "${BLUE}============================================================================${NC}"
        echo ""
        echo -e "${YELLOW}To execute manually:${NC}"
        echo -e "  render psql marketedge-staging-db"
        echo -e "  Then copy and paste the SQL commands above"
        ;;
    4)
        echo -e "${YELLOW}Cancelled${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Post-Execution Steps:${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "1. ${GREEN}Verify Database Update:${NC}"
echo -e "   Check that the SQL output shows role = 'super_admin'"
echo ""
echo -e "2. ${GREEN}Clear User Session:${NC}"
echo -e "   - Open https://staging.zebra.associates in browser"
echo -e "   - Open browser console (F12)"
echo -e "   - Run: localStorage.clear(); sessionStorage.clear();"
echo -e "   - Reload page"
echo ""
echo -e "3. ${GREEN}Fresh Login:${NC}"
echo -e "   - Navigate to https://staging.zebra.associates/login"
echo -e "   - Login with matt.lindop@zebra.associates"
echo -e "   - New JWT token will include super_admin role"
echo ""
echo -e "4. ${GREEN}Verify Admin Access:${NC}"
echo -e "   - Navigate to https://staging.zebra.associates/admin"
echo -e "   - Should load successfully without errors"
echo -e "   - Test user management and feature flags"
echo ""
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo -e "${YELLOW}For detailed verification steps, see:${NC}"
echo -e "  ${SCRIPT_DIR}/STAGING_SUPER_ADMIN_GRANT_GUIDE.md"
echo ""
