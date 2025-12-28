# Module Validation Synthesis

**Date**: 2025-12-28
**Purpose**: Pre-Celery integration validation - consolidated findings
**Agents**: 6 parallel architect-review agents

---

## Executive Summary

All 6 modules were validated for correctness before Phase 4.3 Celery integration. The codebase is **architecturally sound** for single-process operation. For multi-worker Celery deployment, **3 critical issues** must be fixed and **3 modules** need Redis backing.

---

## Validation Results Overview

| Module | Status | Verdict |
|--------|--------|---------|
| Scraping | PASS | Ready for Celery task wrapping |
| Resilience | CONDITIONAL | Needs Redis backing for distributed mode |
| Data | CONDITIONAL | Fix critical issues before 10+ workers |
| Proxy/Celery | PASS | Patterns reusable for scraping tasks |
| Orchestrator | PASS | One bug to fix, needs site registry extension |
| LLM | CONDITIONAL | Needs rate limiting and thread-safety |

---

## Critical Issues (Must Fix Before Phase 4.3)

### 1. Orchestrator: Timeout Not Forwarded

**File**: `orchestrator.py` line 522

```python
# Fix this:
return self.wait_for_refresh_completion(mtime_before, min_count, timeout=timeout, task_id=task_id)
```

**Impact**: Redis polling can loop infinitely with `timeout=0`

---

### 2. Data: Module-Level Init Race Condition

**File**: `data/data_store_main.py` lines 1316-1320

```python
# Current (dangerous):
init_db()
migrate_listings_schema()
# ... runs on import, 10 workers race

# Fix: Move to explicit startup script with file lock
```

**Impact**: Schema corruption, "database is locked" on startup

---

### 3. Data: Read Functions Unprotected

**File**: `data/data_store_main.py` - all `get_*` functions

```python
# Add @retry_on_busy() to:
get_listing_by_url()
get_listings()
get_listing_count()
# ... and other read functions
```

**Impact**: Reads fail during write contention

---

## Modules Needing Redis Backing

### Circuit Breaker (`resilience/circuit_breaker.py`)

**Current**: In-memory singleton per worker process
**Problem**: Worker A blocks domain, Worker B doesn't know
**Solution**: Store state in Redis with `circuit:{domain}` key

### Rate Limiter (`resilience/rate_limiter.py`)

**Current**: In-memory token bucket per worker process
**Problem**: 4 workers x 10 req/min = 40 req/min (intended: 10)
**Solution**: Redis-backed global token bucket OR use Celery's `rate_limit`

### LLM Rate Limiting (`llm/llm_main.py`)

**Current**: No rate limiting to Ollama
**Problem**: 10 workers flood Ollama (handles 2-5 req/s max)
**Solution**: Add semaphore or separate LLM into async enrichment task

---

## What Works Correctly

### Scraping Module
- Scrapers correctly decoupled: `extract_listing(html, url)` takes HTML input
- async_fetcher properly implemented with circuit breaker + rate limiter
- Semaphore-based concurrency control works

### Proxy/Celery Patterns
- Chord pattern: `(group | callback).apply_async()` correct
- Redis INCR atomic for parallel counter updates
- RLock for thread-safety, fcntl for multi-process file access
- **Can be directly copied for scraping tasks**

### Orchestrator
- Context manager lifecycle correct
- Stale process cleanup on startup
- Multi-stage fallback (chord -> Redis -> file)
- Dynamic timeout calculation

### LLM Module
- Correctly decoupled (optional, gap-fill only)
- Exception handling won't crash workers
- Redis caching with graceful degradation

---

## Recommended Phase 4.3 Implementation Order

### Step 1: Critical Fixes (Before Any Celery Work)

1. Fix timeout forwarding in `orchestrator.py:522`
2. Move DB init out of module-level to startup script
3. Add `@retry_on_busy()` to read functions
4. Increase `SQLITE_BUSY_RETRIES` from 3 to 5

### Step 2: Choose Rate Limiting Strategy

**Option A**: Use Celery's built-in `rate_limit='10/m'` per task
- Simpler, no code changes to rate_limiter.py
- Per-worker, not global (may exceed if many workers)

**Option B**: Redis-backed rate limiter
- More accurate global rate limiting
- Requires code changes

**Recommendation**: Start with Option A, monitor, upgrade to B if needed

### Step 3: Choose Circuit Breaker Strategy

**Option A**: Keep in-memory, accept per-worker isolation
- Worker A's circuit open doesn't help Worker B
- Fast failure still works within each worker

**Option B**: Redis-backed circuit breaker
- Shared state across all workers
- More complex, more reliable

**Recommendation**: Option B for production reliability

### Step 4: Create Scraping Celery Tasks

Copy patterns from `proxies/tasks.py`:

```python
# scraping/tasks.py
@celery_app.task(bind=True)
def dispatch_site_scraping(self, site_name, urls):
    job_id = self.request.id
    chunks = [urls[i:i+25] for i in range(0, len(urls), 25)]

    # Initialize Redis tracking
    r.setex(f"scraping:{job_id}:status", 3600, "DISPATCHED")

    # Create chord
    workers = group(scrape_chunk.s(chunk, job_id) for chunk in chunks)
    callback = aggregate_results.s(job_id)
    (workers | callback).apply_async()
```

### Step 5: Extend Orchestrator

Add site registry and lifecycle methods:
- `start_site_scraper(site_name) -> job_id`
- `get_site_progress(site_name) -> dict`
- `stop_site_scraper(site_name)`

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `scraping/tasks.py` | Celery task definitions |
| `scraping/redis_keys.py` | Redis key patterns (copy from proxies) |

### Modify

| File | Changes |
|------|---------|
| `orchestrator.py:522` | Add `timeout=timeout` parameter |
| `data/data_store_main.py` | Move init to startup script, add retry to reads |
| `config/settings.py` | `SQLITE_BUSY_RETRIES = 5` |
| `celery_app.py:29` | Add `"scraping.tasks"` to include list |
| `resilience/circuit_breaker.py` | Optional: Redis backing |
| `llm/llm_main.py` | Add semaphore for rate limiting |

---

## Validation Complete

All 6 validation reports created in `docs/research/`:
- `validation_scraping.md`
- `validation_resilience.md`
- `validation_data.md`
- `validation_proxies.md`
- `validation_orchestrator.md`
- `validation_llm.md`

**Next step**: Create Phase 4.3 implementation spec based on these findings.
