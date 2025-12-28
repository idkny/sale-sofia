# Orchestration Research: Proxy Module

## Executive Summary

The proxy module (`proxies/`) is a **reference implementation** for Phase 4.3. It demonstrates Celery dispatcher/worker/callback patterns, Redis progress tracking, and multi-stage job coordination. These patterns are directly transferable to site scraping tasks.

---

## 1. Proxy Management Architecture

### Core Components
| File | Purpose |
|------|---------|
| `get_free_proxies.py` | Scrape from external sources |
| `get_paid_proxies.py` | Paid proxy sources |
| `proxy_validator.py` | Pre-flight checks with scoring |
| `anonymity_checker.py` | Header-based verification |
| `quality_checker.py` | IP service + target site testing |
| `mubeng_manager.py` | Manages Mubeng rotator process |
| `tasks.py` | Celery tasks for background processing |
| `proxies_main.py` | Facade functions for client code |

---

## 2. Celery Patterns in `proxies/tasks.py`

### Pattern 1: Task Chaining + Chord

```
scrape_new_proxies_task()
  → check_scraped_proxies_task() [dispatcher]
      → group(check_proxy_chunk_task.s() * N) [parallel]
          → process_check_results_task() [callback]
```

### Dispatcher Task (check_scraped_proxies_task)
```python
@celery_app.task(bind=True)
def check_scraped_proxies_task(self, _previous_result):
    # 1. Split proxies into chunks of 100
    chunks = [proxies[i:i+100] for i in range(0, len(proxies), 100)]

    # 2. Initialize Redis progress tracking
    r.set(job_total_chunks_key(job_id), len(chunks))
    r.set(job_completed_chunks_key(job_id), 0)
    r.set(job_status_key(job_id), "DISPATCHED")

    # 3. Create group of parallel tasks
    chunk_tasks = group([
        check_proxy_chunk_task.s(chunk, job_id)
        for chunk in chunks
    ])

    # 4. Chain with callback
    workflow = chord(chunk_tasks, process_check_results_task.s(job_id))
    result = workflow.apply_async()

    # 5. Return dispatch metadata
    return DispatchResult(job_id=job_id, chord_id=result.id, total_chunks=len(chunks))
```

### Worker Task (check_proxy_chunk_task)
```python
@celery_app.task(soft_time_limit=780, time_limit=900)
def check_proxy_chunk_task(chunk, job_id):
    # Process chunk: liveness → anonymity → filter → quality
    results = []
    for proxy in chunk:
        # ... validation logic
        results.append(proxy_result)

    # Update Redis progress
    r.incr(job_completed_chunks_key(job_id))
    return results
```

### Callback Task (process_check_results_task)
```python
@celery_app.task
def process_check_results_task(results, job_id):
    # 1. Flatten results from all chunks
    all_proxies = [p for chunk in results for p in chunk]

    # 2. Filter out Transparent proxies
    good_proxies = [p for p in all_proxies if p.anonymity != "Transparent"]

    # 3. Merge with existing proxies
    merged = merge_proxies(existing, good_proxies)

    # 4. Save to files
    save_to_json("live_proxies.json", merged)
    save_to_txt("live_proxies.txt", merged)

    # 5. Mark job complete
    r.set(job_status_key(job_id), "COMPLETE")
    r.set(job_result_count_key(job_id), len(merged))
```

### Meta-Task for Beat
```python
@celery_app.task
def scrape_and_check_chain_task():
    """Triggers full scrape+check chain for Beat scheduler."""
    refresh_chain = chain(
        scrape_new_proxies_task.s(),
        check_scraped_proxies_task.s()
    )
    result = refresh_chain.delay()
    return f"Chain dispatched: {result.id}"
```

---

## 3. Redis Progress Tracking

### Key Functions (proxies/redis_keys.py)
```python
job_total_chunks_key(job_id)     # proxy_refresh:{job_id}:total_chunks
job_completed_chunks_key(job_id) # proxy_refresh:{job_id}:completed_chunks
job_status_key(job_id)           # proxy_refresh:{job_id}:status
job_started_at_key(job_id)       # proxy_refresh:{job_id}:started_at
job_completed_at_key(job_id)     # proxy_refresh:{job_id}:completed_at
job_result_count_key(job_id)     # proxy_refresh:{job_id}:result_count
```

### Progress Lifecycle
1. Dispatcher initializes all keys with 1-hour TTL
2. Each worker increments `completed_chunks`
3. Callback marks job COMPLETE with result count
4. Orchestrator polls progress via `get_refresh_progress(job_id)`

---

## 4. Proxy Refresh/Rotation Workflow

### Refresh Trigger Points
1. **Scheduled**: Celery Beat (every 6 hours)
2. **On-Demand**: When count falls below `MIN_PROXIES_FOR_SCRAPING`
3. **Manual**: Direct call to `scrape_proxies()` or `check_proxies()`

### Refresh Flow
```
1. Check live_proxies.json count
2. If < MIN_PROXIES_FOR_SCRAPING (10):
   - Trigger scrape_new_proxies_task
   - Chain check_scraped_proxies_task
3. Scraper downloads from ~15 proxy list sites
4. Mubeng --check verifies liveness (45s timeout)
5. Anonymity check via judge URLs
6. Quality check via IP services
7. Transparent proxies filtered out
8. Results merged, sorted by timeout
9. Save to live_proxies.json + live_proxies.txt
```

### Rotation During Scraping
- Mubeng runs on port 8089 as subprocess
- Uses `-w` flag to watch proxy file for changes
- Auto-reloads when `live_proxies.txt` modified
- Rotates randomly (`-m random`), synced mode (`-s`)

---

## 5. Proxy Configuration

### Settings (config/settings.py)
```python
MUBENG_PROXY = "http://localhost:8089"
MIN_PROXIES_TO_START = 1
MIN_PROXIES_FOR_SCRAPING = 10
MAX_PROXY_RETRIES = 3
PROXY_TIMEOUT_SECONDS = 45
PROXY_VALIDATION_TIMEOUT = 10

# Scoring
SCORE_SUCCESS_MULTIPLIER = 1.1   # +10% on success
SCORE_FAILURE_MULTIPLIER = 0.5   # -50% on failure
MAX_PROXY_FAILURES = 3           # Auto-remove
MIN_PROXY_SCORE = 0.01           # Auto-remove if below
```

---

## 6. Celery Patterns Reusable for Phase 4.3

### Pattern A: Dispatcher + Parallel Workers + Callback
```python
@celery_app.task(bind=True)
def dispatch_site_scraping(self, site_name, search_filters):
    """Dispatcher: split URL list into chunks"""
    # 1. Get list of search result URLs
    # 2. Initialize Redis tracking
    # 3. Create group of worker tasks
    # 4. Chain with callback
    # 5. Return dispatch metadata

@celery_app.task(soft_time_limit=780, time_limit=900)
def scrape_url_chunk(urls_chunk, job_id, site_name):
    """Worker: process one chunk of URLs"""
    # 1. Extract listing data
    # 2. Save incrementally
    # 3. Update Redis progress
    # 4. Return chunk results

@celery_app.task
def process_scraping_results(results, job_id, site_name):
    """Callback: merge and deduplicate results"""
    # 1. Flatten chunk results
    # 2. Cross-site dedup
    # 3. Save to database
    # 4. Mark job complete
```

### Pattern B: Progress Tracking via Redis
```python
# Reuse Redis key patterns:
# scraping:{job_id}:total_urls
# scraping:{job_id}:completed_urls
# scraping:{job_id}:status
# scraping:{job_id}:started_at
# scraping:{job_id}:completed_at
# scraping:{job_id}:result_count
```

### Pattern C: Soft + Hard Time Limits
```python
@celery_app.task(soft_time_limit=780, time_limit=900)
def scrape_url_chunk(...):
    """
    Soft limit: 13 min (graceful shutdown signal)
    Hard limit: 15 min (forceful termination)
    """
```

### Pattern D: Chunking for Parallelism
- Proxy chunks: 100 proxies each
- URL chunks: 25-50 URLs (recommended)
- More parallelism = more resilience (one chunk fail ≠ job fail)

---

## 7. Key Architectural Insights

1. **Dispatcher Pattern is Critical**: Splits work, initializes tracking, creates chord, returns metadata

2. **Redis TTL Prevents Accumulation**: All progress keys expire after 1 hour

3. **Merge Strategy for Results**: New proxies override old (fresher data wins)

4. **Worker Time Limits**: Soft (780s) + Hard (900s) ensures robustness

5. **File-Based + Redis**: JSON files = persistent state, Redis = ephemeral progress

6. **Anonymity Filtering is Aggressive**: Only "Anonymous" or "Elite" proxies kept

---

## 8. Configuration for Phase 4.3

### Celery Queue Strategy
- Proxy tasks: `sale_sofia` queue (existing)
- Scraping tasks: Same queue or new `scraping` queue
- Worker concurrency: 8 (current, reasonable for 16-core)

### Redis Database Allocation
- DB 0: Broker (tasks queue)
- DB 1: Result backend
- DB 2: Progress tracking
- DB 3: Cache/temp

### Recommended Chunk Sizes
| Task Type | Chunk Size | Reason |
|-----------|------------|--------|
| Proxies | 100 | Current implementation |
| URLs | 25-50 | Balance parallelism/overhead |

### Time Limits for Scraping
| Limit | Value | Purpose |
|-------|-------|---------|
| Soft | 10-15 min | Graceful shutdown signal |
| Hard | 15-20 min | Force termination |

---

## Summary

The proxy module provides a **complete template** for Phase 4.3:

- Same Celery dispatcher/workers/callback structure
- Same Redis progress tracking
- Same merge/dedup logic
- Same time limit strategy

**Key innovation needed**: Adapt patterns for URLs instead of proxies, add cross-site deduplication at callback stage.
