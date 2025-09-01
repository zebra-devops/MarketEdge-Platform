#!/bin/bash

# Setup Git Hooks for Environment Security
# Prevents accidental commits of .env files and detects secret patterns

set -e

HOOKS_DIR="../.git/hooks"
BACKEND_DIR=$(pwd)

echo "🔗 Setting up Git hooks for environment security..."

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash

# Environment Security Pre-commit Hook
# Prevents .env files from being committed and detects potential secrets

echo "🔒 Running environment security checks..."

# Check for .env files being committed
env_files=$(git diff --cached --name-only | grep -E '\.env$|\.env\.' || true)
if [ -n "$env_files" ]; then
    echo "❌ ERROR: Attempting to commit environment files:"
    echo "$env_files"
    echo ""
    echo "Environment files should never be committed to git!"
    echo "These files may contain sensitive information like:"
    echo "  - Database passwords"
    echo "  - API keys and secrets"
    echo "  - Authentication tokens"
    echo ""
    echo "To fix this:"
    echo "  git reset HEAD $env_files"
    echo "  git add -A && git commit"
    echo ""
    exit 1
fi

# Check for potential secret patterns in staged files
secret_patterns=(
    "AUTH0_CLIENT_SECRET=.*[a-zA-Z0-9]{32,}"
    "JWT_SECRET_KEY=.*[a-zA-Z0-9]{32,}"
    "DATABASE_URL=postgresql://.*:.*@"
    "API_KEY=.*[a-zA-Z0-9]{20,}"
    "SECRET=.*[a-zA-Z0-9]{20,}"
    "PASSWORD=.*[a-zA-Z0-9]{8,}"
    "TOKEN=.*[a-zA-Z0-9]{20,}"
)

found_secrets=false
for pattern in "${secret_patterns[@]}"; do
    matches=$(git diff --cached --name-only | xargs -I{} sh -c 'git show :{} 2>/dev/null || echo ""' | grep -E "$pattern" || true)
    if [ -n "$matches" ]; then
        if [ "$found_secrets" = false ]; then
            echo "⚠️  WARNING: Potential secrets detected in staged changes:"
            found_secrets=true
        fi
        echo "  Pattern: $pattern"
    fi
done

if [ "$found_secrets" = true ]; then
    echo ""
    echo "Please review the staged changes for any hardcoded secrets."
    echo "Consider using environment variables or a secret management system."
    echo ""
    read -p "Continue with commit anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Commit aborted."
        exit 1
    fi
fi

echo "✅ Environment security checks passed"
EOF

# Pre-push hook
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash

# Environment Security Pre-push Hook
# Final check before pushing to remote

echo "🔒 Running pre-push environment security checks..."

# Check if any .env files exist in the repo
env_in_repo=$(git ls-files | grep -E '\.env$|\.env\.' || true)
if [ -n "$env_in_repo" ]; then
    echo "❌ ERROR: Environment files found in repository:"
    echo "$env_in_repo"
    echo ""
    echo "These files should be removed from git history!"
    echo "Use: git filter-branch --tree-filter 'rm -f FILE' HEAD"
    exit 1
fi

# Validate current environment if backend directory exists
if [ -f "backend/.env" ] && [ -f "backend/app/core/secret_manager.py" ]; then
    cd backend
    if python3 -c "
from app.core.secret_manager import SecretManager
import sys
try:
    sm = SecretManager('.env')
    valid, errors = sm.validate_basic()
    if not valid:
        print('❌ Environment validation failed:')
        for error in errors:
            print(f'  - {error}')
        sys.exit(1)
    else:
        print('✅ Environment validation passed')
except Exception as e:
    print(f'⚠️  Could not validate environment: {e}')
"; then
        cd ..
    else
        cd ..
        echo "❌ Environment validation failed - check your .env file"
        exit 1
    fi
fi

echo "✅ Pre-push security checks passed"
EOF

# Make hooks executable
chmod +x "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-push"

echo "✅ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
echo "  📋 pre-commit: Prevents .env file commits and detects secret patterns"
echo "  🚀 pre-push: Validates environment before pushing"
echo ""
echo "To test the hooks:"
echo "  git add .env  # This should be blocked"
echo "  git commit -m 'test'  # This will run security checks"
echo ""