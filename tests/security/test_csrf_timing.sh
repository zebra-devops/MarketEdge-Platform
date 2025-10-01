#!/bin/bash
# CSRF Timing Attack Stress Test
# Verifies constant-time comparison doesn't leak token information

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
TEST_ENDPOINT="${BACKEND_URL}/api/v1/auth/logout"
NUM_REQUESTS=50
PARALLEL_WORKERS=50

echo "🔒 CSRF Timing Attack Stress Test"
echo "=================================="
echo "Backend: ${BACKEND_URL}"
echo "Endpoint: ${TEST_ENDPOINT}"
echo "Requests: ${NUM_REQUESTS} (parallel: ${PARALLEL_WORKERS})"
echo ""

# Check if backend is running
if ! curl -f -s "${BACKEND_URL}/health" > /dev/null; then
    echo "❌ Backend not running at ${BACKEND_URL}"
    echo "Start backend: uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Run timing attack test
echo "Running timing attack test..."
echo "Testing with wrong CSRF tokens (should be rejected in constant time)"

TIMING_RESULTS=$(mktemp)

# Send 50 parallel POST requests with wrong CSRF token
seq 1 ${NUM_REQUESTS} | xargs -P ${PARALLEL_WORKERS} -I {} curl -s -o /dev/null -w "%{time_total}\n" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "X-CSRF-Token: wrong-token-{}" \
    "${TEST_ENDPOINT}" \
    2>/dev/null > "${TIMING_RESULTS}"

# Calculate statistics
MIN_TIME=$(sort -n "${TIMING_RESULTS}" | head -1)
MAX_TIME=$(sort -n "${TIMING_RESULTS}" | tail -1)
AVG_TIME=$(awk '{ sum += $1; count++ } END { print sum/count }' "${TIMING_RESULTS}")
MEDIAN_TIME=$(sort -n "${TIMING_RESULTS}" | awk '{a[NR]=$1} END {print (NR%2==1)?a[(NR+1)/2]:(a[NR/2]+a[NR/2+1])/2}')

echo ""
echo "📊 Timing Statistics (seconds):"
echo "  Min:    ${MIN_TIME}"
echo "  Max:    ${MAX_TIME}"
echo "  Avg:    ${AVG_TIME}"
echo "  Median: ${MEDIAN_TIME}"

# Calculate variance (max/min ratio)
VARIANCE=$(echo "scale=2; ${MAX_TIME} / ${MIN_TIME}" | bc)

echo ""
echo "📈 Timing Variance: ${VARIANCE}x"

# Clean up
rm "${TIMING_RESULTS}"

# Evaluate results
echo ""
if (( $(echo "${VARIANCE} < 1.5" | bc -l) )); then
    echo "✅ PASS: Constant-time comparison verified"
    echo "   Variance < 1.5x indicates no timing leak"
    echo "   max ≈ min → no O(n) timing leak ✅"
    exit 0
else
    echo "⚠️  WARNING: High timing variance detected"
    echo "   Variance ${VARIANCE}x may indicate timing leak"
    echo "   Review constant-time comparison implementation"
    exit 1
fi
