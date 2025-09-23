"""
Repair endpoint for fixing missing database tables.
"""

from fastapi import APIRouter, HTTPException
import asyncpg
import os
from typing import Dict, Any

router = APIRouter()

@router.post("/execute-final-repair", response_model=Dict[str, Any])
async def execute_final_repair():
    """
    Execute the final repair for missing tables.
    Emergency repair endpoint - no auth required for this critical fix.
    """

    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")

        # Convert to asyncpg format if needed
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgres://', 1)

        # Connect using asyncpg for DDL operations
        conn = await asyncpg.connect(database_url)

        # Define the 3 missing tables with correct FK types
        tables_to_create = [
            ("module_configurations", """
                CREATE TABLE IF NOT EXISTS module_configurations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    config JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """),
            ("module_usage_logs", """
                CREATE TABLE IF NOT EXISTS module_usage_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    module_id UUID NOT NULL,
                    organisation_id UUID NOT NULL,
                    user_id UUID,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """),
            ("sector_modules", """
                CREATE TABLE IF NOT EXISTS sector_modules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    sector VARCHAR(100) NOT NULL,
                    module_id UUID NOT NULL,
                    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
        ]

        # Execute table creation
        results = {}
        success_count = 0

        for table_name, create_sql in tables_to_create:
            try:
                await conn.execute(create_sql)
                results[table_name] = {"status": "created", "error": None}
                success_count += 1
            except Exception as e:
                results[table_name] = {"status": "failed", "error": str(e)}

        # Verify tables exist
        verification_result = await conn.fetch("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename IN ('module_configurations', 'module_usage_logs', 'sector_modules')
            ORDER BY tablename
        """)

        created_tables = [row['tablename'] for row in verification_result]

        # Get total table count
        total_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM pg_tables
            WHERE schemaname = 'public'
        """)

        await conn.close()

        return {
            "success": success_count == 3,
            "tables_processed": 3,
            "tables_created": success_count,
            "total_tables_in_db": total_count,
            "created_tables": created_tables,
            "results": results,
            "message": f"Repair completed: {success_count}/3 tables created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Repair failed: {str(e)}")