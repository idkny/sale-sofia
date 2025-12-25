# Stress Test Suite - Executive Summary

## What Was Created

A comprehensive stress testing suite to identify process management issues, resource leaks, and subprocess cleanup bugs in the proxy scraping and checking pipeline.

## Quick Start

```bash
cd /home/wow/Projects/sale-sofia
bash run_all_stress_tests.sh
```

**Results file**: `stress_test_results.md`

## Test Files Created

| File | Purpose |
|------|---------|
| `test1_psc_sigterm.sh` | Test PSC graceful shutdown |
| `test2_psc_sigkill.sh` | Test PSC ungraceful kill |
| `test3_celery_mubeng.py` | Test Celery + Mubeng integration |
| `test5_mid_task_kill.py` | **CRITICAL** - Test for orphan processes |
| `run_all_stress_tests.sh` | Master test runner |
| `STRESS_TESTS_README.md` | Complete documentation |
| `STRESS_TEST_FINDINGS.md` | Detailed test analysis |
| `SUBPROCESS_CLEANUP_ANALYSIS.md` | Technical deep dive |
| `RUN_STRESS_TESTS.md` | Quick reference guide |

## Critical Test: Test 5

**What it does**: Simulates Celery worker crash while task is running

**Why it's critical**: Will definitively reveal if mubeng processes become orphans when Celery dies

**Expected failure mode**: If subprocess cleanup is broken, orphan mubeng processes will be found

**Impact if it fails**: Resource leaks, process accumulation, system instability in production

## Expected Outcomes

### Scenario A: All Tests Pass
```
=== RESULT: PASS ===
All critical tests PASSED
```

**Interpretation**: No subprocess cleanup issues detected. System is production-ready.

**Next steps**:
- Document findings
- Add tests to CI/CD
- Set up production monitoring

### Scenario B: Test 5 Fails
```
CRITICAL FAIL: Orphan mubeng processes found!
Count: N
```

**Interpretation**: Mubeng processes are not cleaned up when Celery worker dies.

**Root cause**: Subprocess management issue in `check_proxy_chunk_task`

**Fix location**: `/home/wow/Projects/sale-sofia/proxies/tasks.py` lines 124-126

**Solution**: Implement process group management (detailed in `SUBPROCESS_CLEANUP_ANALYSIS.md`)

## Documentation Structure

### User-Facing Documentation
- **RUN_STRESS_TESTS.md** - Quick start guide
- **STRESS_TESTS_README.md** - Complete user documentation

### Technical Documentation
- **STRESS_TEST_FINDINGS.md** - Detailed test analysis and findings
- **SUBPROCESS_CLEANUP_ANALYSIS.md** - Technical deep dive into subprocess management

### Test Output
- **stress_test_results.md** - Generated after running tests

## What Gets Tested

### Process Management
- Graceful shutdown (SIGTERM)
- Ungraceful kill (SIGKILL)
- Normal operation cleanup
- **Crash scenario cleanup (CRITICAL)**

### Resource Cleanup
- Process orphaning
- File descriptor leaks
- Memory leaks
- Port/socket cleanup

### Task State
- Task status after crash
- Queue state preservation
- Task result integrity

## Key Metrics Monitored

### Process Counts
```bash
# Before test
pgrep -af "celery|mubeng|proxy-scraper" | wc -l

# After test (should be 0)
pgrep -af "celery|mubeng|proxy-scraper" | wc -l
```

### Queue State
```bash
redis-cli LLEN celery
redis-cli LLEN sale_sofia
```

### Orphan Detection
```bash
pgrep -af mubeng || echo "No orphans"
```

## Identified Potential Issues

### Issue: Orphan Mubeng Processes
**Location**: `/home/wow/Projects/sale-sofia/proxies/tasks.py:124-126`

**Current code**:
```python
cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
```

**Problem**: `subprocess.run()` may not clean up child processes if parent is killed with SIGKILL

**Test that catches it**: Test 5 (`test5_mid_task_kill.py`)

**Solution**: Process group management with context manager (see `SUBPROCESS_CLEANUP_ANALYSIS.md`)

### Issue: PSC Subprocess Leaks
**Location**: `/home/wow/Projects/sale-sofia/proxies/tasks.py:42-49`

**Same root cause**: No explicit subprocess cleanup on parent death

**Tests that catch it**: Tests 1 and 2

## Production Deployment Recommendations

### Pre-Deployment
1. Run full test suite
2. Verify all tests pass
3. If Test 5 fails, implement fix before deployment

### Monitoring
```bash
# Cron job: Check for orphans every 5 minutes
*/5 * * * * pgrep -af mubeng | grep -v celery && echo "ALERT: Orphan mubeng"
```

### Systemd Configuration
```ini
[Service]
KillMode=control-group
KillSignal=SIGTERM
TimeoutStopSec=10
```

### Alerting
- Alert on process count > expected
- Alert on orphan processes detected
- Monitor memory/CPU for leaks

## Cleanup Commands

If tests leave orphan processes:
```bash
pkill -9 -f "mubeng"
pkill -9 -f "proxy-scraper-checker"
pkill -9 -f "celery.*worker"
```

Verify cleanup:
```bash
pgrep -af "celery|mubeng|proxy-scraper" || echo "All clean"
```

## Timeline to Resolution

1. **Run tests** (5 min)
   ```bash
   bash run_all_stress_tests.sh
   ```

2. **Review results** (5 min)
   ```bash
   cat stress_test_results.md
   ```

3. **If Test 5 fails**:
   - Implement fix (15 min)
   - Re-run tests (5 min)
   - Verify fix (5 min)

4. **Document findings** (10 min)

**Total**: 30-45 minutes to complete testing and potential fixes

## Success Criteria

### Tests Pass
- All 5 tests show "PASS"
- No orphan processes detected
- Clean process cleanup in all scenarios

### Tests Fail (Test 5)
- Orphan processes identified
- Root cause documented
- Fix implemented and verified
- Re-test shows "PASS"

## Next Actions

1. **Run the tests**:
   ```bash
   cd /home/wow/Projects/sale-sofia
   bash run_all_stress_tests.sh
   ```

2. **Read the results**:
   ```bash
   cat stress_test_results.md
   ```

3. **Take action based on results**:
   - If all pass: Document success, deploy to production
   - If Test 5 fails: Review `SUBPROCESS_CLEANUP_ANALYSIS.md`, implement fix

4. **Verify in production**:
   - Set up monitoring
   - Run periodic stress tests
   - Alert on anomalies

## Documentation Files Summary

- **RUN_STRESS_TESTS.md** - How to run tests (1 page)
- **STRESS_TESTS_README.md** - Complete test documentation (3 pages)
- **STRESS_TEST_FINDINGS.md** - Detailed findings and analysis (5 pages)
- **SUBPROCESS_CLEANUP_ANALYSIS.md** - Technical deep dive (6 pages)
- **STRESS_TEST_SUMMARY.md** - This file (executive summary)

## Conclusion

This stress test suite provides comprehensive coverage of process management issues in the proxy pipeline. The most critical test is **Test 5**, which will definitively identify if we have the subprocess orphaning issue that needs to be fixed before production deployment.

**Run the tests now to get definitive answers.**
