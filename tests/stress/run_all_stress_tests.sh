#!/bin/bash
# Master script to run all stress tests
# Run with: bash run_all_stress_tests.sh

PROJECT_DIR="/home/wow/Projects/sale-sofia"
STRESS_DIR="$PROJECT_DIR/tests/stress"
cd "$PROJECT_DIR"

RESULTS_FILE="$STRESS_DIR/stress_test_results.md"

# Initialize results
cat > "$RESULTS_FILE" <<EOF
# Stress Test Results

**Date**: $(date)
**Working Directory**: $PROJECT_DIR

---

EOF

echo "Starting stress tests..."
echo "Results will be written to: $RESULTS_FILE"
echo ""

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    pkill -9 -f "proxy-scraper-checker" 2>/dev/null || true
    pkill -9 -f "mubeng" 2>/dev/null || true
    pkill -9 -f "celery.*worker" 2>/dev/null || true
    sleep 2
}

# Ensure clean state
cleanup

# Test 1: PSC SIGTERM
echo "========================================" | tee -a "$RESULTS_FILE"
echo "Running Test 1: PSC SIGTERM" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
bash "$STRESS_DIR/test1_psc_sigterm.sh" 2>&1 | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

cleanup

# Test 2: PSC SIGKILL
echo "========================================" | tee -a "$RESULTS_FILE"
echo "Running Test 2: PSC SIGKILL" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
bash "$STRESS_DIR/test2_psc_sigkill.sh" 2>&1 | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

cleanup

# Test 3: Celery + Mubeng
echo "========================================" | tee -a "$RESULTS_FILE"
echo "Running Test 3: Celery + Mubeng Integration" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
python "$STRESS_DIR/test3_celery_mubeng.py" 2>&1 | tee -a "$RESULTS_FILE"
TEST3_RESULT=$?
echo "" | tee -a "$RESULTS_FILE"

cleanup

# Test 5: Mid-task kill (CRITICAL)
echo "========================================" | tee -a "$RESULTS_FILE"
echo "Running Test 5: Mid-Task Kill (CRITICAL)" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
python "$STRESS_DIR/test5_mid_task_kill.py" 2>&1 | tee -a "$RESULTS_FILE"
TEST5_RESULT=$?
echo "" | tee -a "$RESULTS_FILE"

cleanup

# Summary
echo "" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
echo "SUMMARY" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

if [ $TEST3_RESULT -eq 0 ] && [ $TEST5_RESULT -eq 0 ]; then
    echo "All critical tests PASSED" | tee -a "$RESULTS_FILE"
elif [ $TEST5_RESULT -ne 0 ]; then
    echo "CRITICAL FAILURE: Test 5 failed - mubeng orphan issue detected!" | tee -a "$RESULTS_FILE"
    echo "Action required: Fix subprocess cleanup in check_proxy_chunk_task" | tee -a "$RESULTS_FILE"
else
    echo "Some tests failed - review results above" | tee -a "$RESULTS_FILE"
fi

echo "" | tee -a "$RESULTS_FILE"
echo "Full results saved to: $RESULTS_FILE"
