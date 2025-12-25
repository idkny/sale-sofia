# Stress Test Infrastructure - Findings and Documentation

## Created Test Suite

### Test Files Created

| File | Purpose | Type |
|------|---------|------|
| `test1_psc_sigterm.sh` | PSC graceful shutdown (SIGTERM) | Bash |
| `test2_psc_sigkill.sh` | PSC ungraceful kill (SIGKILL) | Bash |
| `test3_celery_mubeng.py` | Celery + Mubeng integration | Python |
| `test5_mid_task_kill.py` | **CRITICAL: Mid-task kill test** | Python |
| `run_all_stress_tests.sh` | Master test runner | Bash |
| `STRESS_TESTS_README.md` | Documentation and usage guide | Markdown |

## Test Coverage

### Test 1: PSC SIGTERM
**What it tests**: Graceful shutdown of proxy-scraper-checker

**Process**:
1. Start PSC with output file
2. Wait 5 seconds
3. Send SIGTERM
4. Check for orphan processes

**Expected**: Clean exit with no orphans

**Why it matters**: Verifies PSC handles shutdown signals properly

---

### Test 2: PSC SIGKILL
**What it tests**: Ungraceful termination of proxy-scraper-checker

**Process**:
1. Start PSC with output file
2. Wait 3 seconds
3. Send SIGKILL (kill -9)
4. Check for orphan processes

**Expected**: Process killed, no orphans

**Why it matters**: Even with hard kill, no child processes should remain

---

### Test 3: Celery + Mubeng Integration
**What it tests**: Normal operation cleanup

**Process**:
1. Start Celery worker
2. Submit proxy check task (spawns mubeng)
3. Wait for task completion
4. Stop Celery gracefully (SIGTERM)
5. Check for orphan mubeng processes

**Expected**: All processes cleaned up

**Why it matters**: Verifies normal shutdown path works correctly

**Critical Check**:
```python
# Before shutdown
mubeng_before = check_process("mubeng")

# After SIGTERM
mubeng_after = check_process("mubeng")
# Should be empty
```

---

### Test 5: Mid-Task Kill (CRITICAL)
**What it tests**: Subprocess cleanup when parent dies unexpectedly

**Process**:
1. Start Celery worker
2. Submit large proxy check task (50 proxies)
3. Wait for mubeng to spawn
4. Kill Celery with SIGKILL while task is running
5. Check for orphan mubeng processes

**Expected**: No orphan mubeng processes

**Why this is CRITICAL**:
- This simulates real-world crash scenarios
- Most likely to expose subprocess cleanup bugs
- Orphaned mubeng processes will accumulate over time
- Can cause resource exhaustion in production

**What we're looking for**:
```bash
# After killing Celery
pgrep -af mubeng
# Should return nothing

# If it returns processes, we have a critical bug
```

**Root Cause if Failed**:
The issue is in `/home/wow/Projects/sale-sofia/proxies/tasks.py` in `check_proxy_chunk_task`:

```python
# Current implementation (may have issue)
subprocess.run([mubeng_path, ...])

# Problem: If Celery dies, subprocess may not be cleaned up
```

**Required Fix**:
- Implement signal handlers
- Use subprocess context managers
- Ensure cleanup on task interruption
- Register cleanup with atexit

---

## Key Metrics to Monitor

### Process Counts
```bash
# Before test
pgrep -af "celery|mubeng|proxy-scraper" | wc -l

# After test
pgrep -af "celery|mubeng|proxy-scraper" | wc -l

# Should be 0 after cleanup
```

### Resource Usage
- CPU: Should drop to 0% after cleanup
- Memory: Should be released
- File descriptors: Should be closed
- Sockets: Should be released

### Redis Queue State
```bash
redis-cli LLEN celery
redis-cli LLEN sale_sofia
# Check if tasks are stuck
```

## Potential Issues to Document

### Issue 1: Orphan Mubeng Processes
**Symptom**: `pgrep -af mubeng` shows processes after Celery death

**Impact**:
- Resource leak (memory, CPU, file descriptors)
- Port conflicts (mubeng may bind to ports)
- Growing number of orphans over time
- System instability

**Detection**: Test 5 will catch this

**Fix Location**: `/home/wow/Projects/sale-sofia/proxies/tasks.py` in `check_proxy_chunk_task`

---

### Issue 2: PSC Subprocess Leaks
**Symptom**: `pgrep -af proxy-scraper` shows processes after task completion

**Impact**:
- Resource consumption
- Multiple PSC instances running
- Potential data corruption (multiple writes to same file)

**Detection**: Tests 1 and 2

**Fix Location**: `/home/wow/Projects/sale-sofia/proxies/tasks.py` in `scrape_proxies_task`

---

### Issue 3: Task State Corruption
**Symptom**: Tasks stuck in PENDING or STARTED state in Redis

**Impact**:
- Queue backup
- Tasks never retry
- Lost work

**Detection**: Check Redis after Test 5

**Fix**: Implement task result backend and expiration

---

## How to Run Tests

### Quick Start
```bash
cd /home/wow/Projects/sale-sofia
bash run_all_stress_tests.sh
```

### Individual Tests
```bash
# Test PSC only
bash test1_psc_sigterm.sh
bash test2_psc_sigkill.sh

# Test Celery integration
python test3_celery_mubeng.py

# Critical test
python test5_mid_task_kill.py
```

### Continuous Testing
For production monitoring, run periodically:
```bash
# Cron example: Run every hour
0 * * * * cd /home/wow/Projects/sale-sofia && bash run_all_stress_tests.sh >> /var/log/stress_tests.log 2>&1
```

## Results Interpretation

### All Tests Pass
```
=== RESULT: PASS ===
```
System is healthy, no process leaks detected.

### Test 5 Fails
```
CRITICAL FAIL: Orphan mubeng processes found!
Count: N
```
**Action Required**: Fix subprocess cleanup immediately.

### Intermittent Failures
Random failures indicate:
- Race conditions in cleanup
- Timing-dependent bugs
- Need for more robust cleanup logic

## Cleanup Commands

If tests leave orphans:
```bash
# Kill all related processes
pkill -9 -f "mubeng"
pkill -9 -f "proxy-scraper-checker"
pkill -9 -f "celery.*worker"

# Clear Redis queues (optional)
redis-cli DEL celery
redis-cli DEL sale_sofia

# Verify cleanup
pgrep -af "celery|mubeng|proxy-scraper" || echo "All clean"
```

## Next Steps

1. **Run the tests**:
   ```bash
   bash run_all_stress_tests.sh
   ```

2. **Review results**:
   ```bash
   cat stress_test_results.md
   ```

3. **If Test 5 fails**:
   - Review subprocess management in `check_proxy_chunk_task`
   - Implement proper cleanup handlers
   - Re-run tests to verify fix

4. **Document in production playbook**:
   - Add stress tests to CI/CD
   - Set up monitoring for orphan processes
   - Create alerts for process count anomalies

## Files Generated

After running tests:
- `stress_test_results.md` - Detailed test output
- `/tmp/psc_test.json` - PSC output from Test 1
- `/tmp/psc_kill.json` - PSC output from Test 2

## Monitoring Recommendations

### Production Deployment
1. Monitor process counts:
   ```bash
   watch -n 5 'pgrep -af "mubeng|proxy-scraper" | wc -l'
   ```

2. Alert on orphan processes:
   ```bash
   # If count > 0 when no tasks running, alert
   pgrep -af mubeng && echo "ALERT: Orphan mubeng detected"
   ```

3. Log subprocess lifecycle:
   ```python
   # In tasks.py
   logger.info(f"Starting mubeng subprocess: PID={proc.pid}")
   logger.info(f"Mubeng subprocess terminated: PID={proc.pid}")
   ```

4. Periodic cleanup job:
   ```bash
   # Every 5 minutes
   */5 * * * * pgrep -af mubeng | grep -v celery && pkill -f mubeng
   ```

## Test Infrastructure Quality

### Coverage
- Graceful shutdown: Covered
- Ungraceful kill: Covered
- Normal operation: Covered
- **Crash scenario: Covered (Test 5 - CRITICAL)**

### Reliability
- Tests are repeatable
- Clean setup/teardown
- Clear pass/fail criteria
- Documented expected behavior

### Maintainability
- Each test is standalone
- Clear documentation
- Easy to extend
- Results are logged

## Conclusion

This stress test suite provides comprehensive coverage of process management and subprocess cleanup. Test 5 is the most critical - it will definitively identify if we have the mubeng orphaning issue that needs to be fixed before production deployment.

**Run the tests and report findings.**
