#!/bin/bash

# Database migration script for Railway deployment
set -e

echo "Running database migrations..."
echo "Database URL: ${DATABASE_URL:0:20}..." # Show first 20 chars only for security

# Check if database is reachable
echo "Testing database connection..."
python3 -c "
import asyncio
import asyncpg
import sys
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'), timeout=10.0)
        await conn.execute('SELECT 1')
        await conn.close()
        print('Database connection successful')
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(test_connection())
if not result:
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "Database is reachable, running migrations..."
    alembic upgrade head
    echo "Migrations completed successfully"
else
    echo "Database is not reachable, skipping migrations"
    exit 1
fi