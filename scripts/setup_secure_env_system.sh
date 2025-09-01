#!/bin/bash

# Secure Environment Management System Installer
# Prevents environment variable regressions like the Auth0 client secret incident

set -e

echo "🔒 Installing Secure Environment Management System..."

# Create directory structure
mkdir -p scripts
mkdir -p docs
mkdir -p .env_backups
mkdir -p app/core

# Ensure .env_backups is gitignored
if ! grep -q ".env_backups/" .gitignore 2>/dev/null; then
    echo ".env_backups/" >> .gitignore
    echo "📁 Added .env_backups to .gitignore"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install watchdog requests python-dotenv 2>/dev/null || {
    echo "⚠️  Please install dependencies manually: pip install watchdog requests python-dotenv"
}

# Create initial backup of current .env
if [ -f ".env" ]; then
    echo "💾 Creating initial backup of .env file..."
    python3 scripts/env_backup_manager.py backup .env --reason "secure-system-setup" 2>/dev/null || {
        echo "⚠️  Could not create initial backup. Will continue with setup."
    }
fi

# Setup Git hooks
echo "🔗 Installing Git hooks..."
./scripts/setup_git_hooks.sh

# Test the system
echo "🧪 Testing system components..."

# Test backup system
python3 scripts/env_backup_manager.py list >/dev/null 2>&1 && echo "✅ Backup system working" || echo "⚠️  Backup system needs attention"

# Test secret validation
python3 -c "from app.core.secret_manager import SecretManager; sm = SecretManager('.env'); sm.validate_basic()" >/dev/null 2>&1 && echo "✅ Secret validation working" || echo "⚠️  Secret validation needs attention"

echo ""
echo "🎉 Secure Environment Management System installed successfully!"
echo ""
echo "📋 Quick Start Commands:"
echo "  Create backup:     python3 scripts/env_backup_manager.py backup .env --reason 'manual-backup'"
echo "  Safe editing:      python3 scripts/safe_env_editor.py .env"
echo "  Monitor changes:   python3 scripts/env_file_monitor.py --daemon"
echo "  List backups:      python3 scripts/env_backup_manager.py list"
echo "  Health check:      curl http://localhost:8000/secrets/validate"
echo ""
echo "📖 Full documentation: docs/SECURE_ENVIRONMENT_MANAGEMENT.md"
echo ""
echo "🚨 IMPORTANT: The system is now protecting against environment variable regressions!"