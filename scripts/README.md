# Secure Environment Management Scripts

This directory contains scripts for managing environment variables and secrets securely.

## Quick Start

```bash
# Install the complete system
./setup_secure_env_system.sh

# Create a backup
python env_backup_manager.py backup ../.env --reason "manual"

# Safe edit environment file
python safe_env_editor.py ../.env

# Start monitoring
python env_file_monitor.py --daemon
```

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_secure_env_system.sh` | Complete system installation | `./setup_secure_env_system.sh` |
| `env_backup_manager.py` | Backup and restore .env files | `python env_backup_manager.py --help` |
| `secret_manager.py` | Validate and manage secrets | Integrated into FastAPI app |
| `env_file_monitor.py` | Monitor file changes | `python env_file_monitor.py --daemon` |
| `safe_env_editor.py` | Edit files safely | `python safe_env_editor.py .env` |
| `setup_git_hooks.sh` | Install Git hooks | `./setup_git_hooks.sh` |

## Key Features

- 🔒 **Automatic Backups**: Before every modification
- 🛡️ **Secret Validation**: Startup and runtime checks  
- 👁️ **File Monitoring**: Real-time change detection
- ✏️ **Safe Editing**: Built-in validation and backup
- 🚫 **Git Protection**: Prevents secret commits
- 📊 **Health Monitoring**: API endpoints for status

## Emergency Recovery

```bash
# List available backups
python env_backup_manager.py list

# Restore from backup
python env_backup_manager.py restore backup_filename.backup

# Check secret validation
curl http://localhost:8000/secrets/validate
```

## Documentation

See `../docs/SECURE_ENVIRONMENT_MANAGEMENT.md` for complete documentation.