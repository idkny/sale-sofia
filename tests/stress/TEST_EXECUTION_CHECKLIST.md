# Stress Test Execution Checklist

## Pre-Test Setup

- [ ] Redis is running: `redis-cli ping`
- [ ] PSC binary exists: `ls -lh proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker`
- [ ] Mubeng binary exists: `which mubeng`
- [ ] Python environment activated
- [ ] No orphan processes: `pgrep -af "celery|mubeng|proxy-scraper" || echo "Clean"`

## Execute Tests

```bash
cd /home/wow/Projects/sale-sofia
bash run_all_stress_tests.sh
```

## During Test Execution

Watch for:
- [ ] Test 1 output shows no orphan PSC processes
- [ ] Test 2 output shows no orphan PSC processes
- [ ] Test 3 output shows clean Celery + Mubeng shutdown
- [ ] **Test 5 (CRITICAL)** - watch for orphan mubeng processes

## Review Results

```bash
cat stress_test_results.md
```

Check for:
- [ ] Test 1: PASS
- [ ] Test 2: PASS
- [ ] Test 3: PASS
- [ ] **Test 5: PASS or CRITICAL FAIL**

## Post-Test Cleanup

```bash
# Verify no orphans remain
pgrep -af "celery|mubeng|proxy-scraper" || echo "All clean"

# Clean up if needed
pkill -9 -f "mubeng"
pkill -9 -f "proxy-scraper-checker"
pkill -9 -f "celery.*worker"
```

## If Test 5 Fails (CRITICAL)

- [ ] Note the count of orphan processes
- [ ] Review `SUBPROCESS_CLEANUP_ANALYSIS.md`
- [ ] Identify fix location: `proxies/tasks.py` lines 124-126
- [ ] Implement process group management fix
- [ ] Re-run tests
- [ ] Verify PASS on re-run

## If All Tests Pass

- [ ] Document success in project notes
- [ ] Add tests to CI/CD pipeline
- [ ] Set up production monitoring:
  ```bash
  # Add to cron
  */5 * * * * pgrep -af mubeng | grep -v celery && echo "ALERT"
  ```
- [ ] Configure systemd for proper cleanup
- [ ] Ready for production deployment

## Files to Review Based on Results

### All Tests Pass
- [ ] `stress_test_results.md` - Confirm clean execution
- [ ] `STRESS_TEST_SUMMARY.md` - Production deployment checklist

### Test 5 Fails
- [ ] `stress_test_results.md` - See failure details
- [ ] `SUBPROCESS_CLEANUP_ANALYSIS.md` - Understand root cause
- [ ] `proxies/tasks.py` - Implement fix at lines 124-126
- [ ] Re-run: `bash run_all_stress_tests.sh`

## Expected Timeline

| Phase | Time | Status |
|-------|------|--------|
| Pre-test setup | 2 min | [ ] |
| Run all tests | 10 min | [ ] |
| Review results | 5 min | [ ] |
| **If fix needed** | 20 min | [ ] |
| Re-test | 10 min | [ ] |
| Documentation | 5 min | [ ] |
| **Total** | 30-50 min | [ ] |

## Success Criteria

### Green Light for Production
- [x] All tests created successfully
- [ ] All 5 tests executed
- [ ] Test 1: PASS
- [ ] Test 2: PASS
- [ ] Test 3: PASS
- [ ] **Test 5: PASS** (most critical)
- [ ] No orphan processes detected
- [ ] Cleanup working correctly

### Red Light - Fix Required
- [ ] Test 5: FAIL
- [ ] Orphan mubeng processes detected
- [ ] Fix implemented
- [ ] Re-test shows PASS
- [ ] Ready for production

## Quick Commands Reference

```bash
# Run tests
bash run_all_stress_tests.sh

# View results
cat stress_test_results.md

# Check for orphans
pgrep -af "mubeng|proxy-scraper|celery"

# Clean up orphans
pkill -9 -f "mubeng"
pkill -9 -f "proxy-scraper-checker"
pkill -9 -f "celery.*worker"

# Monitor processes
watch -n 2 'pgrep -af "mubeng|celery" | wc -l'

# Check Redis queues
redis-cli LLEN celery
redis-cli LLEN sale_sofia
```

## Sign-Off

Test Date: ________________

Test Executor: ________________

Results:
- [ ] All tests PASS - Ready for production
- [ ] Test 5 FAIL - Fix required, see details below

Notes:
_____________________________________________
_____________________________________________
_____________________________________________

Fix implemented (if needed): [ ] Yes [ ] No

Re-test results: [ ] PASS [ ] N/A

Production deployment: [ ] Approved [ ] On hold
