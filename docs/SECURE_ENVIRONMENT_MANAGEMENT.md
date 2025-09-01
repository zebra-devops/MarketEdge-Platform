# Secure Environment Management System

## Overview

This system prevents environment variable regressions like the Auth0 client secret incident that occurred on August 20th, 2024. It provides automated backup, validation, and monitoring of environment variables with multiple layers of protection.

## 🚨 Emergency Procedures

### Auth0 Authentication Failing (400 Bad Request)

**Symptoms**: 
- `POST /api/v1/auth/login` returns 400 "Failed to exchange authorization code"
- Frontend authentication errors

**Quick Recovery**:
```bash
# 1. Check validation status
curl http://localhost:8000/secrets/validate

# 2. List recent backups
python3 scripts/env_backup_manager.py list

# 3. Restore from backup (if available)
python3 scripts/env_backup_manager.py restore .env_TIMESTAMP.backup

# 4. Or manually fix Auth0 client secret
python3 scripts/safe_env_editor.py .env --set AUTH0_CLIENT_SECRET "your-real-secret"

# 5. Restart backend
pkill -f uvicorn && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
```

### Complete Environment File Loss

```bash
# 1. Check for any backups
python3 scripts/env_backup_manager.py list

# 2. Restore latest backup if available
python3 scripts/env_backup_manager.py restore <latest-backup>

# 3. If no backups, start from template
cp .env.example .env
python3 scripts/safe_env_editor.py .env  # Interactive editing

# 4. Validate configuration
python3 -c "from app.core.secret_manager import SecretManager; sm = SecretManager('.env'); print(sm.validate_basic())"
```

## 🛠️ Daily Operations

### Creating Backups

```bash
# Manual backup with reason
python3 scripts/env_backup_manager.py backup .env --reason "before-auth0-update"

# List all backups
python3 scripts/env_backup_manager.py list

# Restore specific backup
python3 scripts/env_backup_manager.py restore .env_20240820_143022.backup
```

### Safe Environment Editing

```bash
# Interactive editing with validation
python3 scripts/safe_env_editor.py .env

# Quick value update
python3 scripts/safe_env_editor.py .env --set AUTH0_CLIENT_SECRET "new-secret"

# Bulk update (prompts for each)
python3 scripts/safe_env_editor.py .env --interactive
```

### Monitoring and Validation

```bash
# Check environment health
curl http://localhost:8000/secrets/validate

# Comprehensive validation report
python3 -c "
from app.core.secret_manager import SecretManager
import json
sm = SecretManager('.env')
report = sm.get_validation_report()
print(json.dumps(report, indent=2))
"

# Monitor file changes (daemon mode)
python3 scripts/env_file_monitor.py --daemon

# Check critical secrets status (masked)
python3 -c "
from app.core.secret_manager import SecretManager
sm = SecretManager('.env')
status = sm.get_critical_secrets_status()
for key, value in status.items():
    print(f'{key}: {value}')
"
```

## 🔧 System Components

### 1. Environment Backup Manager (`scripts/env_backup_manager.py`)

**Features**:
- Timestamped backups with metadata
- Integrity verification using SHA256 hashes
- Placeholder value detection
- Automatic cleanup (keeps last 50 backups)
- Backup restoration with safety checks

**Commands**:
```bash
python3 scripts/env_backup_manager.py backup <file> [--reason "description"]
python3 scripts/env_backup_manager.py list
python3 scripts/env_backup_manager.py restore <backup-file>
```

### 2. Secret Management System (`app/core/secret_manager.py`)

**Validation Levels**:
- **Basic**: Presence and placeholder checks
- **Strict**: Format validation and connectivity tests  
- **Paranoid**: Comprehensive security analysis

**Critical Secrets Monitored**:
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`
- `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`

**Forbidden Placeholders Detected**:
- `your-auth0-client-secret`, `placeholder`, `change-me`
- `your-database-url`, `localhost` (in production)
- `your-jwt-secret`, `secret-key`

### 3. Git Hooks Protection (`scripts/setup_git_hooks.sh`)

**Pre-commit Hook**:
- Prevents `.env` file commits
- Detects secret patterns in staged changes
- Interactive warnings for potential secrets

**Pre-push Hook**:
- Validates environment before push
- Checks for `.env` files in repository history
- Ensures environment health

### 4. File Monitoring System (`scripts/env_file_monitor.py`)

**Real-time Monitoring**:
- Watches `.env` files for changes
- Creates automatic backups on modification
- Validates changes immediately
- Supports daemon mode for continuous monitoring

### 5. Safe Environment Editor (`scripts/safe_env_editor.py`)

**Safe Editing Features**:
- Pre-edit backup creation
- Interactive value setting with validation
- Secure value masking in display
- Rollback on validation failure

## 🔐 Security Features

### Multi-Layer Protection

1. **File Level**: Git hooks prevent accidental commits
2. **Application Level**: Startup validation blocks invalid configs
3. **Runtime Level**: Health endpoints monitor secret status
4. **Storage Level**: Encrypted backups with integrity checks

### Environment-Specific Security

**Development**:
- Warnings for invalid secrets
- Allows startup with issues (with warnings)
- Basic validation sufficient

**Production**:
- Hard failures for invalid secrets
- Blocks startup with configuration issues
- Paranoid validation required
- Connectivity tests mandatory

### Audit Trail

- All backups logged with timestamps and reasons
- File modifications tracked with automatic backup creation
- Git commits enhanced with configuration change markers
- Health check history via API endpoints

## 📊 Monitoring and Alerting

### Health Check Endpoints

```bash
# Basic application health
curl http://localhost:8000/health

# Secret validation status
curl http://localhost:8000/secrets/validate

# Complete readiness check
curl http://localhost:8000/ready
```

### Response Format

```json
{
  "status": "healthy|unhealthy|error",
  "secrets_valid": true,
  "critical_issues": 0,
  "warnings": 2,
  "last_check": "2024-08-20T11:09:10",
  "critical_secrets": {
    "AUTH0_CLIENT_SECRET": "SET (9CnJ...Ett2)",
    "DATABASE_URL": "SET (post...pper)",
    "JWT_SECRET_KEY": "PLACEHOLDER"
  }
}
```

### Metrics for Alerting

**Critical Alerts** (Immediate Response):
- Secret validation failures
- Missing critical secrets  
- Placeholder secrets detected in production
- Backup creation failures

**Warning Alerts** (High Priority):
- Weak JWT secrets
- Development values in production
- Auth0 connectivity issues

**Info Alerts** (Medium Priority):
- Backup cleanup operations
- Environment file modifications
- Successful secret rotations

## 🔄 Secret Rotation Procedures

### Auth0 Client Secret Rotation

```bash
# 1. Create backup
python3 scripts/env_backup_manager.py backup .env --reason "auth0-secret-rotation"

# 2. Update Auth0 Dashboard with new secret

# 3. Update local environment
python3 scripts/safe_env_editor.py .env --set AUTH0_CLIENT_SECRET "new-secret"

# 4. Validate connectivity
curl http://localhost:8000/secrets/validate

# 5. Restart application
# Backend will be restarted automatically due to --reload flag
```

### Database URL Rotation

```bash
# 1. Backup current environment
python3 scripts/env_backup_manager.py backup .env --reason "database-url-rotation"

# 2. Update database credentials in your database provider

# 3. Update environment file
python3 scripts/safe_env_editor.py .env --set DATABASE_URL "new-connection-string"

# 4. Test connectivity
python3 -c "
import asyncio
from app.core.secret_manager import SecretManager
async def test():
    sm = SecretManager('.env')
    valid, errors = await sm.validate_connectivity()
    print(f'Connectivity: {\"VALID\" if valid else \"INVALID\"}')
    if errors: print(f'Errors: {errors}')
asyncio.run(test())
"

# 5. Restart application
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: "Validation: FAILED - JWT_SECRET_KEY contains forbidden placeholder"
**Solution**: 
```bash
# Generate new JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Update environment
python3 scripts/safe_env_editor.py .env --set JWT_SECRET_KEY "generated-secret"
```

**Issue**: "Auth0 connectivity test failed"
**Solutions**:
```bash
# Check Auth0 domain accessibility
curl https://dev-g8trhgbfdq2sk2m8.us.auth0.com/.well-known/openid_configuration

# Verify Auth0 client credentials in dashboard
# Update client secret if rotated
python3 scripts/safe_env_editor.py .env --set AUTH0_CLIENT_SECRET "correct-secret"
```

**Issue**: "Backup creation failed - permission denied"
**Solution**:
```bash
# Fix permissions
chmod 755 .env_backups
chmod +x scripts/*.py

# Create backup manually
mkdir -p .env_backups
cp .env .env_backups/.env_$(date +%Y%m%d_%H%M%S).backup
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Set debug environment variable
export DEBUG=true

# Run validation with detailed output
python3 -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from app.core.secret_manager import SecretManager
sm = SecretManager('.env')
print(sm.get_validation_report())
"
```

### Log Analysis

Check application logs for secret validation issues:

```bash
# Backend logs (if using systemd)
journalctl -u your-backend-service -f

# Docker logs
docker logs your-backend-container --tail 100 -f

# Direct uvicorn logs
tail -f uvicorn.log | grep -i "secret\|validation\|auth0"
```

## 📈 Best Practices

### Development Environment

1. **Never commit `.env` files** - Git hooks will prevent this
2. **Use placeholders in examples** - `.env.example` should have dummy values
3. **Validate before testing** - Run validation before major testing
4. **Create backups before changes** - Always backup before environment changes

### Production Environment

1. **Use external secret management** - Consider AWS Secrets Manager, Azure Key Vault
2. **Enable paranoid validation** - Set `ENVIRONMENT=production` for strict checks
3. **Monitor secret health** - Set up alerts on validation endpoints
4. **Rotate secrets regularly** - Follow security best practices for rotation

### Team Collaboration

1. **Share procedures, not secrets** - Document processes, not actual secret values
2. **Use different Auth0 tenants** - Separate development and production Auth0 tenants
3. **Backup before merges** - Create backups before pulling/merging changes
4. **Validate after deployments** - Always check secret health after deployments

## 🚀 Advanced Configuration

### Custom Validation Patterns

Edit `app/core/secret_manager.py` to add custom validation:

```python
self.validation_patterns.update({
    'CUSTOM_API_KEY': r'^[A-Z0-9]{32}$',
    'WEBHOOK_SECRET': r'^whsec_[a-zA-Z0-9]{32}$'
})

self.forbidden_placeholders.update({
    'CUSTOM_API_KEY': ['your-api-key', 'placeholder-key']
})
```

### Environment-Specific Settings

```python
# Different validation for different environments
if os.getenv('ENVIRONMENT') == 'staging':
    # Custom staging validation rules
    pass
```

### Integration with External Systems

```python
# Add custom connectivity tests
async def _test_custom_service(self, api_key: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.your-service.com/health",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return response.status_code == 200
    except:
        return False
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Weekly**:
- Review backup cleanup logs
- Check validation endpoint health
- Verify Git hooks are working

**Monthly**:
- Audit secret rotation schedules
- Review validation patterns for new requirements
- Update documentation for new team members

**Quarterly**:
- Evaluate secret management tools
- Review security patterns and update validation
- Conduct secret rotation drills

### Getting Help

1. **Check this documentation first**
2. **Run validation diagnostics**: `curl http://localhost:8000/secrets/validate`
3. **Review recent backups**: `python3 scripts/env_backup_manager.py list`
4. **Check application logs** for detailed error messages
5. **Verify Git hooks are installed**: `ls -la ../.git/hooks/`

### System Updates

When updating the secure environment management system:

```bash
# 1. Backup current state
python3 scripts/env_backup_manager.py backup .env --reason "before-system-update"

# 2. Update system files
git pull origin main

# 3. Reinstall components if needed
./scripts/setup_secure_env_system.sh

# 4. Validate everything still works
curl http://localhost:8000/secrets/validate
```

---

**Remember**: This system is designed to prevent the exact regression that occurred on August 20th, 2024, where the Auth0 client secret was accidentally replaced with a placeholder value. The multi-layered protection ensures this type of incident cannot happen again.