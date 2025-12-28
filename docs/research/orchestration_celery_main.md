# Orchestration Research: Celery & Main Flow

## Executive Summary

Current execution is **sequential in main.py**. Celery is configured and used for proxy tasks, but not yet for scraping. Phase 4.3 should add site-level Celery tasks using the existing proxy task patterns as templates.

---

## 1. Celery Configuration (celery_app.py)

### Redis Connection
```python
broker = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/1"
```

### Task Configuration
| Setting | Value |
|---------|-------|
| Serialization | JSON |
| Timezone | Europe/Sofia |
| Hard time limit | 30 min |
| Soft time limit | 29 min |
| Result expiration | 1 hour |
| Worker prefetch | 1 (fair distribution) |
| Concurrency | 8 workers |

### Beat Schedule
```python
"refresh-proxies-every-6h": {
    "task": "proxies.tasks.scrape_and_check_chain_task",
    "schedule": crontab(minute=0, hour="*/6"),
    "options": {"queue": "sale_sofia"}
}
```

### Key Patterns in Use
- Celery chains for sequential execution
- Celery groups for parallel execution
- Celery chords (group → callback) for aggregating results
- Redis progress tracking via custom keys

---

## 2. Current Flow in main.py

### Entry Point: `run_auto_mode()`

### Execution Flow
```
1. Load start_urls from config/start_urls.yaml
2. Create Orchestrator context manager
3. _setup_infrastructure():
   - Start Redis (or reuse)
   - Start Celery worker + beat
   - Wait for proxies (min 10)
4. _initialize_proxy_pool():
   - Load live_proxies.json
   - Initialize ScoredProxyPool
5. _start_proxy_rotator():
   - Start mubeng on port 8089
6. Pre-flight checks (3-level recovery):
   - Level 1: Auto-rotation (6 attempts)
   - Level 2: Soft restart mubeng (3 attempts)
   - Level 3: Full proxy refresh (3 attempts)
7. _crawl_all_sites():
   - For each site:
     - Phase 1: _collect_listing_urls()
     - Phase 2: _scrape_listings()
8. _print_summary()
```

---

## 3. Module Coordination

### Config System
| File | Purpose |
|------|---------|
| `config/start_urls.yaml` | Sites/URLs to crawl |
| `config/scraping_defaults.yaml` | Global defaults |
| `config/sites/<site>.yaml` | Per-site overrides |
| `config/settings.py` | Constants |

### Scraper Access
```python
from websites import get_scraper, AVAILABLE_SITES
scraper = get_scraper("imot.bg")  # Factory pattern
```

### Data Persistence
- `data_store_main` - SQLite database
- Change detection via content hashing
- Price history tracking

### Resilience Features
- Circuit breaker (per domain)
- Rate limiter (per domain)
- Retry backoff with jitter
- Checkpoint manager for crash recovery

### Proxy Scoring
- `ScoredProxyPool` tracks performance
- 1.1x on success, 0.5x on failure
- Integrates with X-Proxy-Offset header

---

## 4. Relationship: main.py vs orchestrator.py

### Orchestrator Responsibilities
- Lifecycle management (context manager)
- Redis health checking/starting
- Celery worker health checking/starting
- Proxy availability monitoring
- Proxy refresh triggering via Celery
- Stale process cleanup

### Main.py Responsibilities
- High-level crawl orchestration
- Scraper selection and invocation
- Checkpoint management
- Statistics collection
- Proxy pool initialization/scoring

### Interaction Pattern
```python
with Orchestrator() as orch:
    orch.start_redis()
    orch.start_celery()
    orch.wait_for_proxies()
    # main.py does scraping
    orch.trigger_proxy_refresh()
    orch.wait_for_refresh_completion()
# Context exit: auto-stops all
```

---

## 5. Multi-Site Handling

### Current Approach: Sequential
```python
for site in start_urls:
    for start_url in site.urls:
        scrape_from_start_url(start_url)
```

- Sites processed one at a time
- After each site: clear checkpoint, check proxy health
- No parallel site scraping

---

## 6. Changes Needed for Celery-Based Site Tasks

### Gap 1: No Per-Site Tasks
- Current: main.py manually loops
- Needed: `SiteScrapingTask` in Celery
- Should receive: site, URLs, config → return stats

### Gap 2: Fetcher Integration
- Current: Fetcher runs in main process
- Decide: Move fetching to Celery tasks?
- Issue: I/O bound (good for Celery) but needs proxy coordination

### Gap 3: Shared Resource Coordination
- Proxy pool is in-memory in main process
- Multiple Celery workers can't access directly
- Options:
  - A) Redis-backed proxy pool
  - B) Proxy selection via mubeng (current X-Proxy-Offset)
  - C) Central proxy service

### Gap 4: Progress Tracking
- Current: `proxies/tasks.py` uses Redis progress keys
- Needed: Similar pattern for site task progress
- Track: URLs collected, listings scraped, failures

### Gap 5: Error Handling
- Current: try/catch in main.py
- Needed: Celery task error handling + retry logic
- Consider: soft retries vs hard failures

---

## 7. Entry Points

### Development
```bash
python main.py  # Direct sync execution
```
- Useful for testing, debugging
- Starts infrastructure on demand

### Production-Ready Components
```bash
celery -A celery_app beat              # Scheduler only
celery -A celery_app worker --beat     # Worker + scheduler
celery -A celery_app worker -Q sale_sofia  # Worker only
```

### Missing for Production
- Site scraping tasks (Phase 4.3 adds these)
- Monitoring/observability (Spec 114)
- Deployment configs

---

## 8. Key Architectural Insights

### Existing Strengths
1. **Decoupled architecture** - clear module boundaries
2. **Context manager pattern** - clean resource lifecycle
3. **Redis coordination** - progress tracking, distributed state
4. **Chord/Group patterns** - proven in proxies/tasks.py
5. **Configuration flexibility** - YAML per-site settings

### Critical Patterns to Reuse
1. **Dispatcher + Workers** - from proxies/tasks.py
2. **Redis progress keys** - job_id → total, completed, status
3. **Health check pattern** - ping checks, auto-restart
4. **Chain pattern** - sequential task execution

---

## 9. What Phase 4.3 Must Solve

| Requirement | Current | Needed |
|-------------|---------|--------|
| Task execution | Sequential in main.py | Parallel Celery tasks |
| Proxy coordination | In-memory pool + mubeng | Redis-backed + mubeng |
| Progress tracking | Console output | Redis + orchestrator API |
| Per-site parallelism | None | Celery group |
| Error recovery | try/catch in main.py | Task retries + checkpoint |
| Configuration | Per-site YAML | Same, accessed from workers |

---

## 10. Design Questions for Phase 4.3

1. **Should proxy selection move to Redis?**
   - Currently in-memory `ScoredProxyPool`
   - For distributed workers, need shared state

2. **How deep into scraping should Celery go?**
   - Option A: Task per site (phases 1+2 inside task)
   - Option B: Task per URL batch (more parallelism)
   - Option C: Hybrid (collect phase sync, scrape phase parallel)

3. **Who owns rate limiting and circuit breaker?**
   - Currently per-process in resilience/ modules
   - Need Redis-backed or coordinated state

4. **How to handle checkpoint recovery in distributed scenario?**
   - Current: one checkpoint per site per day
   - Distributed: multiple workers might write same checkpoint

5. **Should proxy refresh happen during long crawl or pre-crawl only?**
   - Current: pre-crawl and mid-crawl if count drops
   - Distributed: need coordination to avoid multiple refreshes
