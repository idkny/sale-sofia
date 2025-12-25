# Stress Tests for Proxy System

## Overview

These stress tests verify process management, resource cleanup, and subprocess handling in the proxy scraping and checking pipeline.

## Test Files

### Individual Tests

1. **test1_psc_sigterm.sh** - PSC graceful shutdown
   - Tests if `proxy-scraper-checker` cleans up properly on SIGTERM
   - Expected: Clean exit, no orphan processes

2. **test2_psc_sigkill.sh** - PSC ungraceful kill
   - Tests if `proxy-scraper-checker` leaves orphans on SIGKILL
   - Expected: Process killed, no orphan processes

3. **test3_celery_mubeng.py** - Celery + Mubeng integration
   - Tests if mubeng processes are cleaned up when Celery worker stops gracefully
   - Expected: All mubeng and celery processes cleaned up

4. **test5_mid_task_kill.py** - **CRITICAL TEST**
   - Tests if mubeng processes become orphans when Celery is killed during task execution
   - This is the most important test - detects subprocess cleanup bugs
   - Expected: No orphan mubeng processes after Celery is killed

### Master Script

- **run_all_stress_tests.sh** - Runs all tests in sequence
- Generates `stress_test_results.md` with detailed results

## How to Run

### Run All Tests
```bash
cd /home/wow/Projects/sale-sofia
bash run_all_stress_tests.sh
```

### Run Individual Tests
```bash
# Test 1
bash test1_psc_sigterm.sh

# Test 2
bash test2_psc_sigkill.sh

# Test 3
python test3_celery_mubeng.py

# Test 5 (Critical)
python test5_mid_task_kill.py
```

## What We're Testing For

### Process Orphaning
- **Symptom**: Mubeng or PSC processes continue running after parent dies
- **Impact**: Resource leaks, zombie processes, port conflicts
- **Root Cause**: Improper subprocess management (missing cleanup handlers)

### Resource Cleanup
- **What to watch**: Process counts before/after operations
- **Commands used**:
  - `pgrep -af mubeng` - Check for mubeng processes
  - `pgrep -af proxy-scraper` - Check for PSC processes
  - `pgrep -af celery` - Check for Celery workers

### Task State
- **What to check**: Task status in Redis after crashes
- **Commands**:
  - `redis-cli LLEN celery` - Check celery queue
  - `redis-cli LLEN sale_sofia` - Check sale_sofia queue

## Expected Results

### PASS Criteria
- No orphan processes after graceful shutdown (SIGTERM)
- No orphan processes after ungraceful kill (SIGKILL)
- Mubeng processes cleaned up when Celery stops
- **Most critical**: Mubeng processes cleaned up when Celery dies mid-task

### FAIL Indicators
- Orphan mubeng processes after Celery death
- Growing number of processes over multiple test runs
- Processes that can't be killed with SIGTERM

## Known Issues to Test For

Based on the codebase, we're specifically testing for:

1. **Mubeng subprocess cleanup** in `check_proxy_chunk_task`
   - File: `/home/wow/Projects/sale-sofia/proxies/tasks.py`
   - Current implementation uses `subprocess.run()` which may not handle cleanup properly

2. **PSC subprocess cleanup** in `scrape_proxies_task`
   - File: `/home/wow/Projects/sale-sofia/proxies/tasks.py`
   - Uses `subprocess.Popen()` with context manager, but needs verification

## Interpreting Results

### If Test 5 Fails (CRITICAL)
```
CRITICAL FAIL: Orphan mubeng processes found!
```

**Action Required**:
1. Review `check_proxy_chunk_task` in `/home/wow/Projects/sale-sofia/proxies/tasks.py`
2. Implement proper subprocess cleanup:
   - Use signal handlers
   - Register cleanup with `atexit`
   - Use subprocess context managers
   - Handle SIGTERM/SIGKILL propagation

**Example Fix**:
```python
# Instead of:
subprocess.run([...])

# Use:
proc = subprocess.Popen([...])
try:
    # Do work
finally:
    proc.terminate()
    proc.wait(timeout=5)
    if proc.poll() is None:
        proc.kill()
```

### If Tests Pass
All tests passing means:
- Process cleanup is working correctly
- No resource leaks detected
- System is production-ready for process management

## Cleanup

If tests leave orphan processes:
```bash
pkill -9 -f "mubeng"
pkill -9 -f "proxy-scraper-checker"
pkill -9 -f "celery.*worker"
```

## Results Location

All test results are written to:
```
/home/wow/Projects/sale-sofia/stress_test_results.md
```

## Next Steps After Testing

1. Review `stress_test_results.md`
2. If Test 5 fails, implement subprocess cleanup fix
3. Re-run tests to verify fix
4. Document any production deployment considerations
