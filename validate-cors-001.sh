#!/bin/bash

# CORS-001 Validation Script
# Tests Docker Multi-Service Configuration

set -e

echo "🧪 CORS-001: Docker Multi-Service Configuration Validation"
echo "========================================================"
echo ""

# Check if required files exist
echo "📋 Step 1: Checking configuration files..."
echo "------------------------------------------"

required_files=(
    "Dockerfile"
    "supervisord.conf"
    "Caddyfile"
    "start.sh"
    "railway.toml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "📦 Step 2: Validating Dockerfile configuration..."
echo "------------------------------------------------"

# Check Dockerfile contains required components
if grep -q "supervisor" Dockerfile; then
    echo "✅ Supervisord installed"
else
    echo "❌ Supervisord not found in Dockerfile"
    exit 1
fi

if grep -q "caddy" Dockerfile; then
    echo "✅ Caddy installed"
else
    echo "❌ Caddy not found in Dockerfile"
    exit 1
fi

if grep -q "supervisord" Dockerfile; then
    echo "✅ Supervisord CMD configured"
else
    echo "❌ Supervisord CMD not configured"
    exit 1
fi

echo ""
echo "⚙️  Step 3: Validating supervisord configuration..."
echo "-------------------------------------------------"

if grep -q "program:fastapi" supervisord.conf; then
    echo "✅ FastAPI service configured"
else
    echo "❌ FastAPI service not configured"
    exit 1
fi

if grep -q "program:caddy" supervisord.conf; then
    echo "✅ Caddy service configured"
else
    echo "❌ Caddy service not configured"
    exit 1
fi

echo ""
echo "🌐 Step 4: Validating Caddyfile configuration..."
echo "-----------------------------------------------"

if grep -q "reverse_proxy localhost:8000" Caddyfile; then
    echo "✅ Reverse proxy to FastAPI configured"
else
    echo "❌ Reverse proxy not configured"
    exit 1
fi

if grep -q "Access-Control-Allow" Caddyfile; then
    echo "✅ Basic CORS headers configured"
else
    echo "❌ CORS headers not configured"
    exit 1
fi

echo ""
echo "🚀 Step 5: Validating Railway configuration..."
echo "---------------------------------------------"

if grep -q "PORT.*80" railway.toml; then
    echo "✅ Railway configured for port 80 (Caddy)"
else
    echo "❌ Railway port not configured for Caddy"
    exit 1
fi

echo ""
echo "🎯 Step 6: Configuration validation summary..."
echo "--------------------------------------------"

echo "✅ Docker multi-service setup: VALID"
echo "✅ Supervisord configuration: VALID"
echo "✅ Caddy reverse proxy: VALID"
echo "✅ FastAPI backend: VALID"
echo "✅ Railway integration: VALID"

echo ""
echo "🎉 CORS-001 Configuration Validation: PASSED"
echo "============================================="
echo ""
echo "Ready for:"
echo "- CORS-002: Enhanced Caddyfile CORS configuration"
echo "- CORS-003: Railway service integration and deployment"
echo ""
echo "Manual testing required:"
echo "1. Docker build: docker build -t cors-001-test ."
echo "2. Local run: docker run -p 80:80 -p 8000:8000 cors-001-test"
echo "3. Health check: curl http://localhost:80/health"
echo "4. CORS debug: curl http://localhost:80/cors-debug"