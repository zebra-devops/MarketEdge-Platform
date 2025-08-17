# Super Admin Setup Guide

## Overview

This guide provides instructions for adding Matt Lindop as a super admin user in the MarketEdge platform database.

## Prerequisites

1. **Database Access**: You need the PostgreSQL connection string for the production database
2. **Python Environment**: Python 3.8+ with required packages
3. **Network Access**: Ability to connect to the production database

## Quick Setup

### 1. Install Dependencies

```bash
# If using the main project environment
cd /Users/matt/Sites/MarketEdge
source app/venv/bin/activate  # or your virtual environment

# Or install standalone requirements
pip install -r migration_requirements.txt
```

### 2. Set Database URL

Export the database URL as an environment variable:

```bash
# For Render deployment
export DATABASE_URL="postgresql://username:password@hostname:port/database"

# The current production URL should be:
# postgresql://marketedge_platform_user:xxxxx@dpg-xxxxx-a.oregon-postgres.render.com/marketedge_platform
```

### 3. Run the Migration

```bash
python add_super_admin_migration.py
```

## What the Migration Does

### 1. Creates Zebra Associates Organization
- **Name**: Zebra Associates
- **Industry**: Consulting
- **Subscription**: Enterprise
- **Rate Limits**: High limits (10,000/hour, 1,000 burst)
- **Status**: Active

### 2. Creates Matt Lindop User
- **Email**: matt.lindop@zebra.associates
- **Name**: Matt Lindop
- **Legacy Role**: admin (for backward compatibility)
- **Status**: Active
- **Organization**: Zebra Associates

### 3. Sets Up Hierarchical Permissions
- **Hierarchy Node**: Organization-level for Zebra Associates
- **Enhanced Role**: super_admin (platform-wide access)
- **Assignment**: Primary and active
- **Permissions**: Full platform access

### 4. Verification
- Confirms user creation
- Validates organization assignment
- Verifies hierarchy assignment
- Checks super_admin role assignment

## Safety Features

### Data Protection
- **Idempotent**: Can be run multiple times safely
- **Existence Checks**: Won't duplicate existing data
- **Transaction Safety**: Full rollback on any error
- **Graceful Handling**: Continues if some data already exists

### Production Safety
- **Connection Testing**: Verifies database connectivity first
- **Production Confirmation**: Asks for confirmation on production databases
- **Comprehensive Logging**: Detailed logs with timestamps
- **Error Handling**: Clear error messages and rollback on failure

## Usage Examples

### Basic Usage
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
python add_super_admin_migration.py
```

### With Logging
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
python add_super_admin_migration.py 2>&1 | tee migration.log
```

### Testing Connection Only
```python
from add_super_admin_migration import test_database_connection, get_database_url
database_url = get_database_url()
test_database_connection(database_url)
```

## Expected Output

```
2025-08-17 10:00:00 - INFO - ============================================================
2025-08-17 10:00:00 - INFO - STARTING SUPER ADMIN MIGRATION
2025-08-17 10:00:00 - INFO - ============================================================
2025-08-17 10:00:00 - INFO - Using database: dpg-xxxxx-a.oregon-postgres.render.com
2025-08-17 10:00:00 - INFO - Testing database connection...
2025-08-17 10:00:00 - INFO - ✅ Database connection successful
2025-08-17 10:00:00 - INFO - PostgreSQL version: PostgreSQL 15.4
2025-08-17 10:00:00 - INFO - Creating Zebra Associates organization...
2025-08-17 10:00:00 - INFO - ✅ Created organization: Zebra Associates (ID: xxxx)
2025-08-17 10:00:00 - INFO - Creating Matt Lindop user...
2025-08-17 10:00:00 - INFO - ✅ Created user: matt.lindop@zebra.associates (ID: xxxx)
2025-08-17 10:00:00 - INFO - Creating organization hierarchy node...
2025-08-17 10:00:00 - INFO - ✅ Created hierarchy node: Zebra Associates (ID: xxxx)
2025-08-17 10:00:00 - INFO - Creating user hierarchy assignment...
2025-08-17 10:00:00 - INFO - ✅ Created hierarchy assignment with super_admin role (ID: xxxx)
2025-08-17 10:00:00 - INFO - Verifying super admin setup...
2025-08-17 10:00:00 - INFO - ✅ User verified: matt.lindop@zebra.associates (Matt Lindop) - Role: admin - Org: Zebra Associates
2025-08-17 10:00:00 - INFO - ✅ Hierarchy assignment verified: super_admin role in Zebra Associates (organization)
2025-08-17 10:00:00 - INFO - ============================================================
2025-08-17 10:00:00 - INFO - ✅ SUPER ADMIN MIGRATION COMPLETED SUCCESSFULLY
2025-08-17 10:00:00 - INFO - ============================================================
2025-08-17 10:00:00 - INFO - Organization: Zebra Associates (ID: xxxx)
2025-08-17 10:00:00 - INFO - User: matt.lindop@zebra.associates (ID: xxxx)
2025-08-17 10:00:00 - INFO - Hierarchy: Zebra Associates (ID: xxxx)
2025-08-17 10:00:00 - INFO - Super Admin Access: GRANTED with super_admin role
2025-08-17 10:00:00 - INFO - ============================================================
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify network connectivity
   - Confirm database credentials

2. **Permission Denied**
   - Ensure database user has CREATE/INSERT permissions
   - Check if connecting to correct database

3. **Data Already Exists**
   - This is normal - script handles existing data gracefully
   - Check logs for specific details

### Getting Database URL

For Render PostgreSQL:
1. Go to Render Dashboard
2. Navigate to your PostgreSQL instance
3. Copy the "External Database URL"
4. Use this as your DATABASE_URL

## Verification

After running the migration, you can verify the setup:

### 1. Check User Exists
```sql
SELECT u.email, u.first_name, u.last_name, u.role, o.name as organization
FROM users u 
JOIN organisations o ON u.organisation_id = o.id 
WHERE u.email = 'matt.lindop@zebra.associates';
```

### 2. Check Super Admin Role
```sql
SELECT uha.role, oh.name, oh.level
FROM user_hierarchy_assignments uha
JOIN organization_hierarchy oh ON uha.hierarchy_node_id = oh.id
JOIN users u ON uha.user_id = u.id
WHERE u.email = 'matt.lindop@zebra.associates' AND uha.is_active = true;
```

### 3. Check Organization
```sql
SELECT name, industry_type, subscription_plan, rate_limit_per_hour
FROM organisations 
WHERE name = 'Zebra Associates';
```

## Security Notes

- The super_admin role provides platform-wide access
- This includes access to all organizations and their data
- Use this access responsibly and in accordance with data protection policies
- Consider implementing additional audit logging for super admin actions

## Support

If you encounter issues:
1. Check the migration log file for detailed error information
2. Verify database connectivity and credentials
3. Ensure all required database tables exist (run latest migrations first)
4. Contact the development team if problems persist