#!/bin/bash

# Celery Stress Test Suite
# Tests graceful/ungraceful shutdown, multiple workers, and beat schedule corruption

LOG_FILE="celery_stress_test_results.log"
echo "=== Celery Stress Test Started at $(date) ===" > "$LOG_FILE"

# Helper function to log
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Helper to count celery processes
count_celery() {
    pgrep -c -f celery 2>/dev/null || echo "0"
}

# Helper to list celery processes
list_celery() {
    pgrep -af celery 2>/dev/null || echo "No celery processes"
}

# Cleanup function
cleanup() {
    log "Cleaning up any remaining processes..."
    pkill -9 -f "celery -A celery_app" 2>/dev/null
    sleep 2
}

# Initial cleanup
cleanup

log ""
log "=========================================="
log "TEST 1: Graceful Start/Stop Cycle (5 times)"
log "=========================================="

for i in {1..5}; do
    log ""
    log "=== Cycle $i: Graceful Shutdown ==="

    # Start celery worker
    celery -A celery_app worker -Q celery,sale_sofia --loglevel=info >> "$LOG_FILE" 2>&1 &
    CELERY_PID=$!
    log "Started Celery worker with PID: $CELERY_PID"

    sleep 5

    # Check process count before shutdown
    BEFORE_COUNT=$(count_celery)
    log "Celery processes before shutdown: $BEFORE_COUNT"
    list_celery >> "$LOG_FILE"

    # Graceful shutdown
    log "Sending SIGTERM to PID $CELERY_PID..."
    kill -SIGTERM $CELERY_PID 2>/dev/null
    wait $CELERY_PID 2>/dev/null
    EXIT_CODE=$?
    log "Exit code: $EXIT_CODE"

    sleep 2

    # Check for orphans
    AFTER_COUNT=$(count_celery)
    log "Celery processes after shutdown: $AFTER_COUNT"
    if [ "$AFTER_COUNT" -eq 0 ]; then
        log "✓ No orphans detected"
    else
        log "✗ ORPHANS DETECTED:"
        list_celery >> "$LOG_FILE"
    fi

    sleep 2
done

log ""
log "=========================================="
log "TEST 2: Ungraceful Shutdown (SIGKILL) - 3 cycles"
log "=========================================="

for i in {1..3}; do
    log ""
    log "=== Cycle $i: Ungraceful Shutdown ==="

    # Start celery worker
    celery -A celery_app worker -Q celery,sale_sofia --loglevel=info >> "$LOG_FILE" 2>&1 &
    CELERY_PID=$!
    log "Started Celery worker with PID: $CELERY_PID"

    sleep 5

    # Check process count before kill
    BEFORE_COUNT=$(count_celery)
    log "Celery processes before SIGKILL: $BEFORE_COUNT"
    list_celery >> "$LOG_FILE"

    # Ungraceful shutdown
    log "Sending SIGKILL to PID $CELERY_PID..."
    kill -9 $CELERY_PID 2>/dev/null

    sleep 2

    # Check for orphans
    AFTER_COUNT=$(count_celery)
    log "Celery processes after SIGKILL: $AFTER_COUNT"
    log "Orphan count: $AFTER_COUNT"
    if [ "$AFTER_COUNT" -gt 0 ]; then
        log "✗ ORPHANS DETECTED:"
        list_celery >> "$LOG_FILE"
    else
        log "✓ No orphans detected"
    fi

    # Cleanup orphans for next cycle
    cleanup
done

log ""
log "=========================================="
log "TEST 3: Multiple Celery Processes (5 workers)"
log "=========================================="

log ""
log "=== Starting 5 Celery workers simultaneously ==="

WORKER_PIDS=()
for i in {1..5}; do
    celery -A celery_app worker -Q celery,sale_sofia --loglevel=info >> "$LOG_FILE" 2>&1 &
    PID=$!
    WORKER_PIDS+=($PID)
    log "Started worker $i with PID: $PID"
done

sleep 10

log ""
log "Running workers:"
list_celery >> "$LOG_FILE"
TOTAL_PROCESSES=$(count_celery)
log "Total celery processes: $TOTAL_PROCESSES"

log ""
log "Checking Redis queue state..."
CELERY_QUEUE=$(redis-cli LLEN celery 2>/dev/null || echo "Error: Redis not accessible")
SOFIA_QUEUE=$(redis-cli LLEN sale_sofia 2>/dev/null || echo "Error: Redis not accessible")
log "Celery queue length: $CELERY_QUEUE"
log "sale_sofia queue length: $SOFIA_QUEUE"

log ""
log "Cleaning up all workers..."
pkill -9 -f "celery -A celery_app" 2>/dev/null
sleep 2

AFTER_CLEANUP=$(count_celery)
if [ "$AFTER_CLEANUP" -eq 0 ]; then
    log "✓ All workers cleaned successfully"
else
    log "✗ Cleanup incomplete. Remaining processes: $AFTER_CLEANUP"
    list_celery >> "$LOG_FILE"
fi

log ""
log "=========================================="
log "TEST 4: Beat Schedule Corruption Check"
log "=========================================="

log ""
log "=== Starting Celery with Beat ==="

# Remove old schedule files
rm -f celerybeat-schedule* 2>/dev/null
log "Removed old schedule files"

# Start celery with beat
celery -A celery_app worker --beat -Q celery,sale_sofia --loglevel=info >> "$LOG_FILE" 2>&1 &
BEAT_PID=$!
log "Started Celery with Beat, PID: $BEAT_PID"

sleep 10

log ""
log "Schedule files created:"
ls -la celerybeat-schedule* >> "$LOG_FILE" 2>&1 || log "No schedule files found"

log ""
log "Killing ungracefully with SIGKILL..."
pkill -9 -f celery 2>/dev/null
sleep 2

log ""
log "Schedule files after ungraceful kill:"
ls -la celerybeat-schedule* >> "$LOG_FILE" 2>&1 || log "No schedule files found"

log ""
log "Checking for file corruption..."
if [ -f "celerybeat-schedule.db" ] || [ -f "celerybeat-schedule" ]; then
    python3 -c "import shelve; s = shelve.open('celerybeat-schedule'); print('Schedule contents:', dict(s)); s.close()" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "✓ Schedule file readable (not corrupted)"
    else
        log "✗ Schedule file corrupted or unreadable"
    fi
else
    log "No schedule file to check"
fi

# Final cleanup
cleanup

log ""
log "=========================================="
log "=== Celery Stress Test Completed at $(date) ==="
log "=========================================="

echo ""
echo "Test complete! Results saved to: $LOG_FILE"
echo ""
echo "Summary:"
grep -E "(✓|✗|ORPHANS|Orphan count)" "$LOG_FILE" | tail -20
