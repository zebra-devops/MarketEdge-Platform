#!/usr/bin/env python3
"""
Staging Environment Diagnostic Script
Run this on the staging server to verify environment configuration
"""

import os
import sys
import json
from urllib.parse import urlparse

def color_text(text, color_code):
    """Add color to terminal output"""
    if sys.stdout.isatty():
        return f"\033[{color_code}m{text}\033[0m"
    return text

def red(text): return color_text(text, "91")
def green(text): return color_text(text, "92")
def yellow(text): return color_text(text, "93")
def blue(text): return color_text(text, "94")
def bold(text): return color_text(text, "1")

def check_env():
    print(bold("\n=== MarketEdge Staging Environment Diagnostic ===\n"))

    errors = []
    warnings = []

    # Define expected values for staging
    expected_values = {
        "AUTH0_CLIENT_ID": {
            "correct": "9FRjf82esKN4fx3iY337CT1jpvNVFbAP",
            "wrong": "wEgjaOnk8MSgRTdaWURNKaFu80MG0Sa6",
            "desc": "Staging Auth0 Client ID"
        },
        "AUTH0_DOMAIN": {
            "correct": "dev-g8trhgbfdq2sk2m8.us.auth0.com",
            "desc": "Auth0 domain"
        },
        "AUTH0_AUDIENCE": {
            "correct": "https://dev-g8trhgbfdq2sk2m8.us.auth0.com/api/v2/",
            "desc": "Auth0 API audience"
        },
        "ENVIRONMENT": {
            "correct": "staging",
            "desc": "Environment name"
        },
        "AUTH0_CLIENT_SECRET": {
            "correct": "xrdILihwwXxXNqDjxEa65J1aSjExjC4PNRzxUAVcvy3K9OcwhT_FVEqwziA-bQa7",
            "desc": "Staging Auth0 secret"
        },
        "JWT_SECRET_KEY": {
            "correct_length": 64,
            "desc": "JWT signing key"
        }
    }

    print(bold("Critical Variables Check:\n"))

    # Check AUTH0_CLIENT_ID first (most critical)
    client_id = os.getenv("AUTH0_CLIENT_ID", "NOT SET")
    if client_id == "NOT SET":
        print(red(f"❌ AUTH0_CLIENT_ID: NOT SET"))
        errors.append("AUTH0_CLIENT_ID is not set")
    elif client_id == expected_values["AUTH0_CLIENT_ID"]["wrong"]:
        print(red(f"❌ AUTH0_CLIENT_ID: WRONG VALUE (using dev instead of staging)"))
        print(f"   Current: {client_id}")
        print(f"   Should be: {expected_values['AUTH0_CLIENT_ID']['correct']}")
        errors.append("AUTH0_CLIENT_ID is using dev value instead of staging")
    elif client_id == expected_values["AUTH0_CLIENT_ID"]["correct"]:
        print(green(f"✅ AUTH0_CLIENT_ID: Correct staging value"))
    else:
        print(yellow(f"⚠️  AUTH0_CLIENT_ID: Unknown value ({client_id[:10]}...)"))
        warnings.append(f"AUTH0_CLIENT_ID has unexpected value")

    # Check other critical variables
    for var, config in expected_values.items():
        if var == "AUTH0_CLIENT_ID":
            continue  # Already checked

        value = os.getenv(var, "NOT SET")

        if value == "NOT SET":
            print(red(f"❌ {var}: NOT SET ({config['desc']})"))
            errors.append(f"{var} is not set")
        elif "correct" in config:
            if value == config["correct"]:
                if "SECRET" in var or "KEY" in var:
                    print(green(f"✅ {var}: Set correctly ({len(value)} chars)"))
                else:
                    print(green(f"✅ {var}: {value}"))
            else:
                if "SECRET" in var or "KEY" in var:
                    print(yellow(f"⚠️  {var}: Set but may be incorrect ({len(value)} chars)"))
                    warnings.append(f"{var} may have incorrect value")
                else:
                    print(yellow(f"⚠️  {var}: {value} (expected: {config['correct']})"))
                    warnings.append(f"{var} has unexpected value")
        elif "correct_length" in config:
            if len(value) >= config["correct_length"]:
                print(green(f"✅ {var}: Set ({len(value)} chars)"))
            else:
                print(yellow(f"⚠️  {var}: Set but short ({len(value)} chars, expected {config['correct_length']}+)"))
                warnings.append(f"{var} may be too short")

    # Check DATABASE_URL
    print(bold("\nDatabase Configuration:\n"))
    db_url = os.getenv("DATABASE_URL", "NOT SET")
    if db_url == "NOT SET":
        print(red("❌ DATABASE_URL: NOT SET"))
        errors.append("DATABASE_URL is not set")
    else:
        try:
            parsed = urlparse(db_url)
            if parsed.hostname:
                if "-a" in parsed.hostname or "-a." in parsed.hostname:
                    print(green(f"✅ DATABASE_URL: Internal Render URL detected"))
                    print(f"   Host: {parsed.hostname}")
                    print(f"   Database: {parsed.path.lstrip('/')}")
                elif "render.com" in parsed.hostname:
                    print(yellow("⚠️  DATABASE_URL: External URL (should use internal for better performance)"))
                    print(f"   Host: {parsed.hostname}")
                    warnings.append("DATABASE_URL using external URL instead of internal")
                else:
                    print(green(f"✅ DATABASE_URL: Set"))
                    print(f"   Host: {parsed.hostname[:30]}...")
        except Exception as e:
            print(red(f"❌ DATABASE_URL: Invalid format - {str(e)}"))
            errors.append("DATABASE_URL has invalid format")

    # Check optional but important variables
    print(bold("\nAdditional Configuration:\n"))

    run_migrations = os.getenv("RUN_MIGRATIONS", "NOT SET")
    if run_migrations == "true":
        print(green("✅ RUN_MIGRATIONS: true"))
    else:
        print(yellow(f"⚠️  RUN_MIGRATIONS: {run_migrations} (migrations may not run automatically)"))
        if run_migrations == "NOT SET":
            warnings.append("RUN_MIGRATIONS not set, migrations won't run automatically")

    cors_origins = os.getenv("CORS_ORIGINS", "NOT SET")
    if cors_origins != "NOT SET":
        if "staging.zebra.associates" in cors_origins:
            print(green("✅ CORS_ORIGINS: Includes staging domain"))
        else:
            print(yellow("⚠️  CORS_ORIGINS: May be missing staging.zebra.associates"))
            warnings.append("CORS_ORIGINS may be missing staging domain")
    else:
        print(yellow("⚠️  CORS_ORIGINS: Not set"))

    redis_url = os.getenv("REDIS_URL", "NOT SET")
    if redis_url != "NOT SET":
        print(green("✅ REDIS_URL: Set"))
    else:
        print(blue("ℹ️  REDIS_URL: Not set (optional)"))

    # Summary
    print(bold("\n" + "="*50))
    print(bold("DIAGNOSTIC SUMMARY"))
    print("="*50)

    if errors:
        print(red(f"\n🚨 CRITICAL ERRORS ({len(errors)}):"))
        for i, error in enumerate(errors, 1):
            print(red(f"  {i}. {error}"))

        # Provide specific fix for AUTH0_CLIENT_ID issue
        if any("AUTH0_CLIENT_ID" in e for e in errors):
            print(bold("\n🔧 FIX REQUIRED:"))
            print("  1. Go to Render Dashboard > Environment")
            print(f"  2. Set AUTH0_CLIENT_ID to: {expected_values['AUTH0_CLIENT_ID']['correct']}")
            print("  3. Save changes and wait for redeploy")

    if warnings:
        print(yellow(f"\n⚠️  WARNINGS ({len(warnings)}):"))
        for i, warning in enumerate(warnings, 1):
            print(yellow(f"  {i}. {warning}"))

    if not errors and not warnings:
        print(green("\n✅ All environment variables configured correctly!"))

    # Test database connection if available
    if db_url != "NOT SET" and not any("DATABASE_URL" in e for e in errors):
        print(bold("\n" + "="*50))
        print(bold("DATABASE CONNECTION TEST"))
        print("="*50)
        try:
            import psycopg2
            print("Attempting database connection...")
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT current_database(), current_user, version();")
            result = cur.fetchone()
            print(green("✅ Database connection successful!"))
            print(f"   Database: {result[0]}")
            print(f"   User: {result[1]}")
            print(f"   Version: {result[2][:30]}...")
            cur.close()
            conn.close()
        except ImportError:
            print(blue("ℹ️  psycopg2 not installed, skipping connection test"))
        except Exception as e:
            print(red(f"❌ Database connection failed: {str(e)[:100]}"))
            errors.append("Database connection test failed")

    # Return status
    return len(errors) == 0

if __name__ == "__main__":
    print(bold("MarketEdge Staging Environment Diagnostic"))
    print("Version: 1.0")
    print(f"Running on: {os.getenv('HOSTNAME', 'unknown host')}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'not set')}")

    success = check_env()

    if not success:
        print(bold(red("\n❌ Environment configuration has issues that need to be fixed")))
        print("\nFor detailed instructions, see:")
        print("  /docs/2025_10_06/deployment/staging-env-diagnostics.md")
        sys.exit(1)
    else:
        print(bold(green("\n✅ Environment configuration looks good!")))
        sys.exit(0)