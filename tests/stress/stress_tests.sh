#!/bin/bash
# Stress tests for proxy-scraper-checker and tool integration
# Working directory: /home/wow/Projects/sale-sofia

set -e

RESULTS_FILE="/home/wow/Projects/sale-sofia/stress_test_results.md"
PROJECT_DIR="/home/wow/Projects/sale-sofia"

cd "$PROJECT_DIR"

# Initialize results file
cat > "$RESULTS_FILE" <<'HEADER'
# Stress Test Results

**Date**: $(date)
**Working Directory**: /home/wow/Projects/sale-sofia

---

HEADER

echo "Starting stress tests..."
echo "Results will be written to: $RESULTS_FILE"

# Helper function to check for orphan processes
check_orphans() {
    local process_name=$1
    echo "=== Checking for orphan $process_name processes ===" | tee -a "$RESULTS_FILE"
    if pgrep -af "$process_name"; then
        echo "WARNING: Found orphan $process_name processes!" | tee -a "$RESULTS_FILE"
        pgrep -af "$process_name" | tee -a "$RESULTS_FILE"
        return 1
    else
        echo "OK: No orphan $process_name processes" | tee -a "$RESULTS_FILE"
        return 0
    fi
}

# Cleanup function
cleanup_all() {
    echo "=== Cleaning up all test processes ===" | tee -a "$RESULTS_FILE"
    pkill -9 -f "proxy-scraper-checker" 2>/dev/null || true
    pkill -9 -f "mubeng" 2>/dev/null || true
    pkill -9 -f "celery.*worker" 2>/dev/null || true
    sleep 2
}

# Initial cleanup
cleanup_all

# ========================================
# Test 1: PSC Quick Start/Stop (SIGTERM)
# ========================================
echo "" | tee -a "$RESULTS_FILE"
echo "## Test 1: PSC Quick Start/Stop (SIGTERM)" | tee -a "$RESULTS_FILE"
echo "**Objective**: Test graceful shutdown of proxy-scraper-checker" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "Starting PSC..." | tee -a "$RESULTS_FILE"
./proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker -o /tmp/psc_test.json &
PSC_PID=$!
echo "PSC started with PID: $PSC_PID" | tee -a "$RESULTS_FILE"

sleep 5

echo "Sending SIGTERM to PID $PSC_PID..." | tee -a "$RESULTS_FILE"
kill -SIGTERM $PSC_PID
wait $PSC_PID 2>/dev/null
EXIT_CODE=$?
echo "Exit code after SIGTERM: $EXIT_CODE" | tee -a "$RESULTS_FILE"

sleep 2
check_orphans "proxy-scraper"
TEST1_RESULT=$?

echo "" | tee -a "$RESULTS_FILE"
if [ $TEST1_RESULT -eq 0 ]; then
    echo "**Result**: PASS - PSC terminated gracefully, no orphans" | tee -a "$RESULTS_FILE"
else
    echo "**Result**: FAIL - Orphan processes found" | tee -a "$RESULTS_FILE"
fi
echo "" | tee -a "$RESULTS_FILE"

# ========================================
# Test 2: PSC Ungraceful Kill (SIGKILL)
# ========================================
echo "## Test 2: PSC Ungraceful Kill (SIGKILL)" | tee -a "$RESULTS_FILE"
echo "**Objective**: Test ungraceful shutdown of proxy-scraper-checker" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "Starting PSC..." | tee -a "$RESULTS_FILE"
./proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker -o /tmp/psc_kill.json &
PSC_PID=$!
echo "PSC started with PID: $PSC_PID" | tee -a "$RESULTS_FILE"

sleep 3

echo "Sending SIGKILL to PID $PSC_PID..." | tee -a "$RESULTS_FILE"
kill -9 $PSC_PID

sleep 2
check_orphans "proxy-scraper"
TEST2_RESULT=$?

echo "" | tee -a "$RESULTS_FILE"
if [ $TEST2_RESULT -eq 0 ]; then
    echo "**Result**: PASS - PSC killed, no orphans" | tee -a "$RESULTS_FILE"
else
    echo "**Result**: FAIL - Orphan processes found" | tee -a "$RESULTS_FILE"
fi
echo "" | tee -a "$RESULTS_FILE"

# ========================================
# Test 3: Integration - Celery + Mubeng Together
# ========================================
echo "## Test 3: Integration - Celery + Mubeng Together" | tee -a "$RESULTS_FILE"
echo "**Objective**: Test if mubeng processes are cleaned up when Celery worker stops" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "Starting Celery worker..." | tee -a "$RESULTS_FILE"
celery -A celery_app worker -Q celery,sale_sofia --loglevel=info --concurrency=2 &
CELERY_PID=$!
echo "Celery started with PID: $CELERY_PID" | tee -a "$RESULTS_FILE"

sleep 5

echo "Triggering proxy check task..." | tee -a "$RESULTS_FILE"
python <<'PYCODE' | tee -a "$RESULTS_FILE"
from proxies.tasks import check_proxy_chunk_task
import time

# Small chunk
chunk = [{'host': '1.1.1.1', 'port': 80, 'protocol': 'http'}]
result = check_proxy_chunk_task.delay(chunk)
print(f'Task ID: {result.id}')

for i in range(30):
    time.sleep(1)
    print(f'State: {result.state}')
    if result.ready():
        print(f'Result: {result.result}')
        break
PYCODE

echo "" | tee -a "$RESULTS_FILE"
echo "Checking for mubeng processes before Celery shutdown..." | tee -a "$RESULTS_FILE"
pgrep -af mubeng | tee -a "$RESULTS_FILE" || echo "No mubeng processes" | tee -a "$RESULTS_FILE"

echo "" | tee -a "$RESULTS_FILE"
echo "Stopping Celery gracefully with SIGTERM..." | tee -a "$RESULTS_FILE"
kill -SIGTERM $CELERY_PID
wait $CELERY_PID 2>/dev/null || true

sleep 3

check_orphans "mubeng"
TEST3_MUBENG=$?
check_orphans "celery"
TEST3_CELERY=$?

echo "" | tee -a "$RESULTS_FILE"
if [ $TEST3_MUBENG -eq 0 ] && [ $TEST3_CELERY -eq 0 ]; then
    echo "**Result**: PASS - All processes cleaned up properly" | tee -a "$RESULTS_FILE"
else
    echo "**Result**: FAIL - Orphan processes found after graceful shutdown" | tee -a "$RESULTS_FILE"
fi
echo "" | tee -a "$RESULTS_FILE"

# ========================================
# Test 4: Full Pipeline Under Load
# ========================================
echo "## Test 4: Full Pipeline Under Load" | tee -a "$RESULTS_FILE"
echo "**Objective**: Test full proxy scraping and checking pipeline" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "Starting Celery with beat..." | tee -a "$RESULTS_FILE"
celery -A celery_app worker --beat -Q celery,sale_sofia --loglevel=info --concurrency=4 &
CELERY_PID=$!
echo "Celery started with PID: $CELERY_PID" | tee -a "$RESULTS_FILE"

sleep 5

echo "Triggering chain task..." | tee -a "$RESULTS_FILE"
python <<'PYCODE' | tee -a "$RESULTS_FILE"
from proxies.tasks import scrape_and_check_chain_task
result = scrape_and_check_chain_task.delay()
print(f'Chain task started: {result.id}')
PYCODE

sleep 30

echo "" | tee -a "$RESULTS_FILE"
echo "=== Process state after 30 seconds ===" | tee -a "$RESULTS_FILE"
pgrep -af "celery|mubeng|proxy-scraper" | tee -a "$RESULTS_FILE" || echo "No processes found" | tee -a "$RESULTS_FILE"

echo "" | tee -a "$RESULTS_FILE"
echo "=== Queue state ===" | tee -a "$RESULTS_FILE"
echo -n "celery queue length: " | tee -a "$RESULTS_FILE"
redis-cli LLEN celery | tee -a "$RESULTS_FILE"
echo -n "sale_sofia queue length: " | tee -a "$RESULTS_FILE"
redis-cli LLEN sale_sofia | tee -a "$RESULTS_FILE"

echo "" | tee -a "$RESULTS_FILE"
echo "Killing all processes ungracefully (simulating crash)..." | tee -a "$RESULTS_FILE"
pkill -9 -f celery
pkill -9 -f mubeng
pkill -9 -f proxy-scraper

sleep 3

echo "" | tee -a "$RESULTS_FILE"
echo "=== Orphan check after ungraceful kill ===" | tee -a "$RESULTS_FILE"
check_orphans "celery|mubeng|proxy-scraper"
TEST4_RESULT=$?

echo "" | tee -a "$RESULTS_FILE"
if [ $TEST4_RESULT -eq 0 ]; then
    echo "**Result**: PASS - All processes killed, no orphans" | tee -a "$RESULTS_FILE"
else
    echo "**Result**: FAIL - Orphan processes persist after SIGKILL" | tee -a "$RESULTS_FILE"
fi
echo "" | tee -a "$RESULTS_FILE"

# ========================================
# Test 5: What happens when Celery dies mid-task?
# ========================================
echo "## Test 5: Celery Dies Mid-Task" | tee -a "$RESULTS_FILE"
echo "**Objective**: Test if mubeng processes become orphans when Celery is killed during task execution" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "Starting Celery worker..." | tee -a "$RESULTS_FILE"
celery -A celery_app worker -Q celery,sale_sofia --loglevel=info &
CELERY_PID=$!
echo "Celery started with PID: $CELERY_PID" | tee -a "$RESULTS_FILE"

sleep 5

echo "Starting task with larger chunk (will take longer)..." | tee -a "$RESULTS_FILE"
python <<'PYCODE' | tee -a "$RESULTS_FILE"
from proxies.tasks import check_proxy_chunk_task

# Larger chunk to take longer
chunk = [{'host': f'1.1.1.{i}', 'port': 80, 'protocol': 'http'} for i in range(50)]
result = check_proxy_chunk_task.delay(chunk)
print(f'Task ID: {result.id}')
PYCODE

TASK_ID=$(python -c "from proxies.tasks import check_proxy_chunk_task; chunk = [{'host': f'1.1.1.{i}', 'port': 80, 'protocol': 'http'} for i in range(50)]; result = check_proxy_chunk_task.delay(chunk); print(result.id)")

sleep 3

echo "" | tee -a "$RESULTS_FILE"
echo "Checking processes BEFORE killing Celery..." | tee -a "$RESULTS_FILE"
pgrep -af "celery|mubeng" | tee -a "$RESULTS_FILE" || echo "No processes" | tee -a "$RESULTS_FILE"

echo "" | tee -a "$RESULTS_FILE"
echo "Killing Celery with SIGKILL while task is running..." | tee -a "$RESULTS_FILE"
kill -9 $CELERY_PID

sleep 3

echo "" | tee -a "$RESULTS_FILE"
echo "Checking for orphan mubeng processes AFTER Celery kill..." | tee -a "$RESULTS_FILE"
check_orphans "mubeng"
TEST5_RESULT=$?

echo "" | tee -a "$RESULTS_FILE"
echo "Checking task state in Redis..." | tee -a "$RESULTS_FILE"
python <<'PYCODE' | tee -a "$RESULTS_FILE"
import redis
r = redis.Redis()
print(f'Celery queue length: {r.llen("celery")}')
print(f'sale_sofia queue length: {r.llen("sale_sofia")}')
PYCODE

echo "" | tee -a "$RESULTS_FILE"
if [ $TEST5_RESULT -eq 0 ]; then
    echo "**Result**: PASS - No orphan mubeng processes after Celery kill" | tee -a "$RESULTS_FILE"
else
    echo "**Result**: CRITICAL FAIL - Mubeng processes orphaned when Celery dies mid-task!" | tee -a "$RESULTS_FILE"
    echo "This indicates a subprocess cleanup issue that needs immediate attention." | tee -a "$RESULTS_FILE"
fi
echo "" | tee -a "$RESULTS_FILE"

# Final cleanup
cleanup_all

# Summary
echo "---" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"
echo "## Summary" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"
echo "| Test | Result |" | tee -a "$RESULTS_FILE"
echo "|------|--------|" | tee -a "$RESULTS_FILE"
echo "| Test 1: PSC SIGTERM | $([ $TEST1_RESULT -eq 0 ] && echo 'PASS' || echo 'FAIL') |" | tee -a "$RESULTS_FILE"
echo "| Test 2: PSC SIGKILL | $([ $TEST2_RESULT -eq 0 ] && echo 'PASS' || echo 'FAIL') |" | tee -a "$RESULTS_FILE"
echo "| Test 3: Celery + Mubeng | $([ $TEST3_MUBENG -eq 0 ] && [ $TEST3_CELERY -eq 0 ] && echo 'PASS' || echo 'FAIL') |" | tee -a "$RESULTS_FILE"
echo "| Test 4: Full Pipeline | $([ $TEST4_RESULT -eq 0 ] && echo 'PASS' || echo 'FAIL') |" | tee -a "$RESULTS_FILE"
echo "| Test 5: Mid-Task Kill | $([ $TEST5_RESULT -eq 0 ] && echo 'PASS' || echo 'CRITICAL FAIL') |" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "---" | tee -a "$RESULTS_FILE"
echo "Tests completed. Results saved to: $RESULTS_FILE"
