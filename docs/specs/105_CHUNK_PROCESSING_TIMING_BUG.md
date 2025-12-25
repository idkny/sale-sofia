# Spec 105: Chunk Processing Timing Bug

**Created**: 2025-12-25
**Status**: DOCUMENTED - Needs implementation in production code
**Priority**: P1 - Affects reliability of proxy refresh pipeline

---

## 1. Bug Discovery

### How We Found It
During Test 2.2.6 (PSC → Dispatcher → Mubeng data flow test), the test FAILED initially:

```
[Step 4] Triggering check_scraped_proxies_task (dispatcher)...
OK: Dispatcher completed: Dispatched 29 chunks for processing.

[Step 5] Waiting for Mubeng workers to process chunks...
(This tests parallel chunk processing - may take 2-5 minutes)

[Step 6] Verifying results...
FAIL: live_proxies.json not created
```

### Root Cause
The test terminated before chunks finished processing:
- Test timeout: 5 minutes (300 seconds)
- Actual time needed: ~11 minutes (660 seconds)
- Workers were STILL PROCESSING when test gave up

### Evidence from Logs
```
wow  84438  0.5  0.4  94068 76816 ?  S  14:39  0:01  celery worker...
[2025-12-25 14:43:36,908: INFO] Task check_proxy_chunk_task succeeded in 95.87s
[2025-12-25 14:44:24,332: INFO] Task check_proxy_chunk_task succeeded in 47.39s
```

---

## 2. Timing Analysis

### Current Test Run (2,897 proxies)
| Metric | Value |
|--------|-------|
| Total proxies | 2,897 |
| Chunk size | 100 proxies |
| Total chunks | 29 |
| Worker concurrency | 4 |
| Processing rounds | 29 ÷ 4 = ~8 rounds |
| Time per chunk | 45-95 seconds |
| Total time | ~11 minutes |

### Why Chunks Take 45-95 Seconds Each
Each chunk goes through:
1. **Mubeng liveness check**: ~10-15s (network dependent)
2. **Anonymity check**: ~20-40s (HTTP requests to ipify.org per live proxy)
3. **Quality check**: ~15-30s (additional HTTP requests per non-transparent proxy)

### Scaling Projections

| Proxies | Chunks | Rounds (4 workers) | Estimated Time |
|---------|--------|-------------------|----------------|
| 2,897 | 29 | 8 | 11 min |
| 5,000 | 50 | 13 | 18 min |
| 10,000 | 100 | 25 | 35 min |
| 20,000 | 200 | 50 | 70 min |

**WARNING**: PSC can scrape varying amounts depending on proxy sources availability!

---

## 3. The Fix We Applied (Test Only)

### Original Code (BROKEN)
```python
timeout = 300  # 5 minutes - TOO SHORT!

while time.time() - start_time < timeout:
    if live_json.exists():
        # Check if file exists
        break
    time.sleep(10)
```

### Fixed Code (Test)
```python
timeout = 900  # 15 minutes - better but still hardcoded!

while time.time() - start_time < timeout:
    # Check for results file
    if live_json.exists():
        break

    # Monitor progress via log file
    succeeded = log_content.count("succeeded in")
    print(f"  [{elapsed}s] ~{succeeded} chunks completed...")

    time.sleep(check_interval)
```

---

## 4. Production Code Risk Assessment

### Files That May Have This Bug

**CHECK THESE FILES FOR HARDCODED TIMEOUTS:**

1. **`orchestrator.py`** - May have timeouts waiting for pipeline completion
2. **`celery_app.py:45`** - Has `task_time_limit=1800` (30 min) - this is per-task, not total
3. **Any code that calls `scrape_and_check_chain_task` and waits for results**
4. **Any monitoring/health check code**

### The Real Problem
The dispatcher task (`check_scraped_proxies_task`) returns IMMEDIATELY after dispatching:
```python
# From proxies/tasks.py:87
(parallel_tasks | callback).delay()
logger.info("Dispatched all proxy check chunks to workers.")
return f"Dispatched {len(proxy_chunks)} chunks for processing."  # Returns NOW!
```

Anyone waiting for `check_scraped_proxies_task.delay().get()` will get the dispatch message, NOT the final results!

---

## 5. Correct Solution (For Production)

### Option A: Dynamic Timeout Calculation
```python
def calculate_timeout(num_proxies, chunk_size=100, workers=4, time_per_chunk=120):
    """Calculate expected processing time with safety margin."""
    chunks = (num_proxies + chunk_size - 1) // chunk_size
    rounds = (chunks + workers - 1) // workers
    base_time = rounds * time_per_chunk
    return base_time * 1.5  # 50% safety margin
```

### Option B: Event-Based Completion (Recommended)
Instead of timeouts, use Redis pub/sub or Celery's result backend:
```python
# After dispatching, wait for callback task to complete
chord_result = (parallel_tasks | callback).delay()
final_result = chord_result.get(timeout=calculated_timeout)
```

### Option C: Progress Tracking via Redis
```python
# In check_proxy_chunk_task
redis_client.incr("proxy_check:chunks_completed")

# In monitoring code
while redis_client.get("proxy_check:chunks_completed") < total_chunks:
    time.sleep(10)
```

---

## 6. Test Verification

### Did We Test Multiple Times?
**NO** - We only ran the fixed test once successfully. The 15-minute timeout worked for 2,897 proxies but is NOT guaranteed for larger sets.

### What We Should Do Before Production
1. Run test with simulated large proxy lists (5k, 10k)
2. Implement dynamic timeout calculation
3. Add progress monitoring to production code
4. Consider adding a "max proxies per refresh" limit

---

## 7. Action Items for Next Session

### Must Do Before Full Pipeline Test (2.3)
- [ ] Review `orchestrator.py` for hardcoded timeouts
- [ ] Check if any code waits for `check_scraped_proxies_task` result directly
- [ ] Decide: dynamic timeout vs event-based completion

### Implementation Tasks
- [ ] Add dynamic timeout calculation to test
- [ ] Add progress monitoring to production pipeline
- [ ] Add Redis-based progress tracking (optional but recommended)
- [ ] Add "chunks completed" logging to tasks.py

### Testing Tasks
- [ ] Test with 5,000+ proxy list (can mock PSC output)
- [ ] Verify timeout scales correctly
- [ ] Test edge case: what if PSC returns 0 proxies?

---

## 8. Key Insight

**The bug pattern**: Assuming a pipeline will complete within a fixed time.

**The reality**: Processing time depends on:
- Number of items (proxies)
- Network latency (varies)
- External API response times (ipify.org, target sites)
- Worker availability

**The lesson**: Never use hardcoded timeouts for data pipelines. Either:
1. Calculate timeout dynamically based on input size
2. Use event-based completion signals
3. Implement progress tracking with adaptive waiting

---

## 9. Related Files

| File | Relevance |
|------|-----------|
| `tests/stress/test_psc_dispatcher_mubeng.py` | Test that found this bug |
| `proxies/tasks.py` | Production task code - needs review |
| `orchestrator.py` | May have timeout issues |
| `celery_app.py` | Task timeout configuration |
