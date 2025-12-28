# Debugging Task: Celery + Mubeng + Proxy-Scrape-Checker

**Created**: 2024-12-24
**Status**: In Progress
**Priority**: High

---

## 1. Problem Statement

**Symptoms reported:**
- Celery sometimes works, sometimes doesn't
- Starting/stopping Celery causes issues
- Mubeng works intermittently
- Overall system instability

**Root cause hypothesis:**
Multiple potential issues identified during code review.

---

## 2. Tool Overview & Purpose

### 2.1 Celery (Task Queue)
**Purpose**: Distributed task queue for async processing of proxy scraping/checking
**Version**: 5.4.0
**Config**: `celery_app.py`

**How it should work:**
1. Redis acts as message broker (port 6379)
2. Celery worker picks up tasks from queue
3. Celery Beat schedules periodic tasks (every 6 hours)
4. Tasks run in parallel workers (concurrency=8)

### 2.2 Mubeng (Proxy Rotator/Checker)
**Purpose**: Fast proxy liveness checking and rotation
**Version**: v0.22.0
**Binary**: `proxies/external/mubeng`

**Two modes:**
1. **Checker mode**: `mubeng --check -f input.txt -o output.txt -t 10s`
2. **Rotator mode**: `mubeng -a localhost:8089 -f proxies.txt -t 15s`

### 2.3 Proxy-Scrape-Checker (PSC)
**Purpose**: Scrapes free proxy lists from various sources
**Binary**: `proxies/external/proxy-scraper-checker/target/release/proxy-scraper-checker`
**Output**: `proxies/external/proxy-scraper-checker/out/proxies_pretty.json`

### 2.4 How They Work Together

```
[Celery Beat] --triggers--> [scrape_and_check_chain_task]
                                     |
                                     v
                          [scrape_new_proxies_task]
                                (runs PSC binary)
                                     |
                                     v
                          [check_scraped_proxies_task]
                                (dispatcher)
                                     |
                          +----------+-----------+
                          |          |           |
                          v          v           v
                    [chunk_1]   [chunk_2]   [chunk_N]
                    (mubeng)    (mubeng)    (mubeng)
                          |          |           |
                          +----------+-----------+
                                     |
                                     v
                          [process_check_results_task]
                                (saves results)
                                     |
                                     v
                          live_proxies.json / .txt
```

---

## 3. Identified Potential Issues

### Issue 1: Celery Beat Schedule Corruption
**Location**: Root directory `celerybeat-schedule.*` files
**Problem**: When Celery is killed abruptly, Berkeley DB files can corrupt
**Symptom**: Celery won't start or tasks don't trigger

**Test**: Check if beat schedule files are corrupted
```bash
# Remove and let Celery recreate them
rm -f celerybeat-schedule.bak celerybeat-schedule.dat celerybeat-schedule.dir
```

### Issue 2: Orphan Celery Processes
**Location**: `orchestrator.py:170` uses `start_new_session=True`
**Problem**: Worker detaches from parent, but multiple starts create orphans
**Symptom**: Multiple workers competing, weird behavior

**Test**: Check for multiple workers
```bash
pgrep -f "celery -A celery_app"
ps aux | grep celery
```

### Issue 3: Queue Mismatch
**Location**: `celery_app.py:65` sends to `sale_sofia` queue
**Problem**: Worker must listen to correct queue
**Current**: Worker listens to `celery,sale_sofia` (should be OK)

**Test**: Verify queue consumption
```bash
redis-cli LLEN celery
redis-cli LLEN sale_sofia
```

### Issue 4: Mubeng PTY Requirement
**Location**: `proxies/tasks.py:124`
**Problem**: Mubeng requires terminal/PTY, wrapped with `script`
**Symptom**: Mubeng hangs or doesn't output

**Test**: Run mubeng directly vs with script wrapper
```bash
# Direct (may hang)
./proxies/external/mubeng --check -f test.txt -o out.txt -t 5s

# With script wrapper (should work)
script -q /dev/null -c "./proxies/external/mubeng --check -f test.txt -o out.txt -t 5s"
```

### Issue 5: Redis Connection Drops
**Problem**: Redis may not be running or connection lost
**Symptom**: Tasks stuck in PENDING state

**Test**: Check Redis
```bash
redis-cli ping  # Should return PONG
redis-cli info clients  # Check connected clients
```

### Issue 6: Temp File Cleanup Race
**Location**: `proxies/tasks.py:103-112`
**Problem**: Temp files created with `tempfile.mktemp()` (deprecated)
**Symptom**: Race conditions or files not cleaned up

---

## 4. Debug Test Plan

### Phase 1: Isolated Component Tests

Run each test independently to verify each tool works in isolation.

#### Test 1.1: Redis Connectivity
```bash
# Test file: tests/debug/test_redis_isolated.py
python tests/debug/test_redis_isolated.py
```

#### Test 1.2: Celery Worker Start/Stop
```bash
# Test file: tests/debug/test_celery_isolated.py
python tests/debug/test_celery_isolated.py
```

#### Test 1.3: Mubeng Binary
```bash
# Test file: tests/debug/test_mubeng_isolated.py
python tests/debug/test_mubeng_isolated.py
```

#### Test 1.4: Proxy-Scrape-Checker Binary
```bash
# Test file: tests/debug/test_psc_isolated.py
python tests/debug/test_psc_isolated.py
```

### Phase 2: Integration Tests

#### Test 2.1: Celery + Redis
- Start Redis
- Start Celery worker
- Send test task
- Verify execution

#### Test 2.2: Celery + Mubeng
- Start Celery
- Trigger proxy check task
- Verify mubeng executes

#### Test 2.3: Full Pipeline
- Start all services
- Trigger scrape_and_check_chain_task
- Monitor execution
- Verify output files

### Phase 3: Stress Tests

#### Test 3.1: Start/Stop Cycle
```python
for i in range(5):
    start_celery()
    wait(10)
    stop_celery()
    verify_clean_shutdown()
```

#### Test 3.2: Concurrent Tasks
- Send 10 tasks simultaneously
- Verify all complete without deadlock

---

## 5. Test Files Location

**Stress Tests (ACTUAL - use these):**
```
tests/stress/
├── run_all_stress_tests.sh      # Master runner - START HERE
├── test1_psc_sigterm.sh         # PSC graceful shutdown
├── test2_psc_sigkill.sh         # PSC ungraceful kill
├── test3_celery_mubeng.py       # Celery + Mubeng integration
├── test5_mid_task_kill.py       # CRITICAL: orphan detection
├── stress_tests.sh              # Comprehensive 5-test suite
├── test_mubeng_stress.sh        # Mubeng-specific tests (7 tests)
├── celery_stress_test.py        # Celery stress suite
└── STRESS_TEST_SUMMARY.md       # Results documentation
```

**Run stress tests:**
```bash
cd /home/wow/Projects/sale-sofia/tests/stress
bash run_all_stress_tests.sh
# Results saved to: stress_test_results.md
```

---

## 6. Manual Debug Commands

### Check Current State
```bash
# Redis running?
redis-cli ping

# Celery workers running?
pgrep -af "celery"

# Check Celery queues
redis-cli LLEN celery
redis-cli LLEN sale_sofia

# Check recent Celery log
tail -50 data/logs/celery_worker.log

# Check proxy files
ls -la proxies/live_proxies.json proxies/live_proxies.txt 2>/dev/null
```

### Clean Restart
```bash
# Kill all Celery processes
pkill -9 -f "celery"

# Clear beat schedule (forces fresh start)
rm -f celerybeat-schedule.*

# Clear Redis queues (CAUTION: loses pending tasks)
redis-cli FLUSHDB

# Start fresh
redis-server --daemonize yes
celery -A celery_app worker --beat -Q celery,sale_sofia --loglevel=info
```

### Monitor Live Execution
```bash
# Watch Celery worker
celery -A celery_app events

# Watch Redis keys
redis-cli MONITOR

# Tail logs
tail -f data/logs/celery_worker.log
```

---

## 7. Expected Results

After debugging, the system should:

1. **Redis**: Always reachable, `redis-cli ping` returns PONG
2. **Celery**: Single worker process, clean start/stop
3. **Mubeng**: Executes consistently with PTY wrapper
4. **PSC**: Outputs valid JSON to expected path
5. **Pipeline**: Full chain completes in 5-15 minutes
6. **Output**: `live_proxies.json` contains 10+ validated proxies

---

## 8. Fix Implementation Checklist

- [ ] Test 1.1: Redis isolated - PASS/FAIL
- [ ] Test 1.2: Celery isolated - PASS/FAIL
- [ ] Test 1.3: Mubeng isolated - PASS/FAIL
- [ ] Test 1.4: PSC isolated - PASS/FAIL
- [ ] Test 2.1: Celery+Redis integration - PASS/FAIL
- [ ] Test 2.2: Celery+Mubeng integration - PASS/FAIL
- [ ] Test 2.3: Full pipeline - PASS/FAIL
- [ ] Test 3.1: Start/stop cycle - PASS/FAIL
- [ ] Test 3.2: Concurrent tasks - PASS/FAIL

---

## 9. Reference Implementations

Working implementations from archive/extraction/:

| File | Purpose | Key Pattern |
|------|---------|-------------|
| [automation_AutoBiz.md](../../archive/extraction/automation/automation_AutoBiz.md) | Celery patterns | Chord/Group/Chain orchestration |
| [proxies_AutoBiz.md](../../archive/extraction/proxies/proxies_AutoBiz.md) | Mubeng integration | Checker mode + Rotator mode |
| [config_AutoBiz.md](../../archive/extraction/config/config_AutoBiz.md) | Path management | Absolute paths for Celery workers |
| [workflow_AutoBiz.md](../../archive/extraction/workflow/workflow_AutoBiz.md) | CLI integration | CLI → Celery task triggering |
| [proxies_Scraper.md](../../archive/extraction/proxies/proxies_Scraper.md) | ProxyChecker/Service | Pool management + auto-refresh |

**Key differences to check:**
1. Celery app name: `auto_biz` vs `sale_sofia`
2. Queue configuration
3. Beat schedule format
4. Mubeng invocation pattern (PTY wrapper)
5. Chord orchestration for parallel chunks

---

## 10. Related Documentation

| Document | Purpose |
|----------|---------|
| [102_PROXY_SYSTEM_SPECS.md](102_PROXY_SYSTEM_SPECS.md) | Architecture comparison |
| [TASKS.md](../tasks/TASKS.md) | Master task list |
| [SUBPROCESS_CLEANUP_ANALYSIS.md](../../tests/stress/SUBPROCESS_CLEANUP_ANALYSIS.md) | Technical deep-dive on orphan processes |
