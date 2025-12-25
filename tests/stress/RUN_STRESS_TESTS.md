# How to Run Stress Tests

## Quick Start

```bash
cd /home/wow/Projects/sale-sofia
bash run_all_stress_tests.sh
```

Results will be in: `stress_test_results.md`

## What Gets Tested

1. **Test 1**: PSC graceful shutdown (SIGTERM)
2. **Test 2**: PSC ungraceful kill (SIGKILL)
3. **Test 3**: Celery + Mubeng integration
4. **Test 5**: **CRITICAL** - Celery dies mid-task (orphan detection)

## Critical Test: Test 5

This test simulates Celery crashing while a task is running. It will reveal if mubeng processes become orphans.

**If Test 5 fails**:
- Mubeng processes will be left running
- This is a critical bug that MUST be fixed
- Fix location: `/home/wow/Projects/sale-sofia/proxies/tasks.py` in `check_proxy_chunk_task`

## Expected Output

### All Tests Pass
```
=== RESULT: PASS ===
All critical tests PASSED
```

### Test 5 Fails (Critical Issue)
```
CRITICAL FAIL: Orphan mubeng processes found!
Count: 3
PID CMD
1234 /path/to/mubeng
1235 /path/to/mubeng
1236 /path/to/mubeng

Action required: Fix subprocess cleanup in check_proxy_chunk_task
```

## Cleanup

If tests leave processes running:
```bash
pkill -9 -f "mubeng"
pkill -9 -f "proxy-scraper-checker"
pkill -9 -f "celery.*worker"
```

## Files Created

- `/home/wow/Projects/sale-sofia/test1_psc_sigterm.sh` - Test 1
- `/home/wow/Projects/sale-sofia/test2_psc_sigkill.sh` - Test 2
- `/home/wow/Projects/sale-sofia/test3_celery_mubeng.py` - Test 3
- `/home/wow/Projects/sale-sofia/test5_mid_task_kill.py` - Test 5 (CRITICAL)
- `/home/wow/Projects/sale-sofia/run_all_stress_tests.sh` - Master script
- `/home/wow/Projects/sale-sofia/STRESS_TESTS_README.md` - Full documentation
- `/home/wow/Projects/sale-sofia/STRESS_TEST_FINDINGS.md` - Detailed findings

## Documentation

See `STRESS_TESTS_README.md` for complete documentation.
See `STRESS_TEST_FINDINGS.md` for detailed analysis.
