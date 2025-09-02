#!/bin/bash
# Production Database Fix Script for Render
# Fixes missing Base columns causing authentication 500 errors
# Critical for £925K Zebra Associates opportunity

set -e  # Exit on error

echo "🚀 MarketEdge Database Schema Fix - $(date)"
echo "📋 Fixing missing created_at/updated_at columns"
echo "🎯 Target: Production database on Render"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable not set"
    exit 1
fi

# Extract database connection info (for logging only)
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
echo "🗃️  Database host: $DB_HOST"
echo ""

# Function to run SQL and check result
run_sql() {
    local sql="$1"
    local description="$2"
    
    echo "🔧 $description"
    echo "   SQL: $sql"
    
    if psql "$DATABASE_URL" -c "$sql"; then
        echo "   ✅ Success"
    else
        echo "   ❌ Failed"
        return 1
    fi
    echo ""
}

# Function to check if column exists
column_exists() {
    local table="$1"
    local column="$2"
    
    result=$(psql "$DATABASE_URL" -t -c "
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '$table' 
            AND column_name = '$column'
        );
    " | xargs)
    
    [ "$result" = "t" ]
}

# Function to check if table exists
table_exists() {
    local table="$1"
    
    result=$(psql "$DATABASE_URL" -t -c "
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '$table'
        );
    " | xargs)
    
    [ "$result" = "t" ]
}

echo "🔍 Analyzing current schema..."

# Tables and their missing columns
declare -A MISSING_COLUMNS
MISSING_COLUMNS[feature_flag_overrides]="updated_at"
MISSING_COLUMNS[feature_flag_usage]="created_at updated_at"
MISSING_COLUMNS[module_usage_logs]="created_at updated_at"
MISSING_COLUMNS[admin_actions]="updated_at"
MISSING_COLUMNS[audit_logs]="created_at updated_at"
MISSING_COLUMNS[competitive_insights]="updated_at"
MISSING_COLUMNS[competitors]="updated_at"
MISSING_COLUMNS[market_alerts]="updated_at"
MISSING_COLUMNS[market_analytics]="updated_at"
MISSING_COLUMNS[pricing_data]="updated_at"

# Check current state and build fix list
declare -a FIXES_NEEDED
TOTAL_FIXES=0

for table in "${!MISSING_COLUMNS[@]}"; do
    if ! table_exists "$table"; then
        echo "⚠️  Table $table does not exist - skipping"
        continue
    fi
    
    echo "📊 Checking table: $table"
    
    for column in ${MISSING_COLUMNS[$table]}; do
        if ! column_exists "$table" "$column"; then
            echo "   ❌ Missing column: $column"
            FIXES_NEEDED+=("$table:$column")
            ((TOTAL_FIXES++))
        else
            echo "   ✅ Column exists: $column"
        fi
    done
    echo ""
done

if [ $TOTAL_FIXES -eq 0 ]; then
    echo "🎉 All columns are present! No fixes needed."
    echo "✅ Database schema is correct."
    exit 0
fi

echo "📋 Summary: $TOTAL_FIXES columns need to be added"
echo ""

# Confirm before proceeding
echo "🚨 PRODUCTION FIX CONFIRMATION"
echo "   This will modify the production database schema"
echo "   $TOTAL_FIXES columns will be added to existing tables"
echo ""
echo "   Press ENTER to continue or Ctrl+C to abort..."
read -r

echo "🔄 Starting database fixes..."
echo ""

# Begin transaction
run_sql "BEGIN;" "Starting transaction"

# Apply fixes
for fix in "${FIXES_NEEDED[@]}"; do
    IFS=':' read -r table column <<< "$fix"
    
    echo "🔧 Adding $column to $table"
    
    if [ "$column" = "created_at" ]; then
        sql="ALTER TABLE $table ADD COLUMN $column TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;"
    elif [ "$column" = "updated_at" ]; then
        sql="ALTER TABLE $table ADD COLUMN $column TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;"
    else
        echo "❌ Unknown column type: $column"
        psql "$DATABASE_URL" -c "ROLLBACK;"
        exit 1
    fi
    
    if ! run_sql "$sql" "Adding $column to $table"; then
        echo "❌ Failed to add column - rolling back"
        psql "$DATABASE_URL" -c "ROLLBACK;"
        exit 1
    fi
done

# Commit transaction
run_sql "COMMIT;" "Committing all changes"

echo "✅ All fixes applied successfully!"
echo ""

# Verification
echo "🔍 Verifying fixes..."
VERIFICATION_FAILED=0

for table in "${!MISSING_COLUMNS[@]}"; do
    if ! table_exists "$table"; then
        continue
    fi
    
    echo "📊 Verifying table: $table"
    
    for column in ${MISSING_COLUMNS[$table]}; do
        if column_exists "$table" "$column"; then
            echo "   ✅ Column verified: $column"
        else
            echo "   ❌ Column still missing: $column"
            ((VERIFICATION_FAILED++))
        fi
    done
    echo ""
done

if [ $VERIFICATION_FAILED -eq 0 ]; then
    echo "🎉 ALL FIXES VERIFIED SUCCESSFULLY!"
    echo "✅ Database schema is now correct"
    echo "🚀 Authentication should work properly"
    echo ""
    echo "💰 £925K Zebra Associates opportunity - UNBLOCKED!"
else
    echo "❌ $VERIFICATION_FAILED columns still missing after fixes"
    echo "🔄 Manual intervention may be required"
    exit 1
fi

echo "📊 Database fix completed at $(date)"
echo "✅ Ready for production traffic"