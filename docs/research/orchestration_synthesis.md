# Orchestration Research Synthesis

## Phase 4.3 Readiness Assessment

**Date**: 2025-12-28
**Research Completed**: 7 module investigations

---

## Executive Summary

The codebase is **well-architected for Phase 4.3 extension**. The proxy module provides a complete template for Celery task patterns. The orchestrator has solid infrastructure management. Key gaps: resilience components need Redis backing for multi-worker, and SQLite has write contention concerns.

---

## Module Dependency Map

```
                    ┌─────────────────┐
                    │   Orchestrator   │
                    │  (lifecycle mgr) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    Redis      │   │    Celery     │   │    Mubeng     │
│  (broker +    │   │  (workers +   │   │   (proxy      │
│   progress)   │   │    beat)      │   │   rotator)    │
└───────────────┘   └───────┬───────┘   └───────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Scrapers    │   │  Resilience   │   │     Data      │
│  (websites/)  │   │  (in-memory)  │   │   (SQLite)    │
└───────┬───────┘   └───────────────┘   └───────────────┘
        │
        ▼
┌───────────────┐
│   LLM/Ollama  │
│  (optional)   │
└───────────────┘
```

---

## Initialization Order (What Orchestrator Must Start)

```
1. Redis Server
   ├─ Health check: PING command
   └─ Required for: Celery broker, progress tracking

2. Celery Worker + Beat
   ├─ Health check: inspect().ping()
   ├─ Depends on: Redis
   └─ Required for: proxy tasks, future scraping tasks

3. Proxy Availability
   ├─ Check: live_proxies.json count >= MIN_PROXIES (10)
   ├─ If insufficient: trigger refresh chain via Celery
   └─ Wait until threshold met

4. Mubeng Rotator
   ├─ Start: subprocess on port 8089
   ├─ Depends on: live_proxies.txt
   └─ Required for: HTTP requests

5. Ollama (Optional)
   ├─ Health check: GET localhost:11434
   ├─ If needed: start via subprocess
   └─ Required for: LLM extraction (if use_llm=True)

6. Database Initialization
   ├─ init_db() → migrate_listings_schema() → init_viewings_table()
   └─ Must run before any scraping
```

---

## Patterns to Reuse from Existing Code

### 1. Celery Dispatcher/Worker/Callback (proxies/tasks.py)

```python
# DISPATCHER: Split work, initialize tracking, create chord
@celery_app.task(bind=True)
def dispatch_site_scraping(self, site_name, urls):
    job_id = str(uuid.uuid4())
    chunks = chunk_list(urls, 50)

    # Initialize Redis progress
    r.set(f"scrape:{job_id}:total_chunks", len(chunks))
    r.set(f"scrape:{job_id}:completed", 0)
    r.set(f"scrape:{job_id}:status", "DISPATCHED")

    # Create chord
    workers = group([scrape_chunk.s(chunk, job_id) for chunk in chunks])
    workflow = chord(workers, process_results.s(job_id, site_name))
    result = workflow.apply_async()

    return {"job_id": job_id, "chord_id": result.id}

# WORKER: Process chunk, update progress
@celery_app.task(soft_time_limit=780, time_limit=900)
def scrape_chunk(urls, job_id):
    results = []
    for url in urls:
        # ... scraping logic
        results.append(listing_data)
    r.incr(f"scrape:{job_id}:completed")
    return results

# CALLBACK: Aggregate results, finalize
@celery_app.task
def process_results(all_results, job_id, site_name):
    listings = flatten(all_results)
    save_to_database(listings)
    r.set(f"scrape:{job_id}:status", "COMPLETE")
```

### 2. Context Manager Lifecycle (orchestrator.py)

```python
with Orchestrator() as orch:
    # __enter__: cleanup_stale_processes(), register_shutdown_handlers()
    orch.start_redis()     # Idempotent
    orch.start_celery()    # Idempotent
    orch.wait_for_proxies()
    # ... do work ...
# __exit__: stop_all() guaranteed (Celery before Redis)
```

### 3. Health-Before-Action Pattern

```python
def start_redis(self):
    if self._health_check_redis():
        return True  # Already running
    # Only start if not healthy
    return self._actually_start_redis()
```

### 4. Multi-Stage Fallback (proxy refresh)

```
Stage 1: Chord-based wait (event-driven, preferred)
    ↓ timeout
Stage 2: Redis polling (15s intervals)
    ↓ timeout
Stage 3: File monitoring (mtime check)
```

### 5. Redis Progress Keys (proxies/redis_keys.py)

```
{namespace}:{job_id}:total_chunks
{namespace}:{job_id}:completed_chunks
{namespace}:{job_id}:status          # DISPATCHED, PROCESSING, COMPLETE, FAILED
{namespace}:{job_id}:started_at
{namespace}:{job_id}:completed_at
{namespace}:{job_id}:result_count
```

---

## Critical Gaps for Phase 4.3

### Gap 1: Resilience Components Need Redis Backing

| Component | Current | Impact | Required Change |
|-----------|---------|--------|-----------------|
| Circuit Breaker | In-memory | Each worker has own state | Move to Redis |
| Rate Limiter | In-memory | 10 workers × 10 req/min = 100 | Global Redis bucket |
| Checkpoint | Per-process files | Write race conditions | Coordinate via Redis |

**Priority**: HIGH - Must fix before multi-worker

### Gap 2: SQLite Write Contention

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Single writer at a time | Bottleneck with 10+ agents | Max 3-5 concurrent writes |
| No connection pooling | Overhead | Implement pooling |
| Undecorated reads | Silent failures | Add @retry_on_busy |
| Hard 5.0s delay cap | Cascading timeouts | Dynamic delays |

**Priority**: MEDIUM - Works but needs monitoring

### Gap 3: No Scraping Celery Tasks

| Current | Needed |
|---------|--------|
| Sequential loop in main.py | `dispatch_site_scraping_task` |
| No progress tracking | Redis keys like proxy tasks |
| No parallel sites | Celery group for multiple sites |

**Priority**: HIGH - Core of Phase 4.3

### Gap 4: LLM Rate Limiting

| Current | Needed |
|---------|--------|
| Blocking calls in scraper | Async LLM enrichment phase |
| No rate limiting | Central queue |
| Low cache hit rate | Pre-deduplicate descriptions |

**Priority**: LOW - Can disable LLM for parallel scraping

---

## Recommended Phase 4.3 Implementation

### Step 1: Redis-Backed Resilience (Pre-requisite)

```python
# New: resilience/redis_circuit_breaker.py
class RedisCircuitBreaker:
    def can_request(self, domain):
        state = redis.hget(f"circuit:{domain}", "state")
        return state != "OPEN"

    def record_failure(self, domain, block_type):
        # Atomic increment + state check
        with redis.pipeline() as pipe:
            pipe.hincrby(f"circuit:{domain}", "failures", 1)
            pipe.hset(f"circuit:{domain}", "last_block", block_type)
            failures = pipe.execute()[0]
            if failures >= CIRCUIT_BREAKER_FAIL_MAX:
                redis.hset(f"circuit:{domain}", "state", "OPEN")
```

### Step 2: Scraping Celery Tasks

```python
# New: scraping/tasks.py

@celery_app.task(bind=True)
def scrape_site_task(self, site_name, start_urls):
    """Dispatch scraping for one site."""
    job_id = f"scrape_{site_name}_{uuid4().hex[:8]}"
    scraper = get_scraper(site_name)

    # Phase 1: Collect listing URLs
    all_listing_urls = []
    for start_url in start_urls:
        urls = collect_listing_urls(scraper, start_url)
        all_listing_urls.extend(urls)

    # Phase 2: Dispatch chunk workers
    chunks = chunk_list(all_listing_urls, 50)
    init_redis_progress(job_id, len(chunks))

    workers = group([
        scrape_chunk_task.s(chunk, job_id, site_name)
        for chunk in chunks
    ])
    workflow = chord(workers, aggregate_results_task.s(job_id, site_name))
    result = workflow.apply_async()

    return {"job_id": job_id, "chord_id": result.id, "total_urls": len(all_listing_urls)}


@celery_app.task(soft_time_limit=600, time_limit=720)
def scrape_chunk_task(urls, job_id, site_name):
    """Scrape a chunk of listing URLs."""
    scraper = get_scraper(site_name)
    results = []

    for url in urls:
        try:
            html = fetch_listing_page(url)
            listing = scraper.extract_listing(html, url)
            results.append(listing)
        except Exception as e:
            results.append({"url": url, "error": str(e)})

    redis.incr(f"scrape:{job_id}:completed")
    return results


@celery_app.task
def aggregate_results_task(all_results, job_id, site_name):
    """Finalize: save to DB, run dedup, mark complete."""
    listings = [r for chunk in all_results for r in chunk if "error" not in r]

    # Save to database (batched)
    save_listings_batch(listings)

    # Cross-site deduplication
    run_fingerprint_matching(listings)

    # Mark complete
    redis.set(f"scrape:{job_id}:status", "COMPLETE")
    redis.set(f"scrape:{job_id}:result_count", len(listings))

    return {"job_id": job_id, "saved": len(listings)}
```

### Step 3: Orchestrator Extension

```python
# Add to orchestrator.py

def start_site_scraping(self, site_name, start_urls):
    """Dispatch site scraping task and return job metadata."""
    from scraping.tasks import scrape_site_task
    result = scrape_site_task.delay(site_name, start_urls)
    return {"task_id": result.id, "site": site_name}

def get_site_progress(self, job_id):
    """Get scraping progress from Redis."""
    return {
        "total": int(redis.get(f"scrape:{job_id}:total_chunks") or 0),
        "completed": int(redis.get(f"scrape:{job_id}:completed") or 0),
        "status": redis.get(f"scrape:{job_id}:status") or "UNKNOWN",
    }

def scrape_all_sites_parallel(self, sites_config):
    """Dispatch all sites in parallel."""
    from celery import group
    from scraping.tasks import scrape_site_task

    tasks = group([
        scrape_site_task.s(site, urls)
        for site, urls in sites_config.items()
    ])
    result = tasks.apply_async()
    return {"group_id": result.id}
```

### Step 4: Main.py Integration

```python
# Updated main.py flow

def run_auto_mode():
    with Orchestrator() as orch:
        orch.start_redis()
        orch.start_celery()
        orch.wait_for_proxies()
        orch.start_mubeng()

        # Load sites config
        sites = load_start_urls()

        # Option A: Sequential (current, for testing)
        if os.getenv("PARALLEL_SCRAPING") != "true":
            for site, urls in sites.items():
                scrape_site_sequential(site, urls)

        # Option B: Parallel via Celery (Phase 4.3)
        else:
            result = orch.scrape_all_sites_parallel(sites)
            orch.wait_for_all_sites_completion(result["group_id"])

        print_summary()
```

---

## Testing Strategy

### Unit Tests
- Redis-backed circuit breaker state transitions
- Redis-backed rate limiter token acquisition
- Celery task serialization/deserialization
- Chunk splitting logic

### Integration Tests
- End-to-end scraping task with mock scrapers
- Progress tracking accuracy
- Cross-site deduplication after parallel scraping
- Checkpoint recovery simulation

### Load Tests
- 10 concurrent workers scraping same site
- SQLite write contention under load
- Redis memory usage with many progress keys

---

## Configuration Changes

### New Settings (config/settings.py)

```python
# Phase 4.3 settings
SCRAPING_CHUNK_SIZE = 50           # URLs per worker task
SCRAPING_SOFT_TIME_LIMIT = 600     # 10 min
SCRAPING_HARD_TIME_LIMIT = 720     # 12 min
PARALLEL_SCRAPING_ENABLED = False  # Feature flag

# Redis-backed resilience
REDIS_CIRCUIT_BREAKER_DB = 2
REDIS_RATE_LIMITER_DB = 2
```

### New Redis Key Patterns

```
scrape:{job_id}:total_chunks
scrape:{job_id}:completed
scrape:{job_id}:status
scrape:{job_id}:started_at
scrape:{job_id}:result_count

circuit:{domain}:state
circuit:{domain}:failures
circuit:{domain}:opened_at
circuit:{domain}:last_block

ratelimit:{domain}:tokens
ratelimit:{domain}:last_refill
```

---

## Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `scraping/tasks.py` | Celery tasks for scraping |
| `scraping/redis_keys.py` | Key builders for scraping progress |
| `resilience/redis_circuit_breaker.py` | Redis-backed circuit breaker |
| `resilience/redis_rate_limiter.py` | Redis-backed rate limiter |

### Modified Files
| File | Changes |
|------|---------|
| `orchestrator.py` | Add site scraping methods |
| `main.py` | Add parallel scraping mode |
| `celery_app.py` | Register scraping tasks |
| `config/settings.py` | New configuration |
| `data/data_store_main.py` | Add batch operations |

---

## Success Criteria

Phase 4.3 is complete when:

1. **Parallel Scraping Works**
   - Multiple sites scraped concurrently via Celery
   - Progress tracked in Redis per-site
   - Results aggregated correctly

2. **Resilience is Distributed**
   - Circuit breaker state shared across workers
   - Rate limiting enforced globally
   - Checkpoints coordinated

3. **Data Integrity Maintained**
   - No duplicate listings from race conditions
   - Cross-site deduplication works
   - SQLite handles concurrent writes without failures

4. **Monitoring Enabled**
   - Progress visible via orchestrator API
   - Metrics collected (success rate, avg time)
   - Alerts on failures

---

## Related Documents

- [orchestration_scraping.md](orchestration_scraping.md) - Scraper architecture
- [orchestration_existing.md](orchestration_existing.md) - Current orchestrator patterns
- [orchestration_proxies.md](orchestration_proxies.md) - Celery task templates
- [orchestration_resilience.md](orchestration_resilience.md) - State sharing gaps
- [orchestration_data.md](orchestration_data.md) - SQLite concurrency
- [orchestration_celery_main.md](orchestration_celery_main.md) - Execution flow
- [orchestration_llm.md](orchestration_llm.md) - LLM integration considerations
