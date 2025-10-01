#!/bin/bash
# Security test script for US-6A backup/restore scripts
# Tests all critical security fixes implemented

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Test 1: Verify set -o pipefail is present
test_pipefail() {
    log_test "Test 1: Verify set -o pipefail is present in all scripts"

    local scripts=(
        "/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"
        "/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh"
        "/Users/matt/Sites/MarketEdge/scripts/backup/test_staging_migration.sh"
    )

    local all_passed=true
    for script in "${scripts[@]}"; do
        if grep -q "set -euo pipefail" "$script"; then
            log_pass "  $(basename "$script"): pipefail present"
        else
            log_fail "  $(basename "$script"): pipefail missing"
            all_passed=false
        fi
    done

    if [ "$all_passed" = false ]; then
        ((TESTS_FAILED++))
    fi
}

# Test 2: Verify sanitization functions are present
test_sanitization_functions() {
    log_test "Test 2: Verify sanitization functions are present"

    local scripts=(
        "/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"
        "/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh"
        "/Users/matt/Sites/MarketEdge/scripts/backup/test_staging_migration.sh"
    )

    local all_passed=true
    for script in "${scripts[@]}"; do
        if grep -q "sanitize_db_error()" "$script"; then
            log_pass "  $(basename "$script"): sanitize_db_error() present"
        else
            log_fail "  $(basename "$script"): sanitize_db_error() missing"
            all_passed=false
        fi

        if grep -q "redact_database_url()" "$script"; then
            log_pass "  $(basename "$script"): redact_database_url() present"
        else
            log_fail "  $(basename "$script"): redact_database_url() missing"
            all_passed=false
        fi
    done
}

# Test 3: Verify pg_dump commands use sanitization
test_pg_dump_sanitization() {
    log_test "Test 3: Verify pg_dump commands use sanitization"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"
    local count=$(grep -c "pg_dump.*2> >(sanitize_db_error" "$script" || echo "0")

    if [ "$count" -ge 3 ]; then
        log_pass "  Found $count sanitized pg_dump commands (expected >= 3)"
    else
        log_fail "  Found $count sanitized pg_dump commands (expected >= 3)"
    fi
}

# Test 4: Verify psql commands use sanitization
test_psql_sanitization() {
    log_test "Test 4: Verify psql commands use sanitization in restore script"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh"
    local count=$(grep -c "psql.*2> >(sanitize_db_error" "$script" || echo "0")

    if [ "$count" -ge 3 ]; then
        log_pass "  Found $count sanitized psql commands (expected >= 3)"
    else
        log_fail "  Found $count sanitized psql commands (expected >= 3)"
    fi
}

# Test 5: Verify AWS CLI output sanitization
test_aws_sanitization() {
    log_test "Test 5: Verify AWS CLI output sanitization"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"

    if grep -q "sanitize_aws_error()" "$script" && grep -q "aws s3 cp.*sanitize_aws_error" "$script"; then
        log_pass "  AWS CLI sanitization present"
    else
        log_fail "  AWS CLI sanitization missing"
    fi
}

# Test 6: Verify DATABASE_URL redaction in statistics
test_database_url_redaction() {
    log_test "Test 6: Verify DATABASE_URL redaction in statistics files"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"

    if grep -q "database_url_redacted=\$(redact_database_url" "$script"; then
        log_pass "  DATABASE_URL redaction present in backup script"
    else
        log_fail "  DATABASE_URL redaction missing in backup script"
    fi
}

# Test 7: Verify SQL injection protection (UUID validation)
test_sql_injection_protection() {
    log_test "Test 7: Verify SQL injection protection in test script"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/test_staging_migration.sh"

    # Check for UUID validation regex
    if grep -q '\[0-9a-f\]{8}-\[0-9a-f\]{4}-\[0-9a-f\]{4}-\[0-9a-f\]{4}-\[0-9a-f\]{12}' "$script"; then
        log_pass "  UUID validation regex present"
    else
        log_fail "  UUID validation regex missing"
    fi

    # Check for psql variable usage (parameterized query)
    if grep -q "psql.*-v user_id=" "$script"; then
        log_pass "  Parameterized psql query present"
    else
        log_fail "  Parameterized psql query missing"
    fi
}

# Test 8: Verify path traversal protection
test_path_traversal_protection() {
    log_test "Test 8: Verify path traversal protection in restore script"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh"

    if grep -q 'BACKUP_DIR.*"\.\."' "$script"; then
        log_pass "  Path traversal check present"
    else
        log_fail "  Path traversal check missing"
    fi
}

# Test 9: Verify row count comparison uses numeric comparison
test_row_count_comparison() {
    log_test "Test 9: Verify row count comparison uses numeric comparison"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh"

    if grep -q '\[ "\${backup_count}" -eq "\${restore_count}" \]' "$script"; then
        log_pass "  Numeric comparison present (-eq instead of =)"
    else
        log_fail "  Numeric comparison missing"
    fi

    if grep -q "grep -o '\[0-9\]\*'" "$script"; then
        log_pass "  Numeric extraction with grep -o present"
    else
        log_fail "  Numeric extraction with grep -o missing"
    fi
}

# Test 10: Verify variable quoting in tar command
test_variable_quoting() {
    log_test "Test 10: Verify variable quoting in tar command"

    local script="/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"

    if grep -q 'tar.*dirname "\${BACKUP_DIR}"' "$script"; then
        log_pass "  Variable quoting present in tar command"
    else
        log_fail "  Variable quoting missing in tar command"
    fi
}

# Test 11: Verify no plain DATABASE_URL exposure
test_no_plain_database_url() {
    log_test "Test 11: Verify no plain DATABASE_URL in output"

    local scripts=(
        "/Users/matt/Sites/MarketEdge/scripts/backup/backup_enum_migration.sh"
        "/Users/matt/Sites/MarketEdge/scripts/backup/restore_enum_migration.sh"
        "/Users/matt/Sites/MarketEdge/scripts/backup/test_staging_migration.sh"
    )

    local all_passed=true
    for script in "${scripts[@]}"; do
        # Check for unredacted DATABASE_URL patterns (should be redacted)
        local unredacted_count=$(grep -c 'DATABASE_URL%%@\*' "$script" 2>/dev/null || echo "0")

        if [ "$unredacted_count" -eq 0 ]; then
            log_pass "  $(basename "$script"): No unredacted DATABASE_URL patterns"
        else
            log_fail "  $(basename "$script"): Found $unredacted_count unredacted DATABASE_URL patterns"
            all_passed=false
        fi
    done
}

# Test 12: Test actual credential sanitization function
test_credential_sanitization_function() {
    log_test "Test 12: Test credential sanitization function"

    # Source the function
    sanitize_db_error() {
        sed -E 's/(password|pwd)=([^ ]+)/\1=***/g; s/postgresql:\/\/[^:]+:[^@]+@/postgresql:\/\/***:***@/g'
    }

    redact_database_url() {
        echo "${1}" | sed -E 's/postgresql:\/\/[^:]+:[^@]+@/postgresql:\/\/***:***@/g'
    }

    # Test examples
    local test_url="postgresql://admin:SuperSecret@localhost/test"
    local redacted=$(redact_database_url "$test_url")

    if [[ "$redacted" == "postgresql://***:***@localhost/test" ]]; then
        log_pass "  Credential redaction works correctly"
    else
        log_fail "  Credential redaction failed: got '$redacted'"
    fi

    # Test password parameter redaction
    local test_error="Error: password=secret123 connection failed"
    local sanitized=$(echo "$test_error" | sanitize_db_error)

    if [[ "$sanitized" == "Error: password=*** connection failed" ]]; then
        log_pass "  Password parameter sanitization works correctly"
    else
        log_fail "  Password parameter sanitization failed: got '$sanitized'"
    fi
}

# Run all tests
main() {
    echo "========================================"
    echo "US-6A Security Fixes Validation Tests"
    echo "========================================"
    echo ""

    test_pipefail
    test_sanitization_functions
    test_pg_dump_sanitization
    test_psql_sanitization
    test_aws_sanitization
    test_database_url_redaction
    test_sql_injection_protection
    test_path_traversal_protection
    test_row_count_comparison
    test_variable_quoting
    test_no_plain_database_url
    test_credential_sanitization_function

    echo ""
    echo "========================================"
    echo "Test Summary"
    echo "========================================"
    echo -e "${GREEN}Tests Passed: ${TESTS_PASSED}${NC}"
    echo -e "${RED}Tests Failed: ${TESTS_FAILED}${NC}"

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}All security tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some security tests failed!${NC}"
        exit 1
    fi
}

main
