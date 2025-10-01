# Deployment Scripts

This directory contains scripts to assist with safe production deployment procedures.

## CSRF Protection Enablement

**Script**: `csrf-enable.sh`

### Purpose

Safely enable CSRF protection in production after running smoke tests. This script implements the kill-switch deployment procedure to minimize risk.

### Kill-Switch Deployment Procedure

The CSRF protection should always be deployed using a two-step process:

1. **Deploy with CSRF Disabled** (5 minutes)
2. **Enable CSRF After Smoke Test** (using this script)

This ensures that if there are any issues with the CSRF implementation, the system remains operational while you troubleshoot.

### Usage

```bash
# Interactive mode (recommended)
./scripts/deployment/csrf-enable.sh

# Specify custom .env file
./scripts/deployment/csrf-enable.sh /path/to/.env

# Specify custom log file location
./scripts/deployment/csrf-enable.sh .env /var/log/custom/app.log
```

### Step-by-Step Process

#### Step 1: Deploy with CSRF Disabled (5 minutes)

```bash
# In production .env
CSRF_ENABLED=False

# Deploy application
git pull origin main
systemctl restart marketedge-backend  # or your deployment command

# Run 5-minute smoke test
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/auth/login -d '{"code":"test","redirect_uri":"..."}'
curl -X POST http://localhost:8000/api/v1/auth/logout

# Monitor logs for errors
tail -f /var/log/marketedge/app.log
```

#### Step 2: Enable CSRF After Smoke Test

```bash
# Run the enablement script
./scripts/deployment/csrf-enable.sh .env

# Output:
# 🔒 Enabling CSRF Protection
# ===========================
# Env file: .env
#
# Current CSRF_ENABLED: False
#
# Enable CSRF protection? (yes/no): yes
#
# Updating .env...
# ✅ Updated CSRF_ENABLED=True
#
# Restarting backend service...
# ⚠️  Manual restart required (adjust script for your deployment)
#
# Monitor CSRF validation logs:
# tail -f /var/log/marketedge/app.log | grep csrf
#
# ✅ CSRF protection enabled
#    Watch logs for 5 minutes to ensure no false positives
```

#### Step 3: Restart Backend

```bash
# Restart using your deployment method
systemctl restart marketedge-backend
# OR
supervisorctl restart marketedge
# OR
pm2 restart marketedge
# OR
docker-compose restart backend
```

#### Step 4: Monitor CSRF Validation

```bash
# Monitor logs for CSRF validation
tail -f /var/log/marketedge/app.log | grep csrf_validation

# Look for:
# - csrf_validation_success: Normal operation
# - csrf_validation_failed: Investigate immediately
# - csrf_token_mismatch: Check frontend integration
```

### Rollback Procedure

If CSRF causes issues in production:

```bash
# Option 1: Immediate rollback via environment variable
# Edit .env
CSRF_ENABLED=False
systemctl restart marketedge-backend

# Option 2: Restore backup .env (created by script)
cp .env.bak .env
systemctl restart marketedge-backend

# Option 3: Revert commit
git revert <csrf-commit-hash>
git push origin main
# Deploy reverted version
```

### Script Features

- **Current status display**: Shows current CSRF_ENABLED value
- **Interactive confirmation**: Requires "yes" to proceed (prevents accidents)
- **Automatic backup**: Creates `.env.bak` before modifying
- **Safe updates**: Uses `sed` to precisely update CSRF_ENABLED
- **Monitoring guidance**: Provides log monitoring commands
- **Restart instructions**: Shows how to restart the service

### Customization

To automate the restart for your deployment environment, edit the script:

```bash
# Line 36-43 in csrf-enable.sh
# Uncomment and customize the appropriate command:

# Systemd
systemctl restart marketedge-backend

# Supervisor
supervisorctl restart marketedge

# PM2
pm2 restart marketedge

# Docker Compose
docker-compose restart backend
```

### Environment Requirements

- `bash` shell
- `sed` command
- `.env` file exists with `CSRF_ENABLED` variable
- Appropriate permissions to restart the service

### Security Considerations

1. **Kill-switch is critical**: Never skip the two-step deployment
2. **Monitor logs**: Watch for 5+ minutes after enabling
3. **Test in staging first**: Always test the procedure in staging
4. **Have rollback ready**: Know how to quickly disable if needed
5. **Coordinate with team**: Notify team before enabling in production

### Testing the Script

Test the script in a development environment first:

```bash
# Create test .env
echo "CSRF_ENABLED=False" > test.env

# Run script
./scripts/deployment/csrf-enable.sh test.env

# Verify changes
grep CSRF_ENABLED test.env
# Should output: CSRF_ENABLED=True

# Verify backup created
ls -la test.env.bak
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Enable CSRF Protection

on:
  workflow_dispatch:
    inputs:
      confirm:
        description: 'Type YES to enable CSRF protection'
        required: true

jobs:
  enable-csrf:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Verify confirmation
        if: github.event.inputs.confirm != 'YES'
        run: |
          echo "Confirmation not provided"
          exit 1

      - name: Enable CSRF
        run: |
          ssh production "cd /app && ./scripts/deployment/csrf-enable.sh .env"

      - name: Restart service
        run: |
          ssh production "systemctl restart marketedge-backend"

      - name: Monitor logs
        run: |
          ssh production "timeout 60 tail -f /var/log/marketedge/app.log | grep csrf" || true
```

## References

- [CSRF Protection Implementation](../../docs/CSRF_SECURITY_IMPLEMENTATION.md)
- [Deployment Safety Documentation](../../docs/CSRF_SECURITY_IMPLEMENTATION.md#deployment-safety)
- [Kill-Switch Procedure](../../docs/CSRF_SECURITY_IMPLEMENTATION.md#kill-switch-procedure)
