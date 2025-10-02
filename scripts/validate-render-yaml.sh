#!/bin/bash

# Render.yaml Validation Script
# Purpose: Validate render.yaml configuration for common issues and conflicts
# Usage: ./scripts/validate-render-yaml.sh
# Exit codes: 0 for success, 1 for failure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RENDER_YAML="render.yaml"
ERRORS=0
WARNINGS=0

echo "========================================="
echo "Render.yaml Validation Script"
echo "========================================="
echo ""

# Check if render.yaml exists
if [ ! -f "$RENDER_YAML" ]; then
    echo -e "${RED}ERROR: $RENDER_YAML not found!${NC}"
    exit 1
fi

# Function to check for value + sync conflicts
check_value_sync_conflicts() {
    echo "Checking for value + sync conflicts..."

    # Use Python for reliable YAML parsing
    python3 << 'EOF'
import yaml
import sys

errors = []
warnings = []

try:
    with open('render.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Check services
    if 'services' in config:
        for service_idx, service in enumerate(config['services']):
            service_name = service.get('name', f'service_{service_idx}')

            if 'envVars' in service:
                for var_idx, var in enumerate(service['envVars']):
                    key = var.get('key', f'var_{var_idx}')

                    # Check for conflicting fields
                    has_value = 'value' in var
                    has_sync = 'sync' in var
                    has_from = any(k.startswith('from') for k in var.keys())
                    has_generate = 'generateValue' in var

                    # Rule 1: value + sync = false is a conflict
                    if has_value and has_sync and not var.get('sync', True):
                        errors.append(f"Service '{service_name}', env var '{key}': Cannot have both 'value' and 'sync: false'")

                    # Rule 2: from* + sync is a conflict
                    if has_from and has_sync:
                        errors.append(f"Service '{service_name}', env var '{key}': Cannot have both 'from*' field and 'sync' field")

                    # Rule 3: generateValue + sync is a conflict
                    if has_generate and has_sync:
                        errors.append(f"Service '{service_name}', env var '{key}': Cannot have both 'generateValue' and 'sync' field")

                    # Warning: sync: false without value/from* (these should be secrets)
                    if has_sync and not var.get('sync', True) and not has_value and not has_from and not has_generate:
                        # This is OK - it's a secret that will be set in dashboard
                        pass

                    # Warning: value without sync field (OK but could be explicit)
                    if has_value and not has_sync and 'previewValue' not in var:
                        # This is OK - sync defaults to true for values
                        pass

    # Print results
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  ❌ {error}")
        sys.exit(1)
    else:
        print("✅ No value + sync conflicts found")

    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")

except yaml.YAMLError as e:
    print(f"❌ YAML parsing error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        ((ERRORS++))
    fi
}

# Function to validate YAML syntax
check_yaml_syntax() {
    echo "Checking YAML syntax..."

    python3 << 'EOF'
import yaml
import sys

try:
    with open('render.yaml', 'r') as f:
        yaml.safe_load(f)
    print("✅ YAML syntax is valid")
except yaml.YAMLError as e:
    print(f"❌ YAML syntax error: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        ((ERRORS++))
    fi
}

# Function to check for required secrets
check_required_secrets() {
    echo "Checking for required secrets configuration..."

    python3 << 'EOF'
import yaml
import sys

required_secrets = [
    'AUTH0_CLIENT_SECRET',
    'AUTH0_ACTION_SECRET',
    'JWT_SECRET_KEY',
    'DATABASE_URL',
    'REDIS_URL'
]

warnings = []

try:
    with open('render.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Check production service
    if 'services' in config:
        for service in config['services']:
            if service.get('name') == 'marketedge-platform':
                if 'envVars' in service:
                    for var in service['envVars']:
                        key = var.get('key', '')
                        if key in required_secrets:
                            # Should have sync: false and no value
                            if 'value' in var:
                                warnings.append(f"Secret '{key}' should not have 'value' field (use Render Dashboard)")
                            if not ('sync' in var and not var['sync']):
                                warnings.append(f"Secret '{key}' should have 'sync: false' to prevent overwriting")

    if warnings:
        print("⚠️  Secret configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("✅ Secret configuration looks good")

except Exception as e:
    print(f"❌ Error checking secrets: {e}")
    sys.exit(1)
EOF
}

# Function to check for duplicate environment variables
check_duplicate_vars() {
    echo "Checking for duplicate environment variables..."

    python3 << 'EOF'
import yaml
import sys
from collections import defaultdict

try:
    with open('render.yaml', 'r') as f:
        config = yaml.safe_load(f)

    errors = []

    if 'services' in config:
        for service in config['services']:
            service_name = service.get('name', 'unknown')
            env_vars = defaultdict(int)

            if 'envVars' in service:
                for var in service['envVars']:
                    if 'key' in var:
                        env_vars[var['key']] += 1

                for key, count in env_vars.items():
                    if count > 1:
                        errors.append(f"Service '{service_name}': Duplicate env var '{key}' ({count} times)")

    if errors:
        print("❌ Duplicate environment variables found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ No duplicate environment variables")

except Exception as e:
    print(f"❌ Error checking duplicates: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        ((ERRORS++))
    fi
}

# Function to validate service configuration
check_service_config() {
    echo "Checking service configuration..."

    python3 << 'EOF'
import yaml
import sys

errors = []
warnings = []

try:
    with open('render.yaml', 'r') as f:
        config = yaml.safe_load(f)

    if 'services' in config:
        for service in config['services']:
            service_name = service.get('name', 'unknown')

            # Check required fields
            if 'type' not in service:
                errors.append(f"Service '{service_name}': Missing 'type' field")
            if 'name' not in service:
                errors.append(f"Service at index: Missing 'name' field")
            if 'runtime' not in service and service.get('type') == 'web':
                errors.append(f"Service '{service_name}': Missing 'runtime' field")

            # Check for common issues
            if service.get('type') == 'web':
                if 'startCommand' not in service:
                    warnings.append(f"Service '{service_name}': No 'startCommand' specified")
                if 'buildCommand' not in service:
                    warnings.append(f"Service '{service_name}': No 'buildCommand' specified")

    if errors:
        print("❌ Service configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("✅ Service configuration valid")

    if warnings:
        print("⚠️  Service configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")

except Exception as e:
    print(f"❌ Error checking services: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        ((ERRORS++))
    fi
}

# Run all validation checks
echo "Starting validation..."
echo ""

check_yaml_syntax
echo ""

check_value_sync_conflicts
echo ""

check_required_secrets
echo ""

check_duplicate_vars
echo ""

check_service_config
echo ""

# Summary
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Validation PASSED${NC}"
    echo "render.yaml is ready for deployment"
    exit 0
else
    echo -e "${RED}❌ Validation FAILED${NC}"
    echo "Found $ERRORS error(s)"
    echo "Please fix the issues above before deploying"
    exit 1
fi