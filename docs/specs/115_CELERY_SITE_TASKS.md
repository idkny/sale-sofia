# Spec 115: Phase 4.3 - Celery Site Tasks

**Status**: Draft
**Author**: Instance 2
**Created**: 2025-12-28
**Priority**: P0 (Core infrastructure)
**Phase**: 4.3 of Crawler Validation & Enhancement

---

## Problem Statement

The scraper currently runs sites sequentially in a single process. For production:
- 2 sites take 2x time (no parallelism)
- Single failure blocks all sites
- No visibility into per-site progress
- Resilience components (circuit breaker, rate limiter) don't share state across workers

**Goal**: Parallel site scraping via Celery with shared resilience state.

---

## Research Summary

Based on validation research (`docs/research/validation_*.md`):

| Module | Status | Action Required |
|--------|--------|-----------------|
| Scraping | READY | Wrap in Celery tasks |
| Resilience | BROKEN for distributed | Redis backing required |
| Data | CONDITIONAL | Fix 3 critical issues |
| Proxy/Celery | READY | Copy patterns to scraping |
| Orchestrator | READY | One bug fix + extensions |
| LLM | CONDITIONAL | Add rate limiting |

---

## Pre-requisites (Must Complete First)

### Critical Fix 1: Timeout Forwarding

**File**: `orchestrator.py:522`

```python
# Current (BUG):
return self.wait_for_refresh_completion(mtime_before, min_count, task_id=task_id)

# Fixed:
return self.wait_for_refresh_completion(mtime_before, min_count, timeout=timeout, task_id=task_id)
```

**Impact**: Without fix, Redis polling can loop infinitely.

---

### Critical Fix 2: Module-Level Init Race

**File**: `data/data_store_main.py:1316-1320`

```python
# Current (DANGEROUS - runs on import):
init_db()
migrate_listings_schema()
init_viewings_table()

# Fixed: Move to explicit function, call from startup script
def initialize_database():
    """Call once from main.py before spawning workers."""
    with FileLock(DB_PATH + ".init.lock"):
        init_db()
        migrate_listings_schema()
        init_viewings_table()
```

**Impact**: 10 workers importing simultaneously causes schema corruption.

---

### Critical Fix 3: Read Function Protection

**File**: `data/data_store_main.py`

Add `@retry_on_busy()` decorator to all read functions:
- `get_listing_by_url()`
- `get_listings()`
- `get_listing_count()`
- `get_all_urls()`
- Other `get_*` functions

**Impact**: Reads fail during write contention without retry.

---

### Critical Fix 4: Increase Retry Count

**File**: `config/settings.py`

```python
# Current:
SQLITE_BUSY_RETRIES = 3

# Changed:
SQLITE_BUSY_RETRIES = 5
```

---

## Phase 4.3.1: Redis-Backed Circuit Breaker

### Why Needed

Current: In-memory singleton per worker process
Problem: Worker A blocks domain, Worker B doesn't know

### Implementation

**New file**: `resilience/redis_circuit_breaker.py`

```python
"""Redis-backed circuit breaker for distributed workers."""
import redis
import time
from config.settings import (
    CIRCUIT_BREAKER_FAIL_MAX,
    CIRCUIT_BREAKER_RESET_TIMEOUT,
    REDIS_HOST, REDIS_PORT, REDIS_DB
)

class RedisCircuitBreaker:
    """
    Circuit breaker with Redis-backed state.

    States: CLOSED (normal) -> OPEN (blocked) -> HALF_OPEN (testing)

    Redis keys per domain:
        circuit:{domain}:state       - CLOSED|OPEN|HALF_OPEN
        circuit:{domain}:failures    - consecutive failure count
        circuit:{domain}:opened_at   - timestamp when opened
        circuit:{domain}:last_block  - block type (cloudflare, captcha, etc)
    """

    def __init__(self):
        self.redis = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
            decode_responses=True
        )
        self.fail_max = CIRCUIT_BREAKER_FAIL_MAX
        self.reset_timeout = CIRCUIT_BREAKER_RESET_TIMEOUT

    def _key(self, domain: str, field: str) -> str:
        return f"circuit:{domain}:{field}"

    def can_request(self, domain: str) -> bool:
        """Check if requests to domain are allowed."""
        state = self.redis.get(self._key(domain, "state")) or "CLOSED"

        if state == "CLOSED":
            return True

        if state == "OPEN":
            opened_at = float(self.redis.get(self._key(domain, "opened_at")) or 0)
            if time.time() - opened_at >= self.reset_timeout:
                # Transition to HALF_OPEN
                self.redis.set(self._key(domain, "state"), "HALF_OPEN")
                return True
            return False

        if state == "HALF_OPEN":
            # Allow limited test requests
            return True

        return True  # Fail-open

    def record_success(self, domain: str):
        """Record successful request."""
        state = self.redis.get(self._key(domain, "state")) or "CLOSED"

        if state == "HALF_OPEN":
            # Close circuit on success
            pipe = self.redis.pipeline()
            pipe.set(self._key(domain, "state"), "CLOSED")
            pipe.set(self._key(domain, "failures"), 0)
            pipe.execute()
        elif state == "CLOSED":
            # Reset failure count
            self.redis.set(self._key(domain, "failures"), 0)

    def record_failure(self, domain: str, block_type: str = "unknown"):
        """Record failed request, possibly opening circuit."""
        state = self.redis.get(self._key(domain, "state")) or "CLOSED"

        if state == "HALF_OPEN":
            # Re-open on failure during test
            pipe = self.redis.pipeline()
            pipe.set(self._key(domain, "state"), "OPEN")
            pipe.set(self._key(domain, "opened_at"), time.time())
            pipe.set(self._key(domain, "last_block"), block_type)
            pipe.execute()
            return

        # Increment failures atomically
        failures = self.redis.incr(self._key(domain, "failures"))

        if failures >= self.fail_max:
            pipe = self.redis.pipeline()
            pipe.set(self._key(domain, "state"), "OPEN")
            pipe.set(self._key(domain, "opened_at"), time.time())
            pipe.set(self._key(domain, "last_block"), block_type)
            pipe.execute()

    def get_state(self, domain: str) -> dict:
        """Get current circuit state for monitoring."""
        return {
            "domain": domain,
            "state": self.redis.get(self._key(domain, "state")) or "CLOSED",
            "failures": int(self.redis.get(self._key(domain, "failures")) or 0),
            "opened_at": self.redis.get(self._key(domain, "opened_at")),
            "last_block": self.redis.get(self._key(domain, "last_block")),
        }


# Singleton instance
_redis_circuit_breaker = None

def get_redis_circuit_breaker() -> RedisCircuitBreaker:
    global _redis_circuit_breaker
    if _redis_circuit_breaker is None:
        _redis_circuit_breaker = RedisCircuitBreaker()
    return _redis_circuit_breaker
```

### Settings Addition

**File**: `config/settings.py`

```python
# Redis-backed resilience (Phase 4.3)
REDIS_CIRCUIT_BREAKER_ENABLED = True  # Feature flag
```

### Migration Strategy

1. Add feature flag `REDIS_CIRCUIT_BREAKER_ENABLED`
2. In `resilience/__init__.py`, return Redis or in-memory based on flag
3. Test with flag off (current behavior)
4. Enable for Celery workers

---

## Phase 4.3.2: Redis-Backed Rate Limiter

### Why Needed

Current: In-memory token bucket per worker
Problem: 4 workers x 10 req/min = 40 req/min (intended: 10)

### Implementation

**New file**: `resilience/redis_rate_limiter.py`

```python
"""Redis-backed rate limiter for distributed workers."""
import redis
import time
from config.settings import DOMAIN_RATE_LIMITS, REDIS_HOST, REDIS_PORT, REDIS_DB

class RedisRateLimiter:
    """
    Token bucket rate limiter with Redis-backed state.

    Redis keys per domain:
        ratelimit:{domain}:tokens     - current token count (float)
        ratelimit:{domain}:last_update - last refill timestamp
    """

    def __init__(self):
        self.redis = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
            decode_responses=True
        )
        self.rate_limits = DOMAIN_RATE_LIMITS

    def _key(self, domain: str, field: str) -> str:
        return f"ratelimit:{domain}:{field}"

    def _get_rate(self, domain: str) -> float:
        return self.rate_limits.get(domain, self.rate_limits.get("default", 10))

    def acquire(self, domain: str, blocking: bool = True) -> bool:
        """
        Acquire a token for the domain.

        Args:
            domain: Target domain
            blocking: If True, wait for token. If False, return immediately.

        Returns:
            True if token acquired, False if non-blocking and no token available.
        """
        rate_per_minute = self._get_rate(domain)
        max_tokens = rate_per_minute  # Bucket size = rate

        while True:
            # Atomic token acquisition using Lua script
            acquired = self._try_acquire(domain, rate_per_minute, max_tokens)

            if acquired:
                return True

            if not blocking:
                return False

            # Wait before retry (outside Redis call)
            time.sleep(1.0)

    def _try_acquire(self, domain: str, rate: float, max_tokens: float) -> bool:
        """Attempt atomic token acquisition."""
        lua_script = """
        local tokens_key = KEYS[1]
        local last_update_key = KEYS[2]
        local rate = tonumber(ARGV[1])
        local max_tokens = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        -- Get current state
        local tokens = tonumber(redis.call('GET', tokens_key) or max_tokens)
        local last_update = tonumber(redis.call('GET', last_update_key) or now)

        -- Refill tokens
        local elapsed = now - last_update
        local refill = elapsed * (rate / 60.0)
        tokens = math.min(max_tokens, tokens + refill)

        -- Try to consume
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('SET', tokens_key, tokens)
            redis.call('SET', last_update_key, now)
            return 1
        else
            redis.call('SET', tokens_key, tokens)
            redis.call('SET', last_update_key, now)
            return 0
        end
        """

        result = self.redis.eval(
            lua_script,
            2,
            self._key(domain, "tokens"),
            self._key(domain, "last_update"),
            rate,
            max_tokens,
            time.time()
        )

        return result == 1

    async def acquire_async(self, domain: str) -> bool:
        """Async version using asyncio.sleep."""
        import asyncio

        rate_per_minute = self._get_rate(domain)
        max_tokens = rate_per_minute

        while True:
            acquired = self._try_acquire(domain, rate_per_minute, max_tokens)
            if acquired:
                return True
            await asyncio.sleep(1.0)


# Singleton
_redis_rate_limiter = None

def get_redis_rate_limiter() -> RedisRateLimiter:
    global _redis_rate_limiter
    if _redis_rate_limiter is None:
        _redis_rate_limiter = RedisRateLimiter()
    return _redis_rate_limiter
```

### Settings Addition

```python
# config/settings.py
REDIS_RATE_LIMITER_ENABLED = True  # Feature flag
```

---

## Phase 4.3.3: Scraping Celery Tasks

### Pattern Source

Copy from `proxies/tasks.py` which has working:
- Dispatcher/Worker/Callback pattern
- Redis progress tracking
- Chord-based workflow

### Implementation

**New file**: `scraping/tasks.py`

```python
"""Celery tasks for parallel site scraping."""
import uuid
import redis
from celery import group, chord

from celery_app import celery_app
from config.settings import REDIS_HOST, REDIS_PORT
from config.scraping_config import load_scraping_config
from scraping.redis_keys import ScrapingKeys

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


@celery_app.task(bind=True)
def dispatch_site_scraping(self, site_name: str, start_urls: list) -> dict:
    """
    Dispatcher: Collect listing URLs and dispatch chunk workers.

    Args:
        site_name: Site identifier (e.g., "imot.bg")
        start_urls: List of category/search page URLs to crawl

    Returns:
        {"job_id": str, "chord_id": str, "total_urls": int}
    """
    from websites import get_scraper

    job_id = f"scrape_{site_name}_{uuid.uuid4().hex[:8]}"
    config = load_scraping_config(site_name)
    scraper = get_scraper(site_name)

    # Phase 1: Collect all listing URLs from start pages
    all_listing_urls = []
    for start_url in start_urls:
        urls = scraper.collect_listing_urls(start_url)
        all_listing_urls.extend(urls)

    # Deduplicate
    all_listing_urls = list(set(all_listing_urls))

    if not all_listing_urls:
        r.setex(ScrapingKeys.status(job_id), 3600, "COMPLETE")
        r.setex(ScrapingKeys.result_count(job_id), 3600, 0)
        return {"job_id": job_id, "total_urls": 0, "status": "NO_URLS"}

    # Phase 2: Split into chunks
    chunk_size = config.get("chunk_size", 25)
    chunks = [all_listing_urls[i:i+chunk_size] for i in range(0, len(all_listing_urls), chunk_size)]

    # Initialize Redis progress tracking
    r.setex(ScrapingKeys.status(job_id), 3600, "DISPATCHED")
    r.setex(ScrapingKeys.total_chunks(job_id), 3600, len(chunks))
    r.setex(ScrapingKeys.completed_chunks(job_id), 3600, 0)
    r.setex(ScrapingKeys.total_urls(job_id), 3600, len(all_listing_urls))

    # Phase 3: Create chord (workers | callback)
    workers = group([
        scrape_chunk.s(chunk, job_id, site_name)
        for chunk in chunks
    ])
    callback = aggregate_results.s(job_id, site_name)

    workflow = chord(workers, callback)
    result = workflow.apply_async()

    return {
        "job_id": job_id,
        "chord_id": result.id,
        "total_urls": len(all_listing_urls),
        "total_chunks": len(chunks),
    }


@celery_app.task(
    bind=True,
    soft_time_limit=600,  # 10 min soft limit
    time_limit=720,       # 12 min hard limit
    max_retries=2,
    default_retry_delay=30,
)
def scrape_chunk(self, urls: list, job_id: str, site_name: str) -> list:
    """
    Worker: Scrape a chunk of listing URLs.

    Uses Redis-backed circuit breaker and rate limiter.
    Returns list of extracted listings (or error dicts).
    """
    from websites import get_scraper
    from scraping.async_fetcher import fetch_page
    from resilience import get_circuit_breaker, get_rate_limiter

    scraper = get_scraper(site_name)
    circuit_breaker = get_circuit_breaker()
    rate_limiter = get_rate_limiter()

    results = []
    domain = site_name  # Simplified; extract from URL if needed

    for url in urls:
        try:
            # Check circuit breaker
            if not circuit_breaker.can_request(domain):
                results.append({"url": url, "error": "circuit_open", "skipped": True})
                continue

            # Rate limit
            rate_limiter.acquire(domain, blocking=True)

            # Fetch and extract
            html = fetch_page(url)
            listing = scraper.extract_listing(html, url)

            circuit_breaker.record_success(domain)
            results.append(listing)

        except Exception as e:
            circuit_breaker.record_failure(domain, str(type(e).__name__))
            results.append({"url": url, "error": str(e)})

    # Update progress
    r.incr(ScrapingKeys.completed_chunks(job_id))

    return results


@celery_app.task(bind=True)
def aggregate_results(self, chunk_results: list, job_id: str, site_name: str) -> dict:
    """
    Callback: Aggregate results from all workers, save to DB.

    Args:
        chunk_results: List of lists from each scrape_chunk worker
        job_id: Job identifier
        site_name: Site name for logging

    Returns:
        {"job_id": str, "saved": int, "errors": int}
    """
    from data.data_store_main import upsert_listing

    r.set(ScrapingKeys.status(job_id), "AGGREGATING")

    # Flatten results
    all_results = []
    for chunk in chunk_results:
        if chunk:  # Handle None from failed tasks
            all_results.extend(chunk)

    # Separate successes and errors
    listings = [r for r in all_results if "error" not in r]
    errors = [r for r in all_results if "error" in r]

    # Save to database
    saved_count = 0
    for listing in listings:
        try:
            upsert_listing(listing)
            saved_count += 1
        except Exception as e:
            errors.append({"url": listing.get("url"), "error": f"db_save: {e}"})

    # Mark complete
    r.setex(ScrapingKeys.status(job_id), 3600, "COMPLETE")
    r.setex(ScrapingKeys.result_count(job_id), 3600, saved_count)
    r.setex(ScrapingKeys.error_count(job_id), 3600, len(errors))

    return {
        "job_id": job_id,
        "site": site_name,
        "saved": saved_count,
        "errors": len(errors),
        "total_processed": len(all_results),
    }


@celery_app.task
def scrape_all_sites(sites_config: dict) -> dict:
    """
    Dispatch scraping for all sites in parallel.

    Args:
        sites_config: {"imot.bg": ["url1", "url2"], "bazar.bg": ["url3"]}

    Returns:
        {"group_id": str, "jobs": [{"site": str, "job_id": str}]}
    """
    tasks = group([
        dispatch_site_scraping.s(site, urls)
        for site, urls in sites_config.items()
    ])

    result = tasks.apply_async()

    return {
        "group_id": result.id,
        "sites": list(sites_config.keys()),
    }
```

**New file**: `scraping/redis_keys.py`

```python
"""Redis key patterns for scraping progress tracking."""


class ScrapingKeys:
    """Redis key builders for scraping job progress."""

    PREFIX = "scraping"

    @classmethod
    def status(cls, job_id: str) -> str:
        """Job status: DISPATCHED, PROCESSING, AGGREGATING, COMPLETE, FAILED"""
        return f"{cls.PREFIX}:{job_id}:status"

    @classmethod
    def total_chunks(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:total_chunks"

    @classmethod
    def completed_chunks(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:completed_chunks"

    @classmethod
    def total_urls(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:total_urls"

    @classmethod
    def result_count(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:result_count"

    @classmethod
    def error_count(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:error_count"

    @classmethod
    def started_at(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:started_at"

    @classmethod
    def completed_at(cls, job_id: str) -> str:
        return f"{cls.PREFIX}:{job_id}:completed_at"
```

---

## Phase 4.3.4: Celery App Registration

**File**: `celery_app.py`

```python
# Add to include list:
celery_app = Celery(
    "sale_sofia",
    broker=...,
    include=[
        "proxies.tasks",
        "scraping.tasks",  # NEW
    ],
)
```

---

## Phase 4.3.5: Orchestrator Extensions

**File**: `orchestrator.py`

Add methods:

```python
def start_site_scraping(self, site_name: str, start_urls: list) -> dict:
    """Dispatch site scraping task."""
    from scraping.tasks import dispatch_site_scraping
    result = dispatch_site_scraping.delay(site_name, start_urls)
    return {"task_id": result.id, "site": site_name}

def start_all_sites_scraping(self, sites_config: dict) -> dict:
    """Dispatch all sites in parallel."""
    from scraping.tasks import scrape_all_sites
    result = scrape_all_sites.delay(sites_config)
    return {"group_id": result.id}

def get_scraping_progress(self, job_id: str) -> dict:
    """Get scraping job progress from Redis."""
    from scraping.redis_keys import ScrapingKeys
    return {
        "job_id": job_id,
        "status": self.redis.get(ScrapingKeys.status(job_id)) or "UNKNOWN",
        "total_chunks": int(self.redis.get(ScrapingKeys.total_chunks(job_id)) or 0),
        "completed_chunks": int(self.redis.get(ScrapingKeys.completed_chunks(job_id)) or 0),
        "result_count": int(self.redis.get(ScrapingKeys.result_count(job_id)) or 0),
        "error_count": int(self.redis.get(ScrapingKeys.error_count(job_id)) or 0),
    }
```

---

## Phase 4.3.6: Main.py Integration

**File**: `main.py`

```python
def run_auto_mode():
    with Orchestrator() as orch:
        orch.start_redis()
        orch.start_celery()
        orch.wait_for_proxies()
        orch.start_mubeng()

        # Initialize database ONCE before workers touch it
        from data.data_store_main import initialize_database
        initialize_database()

        # Load sites
        sites = load_start_urls()

        if os.getenv("PARALLEL_SCRAPING", "false").lower() == "true":
            # Parallel via Celery
            result = orch.start_all_sites_scraping(sites)
            wait_for_scraping_completion(orch, result["group_id"])
        else:
            # Sequential (current behavior, for testing)
            for site, urls in sites.items():
                scrape_site_sequential(site, urls)

        print_summary()
```

---

## Settings Additions

**File**: `config/settings.py`

```python
# Phase 4.3: Celery Site Tasks
PARALLEL_SCRAPING_ENABLED = False        # Feature flag
SCRAPING_CHUNK_SIZE = 25                 # URLs per worker task
SCRAPING_SOFT_TIME_LIMIT = 600           # 10 min soft limit
SCRAPING_HARD_TIME_LIMIT = 720           # 12 min hard limit

# Redis-backed resilience
REDIS_CIRCUIT_BREAKER_ENABLED = False    # Enable after testing
REDIS_RATE_LIMITER_ENABLED = False       # Enable after testing

# SQLite tuning for concurrent workers
SQLITE_BUSY_RETRIES = 5                  # Increased from 3
```

---

## Files Summary

### New Files

| File | Purpose |
|------|---------|
| `resilience/redis_circuit_breaker.py` | Redis-backed circuit breaker |
| `resilience/redis_rate_limiter.py` | Redis-backed rate limiter |
| `scraping/tasks.py` | Celery task definitions |
| `scraping/redis_keys.py` | Redis key patterns |

### Modified Files

| File | Changes |
|------|---------|
| `orchestrator.py:522` | Fix timeout forwarding |
| `orchestrator.py` | Add scraping orchestration methods |
| `data/data_store_main.py` | Move init to function, add retry to reads |
| `config/settings.py` | New settings |
| `celery_app.py` | Register scraping tasks |
| `main.py` | Add parallel scraping mode |
| `resilience/__init__.py` | Factory for Redis vs in-memory |

---

## Testing Strategy

### Unit Tests

| Test | Location |
|------|----------|
| Redis circuit breaker state transitions | `tests/resilience/test_redis_circuit_breaker.py` |
| Redis rate limiter token acquisition | `tests/resilience/test_redis_rate_limiter.py` |
| Celery task serialization | `tests/scraping/test_tasks.py` |
| Chunk splitting logic | `tests/scraping/test_tasks.py` |
| Redis key patterns | `tests/scraping/test_redis_keys.py` |

### Integration Tests

| Test | Description |
|------|-------------|
| End-to-end scraping task | Mock scraper, real Celery, verify DB saves |
| Progress tracking | Verify Redis keys update correctly |
| Circuit breaker sharing | Two workers, one triggers open, verify other sees it |
| Rate limiter sharing | Two workers, verify combined rate ≤ limit |

---

## Implementation Order

```
1. Critical Fixes (Pre-requisites)
   ├── Fix orchestrator.py:522
   ├── Fix data_store_main.py init
   ├── Add @retry_on_busy() to reads
   └── Increase SQLITE_BUSY_RETRIES

2. Redis-Backed Resilience
   ├── Create redis_circuit_breaker.py
   ├── Create redis_rate_limiter.py
   ├── Update resilience/__init__.py factory
   └── Write tests

3. Scraping Celery Tasks
   ├── Create scraping/tasks.py
   ├── Create scraping/redis_keys.py
   ├── Update celery_app.py
   └── Write tests

4. Integration
   ├── Add orchestrator methods
   ├── Update main.py
   ├── Integration tests
   └── Feature flag testing
```

---

## Success Criteria

Phase 4.3 is complete when:

1. **Pre-requisites Fixed**
   - Timeout forwarding bug fixed
   - DB init race condition fixed
   - Read functions have retry decorator

2. **Redis-Backed Resilience Working**
   - Circuit breaker state shared across workers
   - Rate limiter enforced globally
   - Feature flags allow gradual rollout

3. **Scraping Tasks Functional**
   - `dispatch_site_scraping` creates chord workflow
   - `scrape_chunk` processes URLs with resilience
   - `aggregate_results` saves to database
   - Progress visible via Redis keys

4. **Integration Complete**
   - Orchestrator can dispatch parallel scraping
   - main.py supports `PARALLEL_SCRAPING=true`
   - All tests passing

> **Task tracking**: See [TASKS.md](../tasks/TASKS.md) Phase 4.3 for checkboxes

---

## Related Documents

- [validation_synthesis.md](../research/validation_synthesis.md) - Validation findings
- [orchestration_synthesis.md](../research/orchestration_synthesis.md) - Implementation patterns
- [114_SCRAPER_MONITORING.md](114_SCRAPER_MONITORING.md) - Monitoring (recommended before 4.3)
- [TASKS.md](../tasks/TASKS.md) - Task tracking
