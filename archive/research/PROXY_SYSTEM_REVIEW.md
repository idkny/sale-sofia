# Proxy System Architecture Review

**Created**: 2025-12-30 (Session 55)
**Updated**: 2025-12-30 (Session 57)
**Author**: Instance 2
**Status**: ✅ Phase 1 & 2 Cleanup Complete

---

## Executive Summary

Comprehensive review of the proxy system including Celery, Redis, and all tools/processes.

**Key Finding**: The system was simplified in Session 50. Mubeng server is NO LONGER used for scraping. Proxies are selected directly from `ScoredProxyPool` with per-request liveness checks via httpx.

### Session 57 Cleanup Completed (Phase 2)

| Change | Lines Removed |
|--------|---------------|
| Deleted `proxies/mubeng_manager.py` | ~114 lines |
| Deleted `proxies/proxies_main.py` | ~192 lines |
| Fixed `async_fetcher.py` - proxy now required | - |
| Fixed `scraping/tasks.py` - uses ScoredProxyPool | - |
| Updated settings.py comment | - |
| Added test fixture in conftest.py | - |
| **Phase 2 Total** | **~306 lines** |

### Session 56 Cleanup Completed (Phase 1)

| Change | Lines Removed |
|--------|---------------|
| Solution F code from `proxy_scorer.py` | ~122 lines |
| Unused facades from `proxies_main.py` | ~25 lines |
| 6-hour Beat schedule from `celery_app.py` | ~12 lines |
| **Phase 1 Total** | **~159 lines** |

**Grand Total Removed**: ~465 lines of dead code

**Proxy refresh is now on-demand only** via `scrape_and_check_chain_task.delay()`.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PROXY SYSTEM ARCHITECTURE                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Layer 5: INFRASTRUCTURE                                                     │
│  ├── Redis → Message broker (db=0), result backend (db=1), progress tracking │
│  │   └── Config: celery_app.py:16-22                                         │
│  └── orchestrator.py → Manages Redis, Celery lifecycle, proxy refresh wait   │
│      └── wait_for_proxies(), trigger_proxy_refresh()                         │
│                                                                              │
│  Layer 4: CELERY TASK LAYER (Proxy Refresh - On-Demand)                      │
│  ├── scrape_new_proxies_task → Runs PSC binary to gather raw proxies         │
│  │   └── proxies/tasks.py:51-91                                              │
│  ├── check_scraped_proxies_task → Dispatcher: splits proxies into chunks     │
│  │   └── proxies/tasks.py:93-138                                             │
│  ├── check_proxy_chunk_task → Worker: mubeng liveness + anonymity + quality  │
│  │   └── proxies/tasks.py:280-295                                            │
│  ├── process_check_results_task → Callback: aggregates results, saves file   │
│  │   └── proxies/tasks.py:391-415                                            │
│  └── scrape_and_check_chain_task → Manual trigger (no Beat schedule)         │
│      └── proxies/tasks.py:418-432                                            │
│                                                                              │
│  Layer 3: PROXY MANAGEMENT LAYER                                             │
│  ├── ScoredProxyPool → Runtime selection with failure tracking               │
│  │   ├── select_proxy() → Random selection                                   │
│  │   ├── record_result() → Track consecutive failures                        │
│  │   └── remove_proxy() → Auto-prune after MAX_CONSECUTIVE_PROXY_FAILURES    │
│  │   └── proxies/proxy_scorer.py                                             │
│  └── scraping/tasks.py → Parallel scraping with proxy pool integration       │
│      ├── get_proxy_pool() → Singleton proxy pool per worker                  │
│      ├── get_working_proxy() → Get proxy with liveness check                 │
│      └── quick_liveness_check() → httpx ping before use                      │
│                                                                              │
│  Layer 2: SCRAPING INTEGRATION LAYER                                         │
│  ├── quick_liveness_check() → httpx ping before each request                 │
│  │   └── main.py:74-92                                                       │
│  ├── _fetch_search_page() → Fetcher + liveness check + circuit breaker       │
│  │   └── main.py:145-252                                                     │
│  └── _fetch_listing_page() → StealthyFetcher + liveness check                │
│      └── main.py:321-432                                                     │
│                                                                              │
│  Layer 1: EXTERNAL SOURCES                                                   │
│  ├── proxy-scraper-checker (PSC) → Binary at proxies/external/psc            │
│  │   └── Scrapes free proxies from public lists                              │
│  ├── mubeng → Binary at proxies/external/mubeng                              │
│  │   └── Used only in check_proxy_chunk_task for liveness verification       │
│  └── live_proxies.json → Source of truth: proxies/live_proxies.json          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Settings

| Setting | Value | Location | Used By |
|---------|-------|----------|---------|
| MUBENG_PROXY | :8089 | settings.py:12 | *NOTE 1 |
| MIN_PROXIES_TO_START | 1 | settings.py:16 | proxies |
| MIN_PROXIES_FOR_SCRAPING | 10 | settings.py:20 | main,orch |
| MAX_URL_RETRIES | 3 | settings.py:23 | main.py |
| PROXY_TIMEOUT_SECONDS | 45 | settings.py:28 | ALL |
| PROXY_TIMEOUT_MS | 45000 | settings.py:34 | Stealthy |
| MAX_CONSECUTIVE_PROXY_FAILURES | 3 | settings.py:41 | scorer |
| PARALLEL_SCRAPING_ENABLED | False | settings.py:207 | main.py |
| SCRAPING_CHUNK_SIZE | 25 | settings.py:210 | tasks |

*NOTE 1: MUBENG_PROXY only used when PARALLEL_SCRAPING_ENABLED=True or via ScraplingMixin methods (not currently used in main flow)

### Celery Settings (celery_app.py)

| Setting | Value | Location |
|---------|-------|----------|
| worker_concurrency | 8 | celery_app.py:56 |
| task_time_limit | 30 min | celery_app.py:48 |
| result_expires | 1 hour | celery_app.py:52 |

*Note: Beat schedule removed in Session 56. Proxy refresh is now on-demand only.*

### Task-specific Limits

| Setting | Value | Location |
|---------|-------|----------|
| check_proxy_chunk_task soft | 13 min | tasks.py:280 |
| check_proxy_chunk_task hard | 15 min | tasks.py:280 |
| SCRAPING_SOFT_TIME_LIMIT | 10 min | settings.py:213 |
| SCRAPING_HARD_TIME_LIMIT | 12 min | settings.py:214 |

---

## Data Flow

### Flow A: Proxy Refresh (On-Demand)

```
1. Manual Trigger
   └→ scrape_and_check_chain_task.delay()
      └→ chain(scrape_new_proxies_task, check_scraped_proxies_task)

2. Scrape Phase
   └→ scrape_new_proxies_task
      └→ subprocess: PSC binary
         └→ OUTPUT: proxies/external/psc/out/proxies_pretty.json

3. Dispatch Phase
   └→ check_scraped_proxies_task (DISPATCHER)
      ├→ Read proxies_pretty.json (~1000+ proxies)
      ├→ Split into chunks of 100
      ├→ Set Redis progress keys (job_id, total_chunks, status)
      └→ Dispatch Celery chord: group(workers) | callback

4. Check Phase (PARALLEL - 8 workers)
   └→ check_proxy_chunk_task × N
      ├→ _run_mubeng_liveness_check() → mubeng --check
      ├→ _enrich_with_anonymity() → HTTP request to IP check service
      ├→ _filter_by_real_ip_subnet() → Remove same-subnet proxies
      ├→ _check_quality_for_non_transparent() → Target site check
      └→ _update_redis_progress() → Increment completed_chunks

5. Aggregate Phase
   └→ process_check_results_task (CALLBACK)
      ├→ Flatten all chunk results
      ├→ Filter out Transparent proxies
      ├→ Merge with existing live_proxies.json
      ├→ Sort by timeout (fastest first)
      └→ OUTPUT: proxies/live_proxies.json + live_proxies.txt
```

### Flow B: Scraping (Sequential Mode - Default)

```
1. Startup
   └→ main.py → run_auto_mode()
      ├→ Orchestrator.__enter__() → cleanup_stale_processes()
      ├→ start_redis() → Health check via PING
      ├→ start_celery() → Start worker+beat
      └→ wait_for_proxies() → Trigger refresh if < MIN_PROXIES_FOR_SCRAPING

2. Initialize Pool
   └→ _initialize_proxy_pool()
      └→ ScoredProxyPool(live_proxies.json)
         ├→ Load proxies from JSON
         └→ Initialize failure tracking dict

3. Per-Request Flow
   └→ _fetch_search_page() or _fetch_listing_page()
      ├→ STEP 1: proxy_pool.select_proxy() → Random selection
      ├→ STEP 2: quick_liveness_check(proxy_url) → httpx ping
      │  └→ If DEAD → remove_proxy() → try next (up to 10 times)
      ├→ STEP 3: Fetcher.get() or StealthyFetcher.fetch()
      │  └→ Pass live proxy directly (no mubeng!)
      ├→ STEP 4: detect_soft_block(html)
      │  └→ If blocked → record_failure() → raise BlockedException
      └→ STEP 5: record_result(success=True/False)
         └→ If 3 consecutive failures → auto-remove proxy

4. Between Sites
   └→ _ensure_min_proxies()
      └→ If proxy_count < 10 → trigger_proxy_refresh() + wait
```

---

## File Structure

```
proxies/
├── __init__.py              → proxy_to_url() helper
├── tasks.py                 → Celery tasks for proxy refresh
│   ├── scrape_new_proxies_task
│   ├── check_scraped_proxies_task
│   ├── check_proxy_chunk_task
│   ├── process_check_results_task
│   └── scrape_and_check_chain_task
├── redis_keys.py            → Key patterns: proxy_refresh:{job_id}:*
├── proxy_scorer.py          → ScoredProxyPool class (runtime selection)
├── anonymity_checker.py     → IP leak detection service
├── quality_checker.py       → Target site reachability tests
├── get_free_proxies.py      → Only used in tests
├── get_paid_proxies.py      → Only used in tests
├── live_proxies.json        → OUTPUT: Validated proxy list
├── live_proxies.txt         → OUTPUT: Same as JSON, one URL per line
└── external/
    ├── psc/                 → proxy-scraper-checker binary
    └── mubeng/              → mubeng binary (used for --check liveness only)

scraping/
├── tasks.py                 → Celery tasks for parallel scraping
│   ├── dispatch_site_scraping → Collect URLs, dispatch workers
│   ├── scrape_chunk → Fetch URLs with proxy pool
│   ├── aggregate_results → Save to database
│   ├── get_proxy_pool() → Singleton proxy pool per worker
│   └── get_working_proxy() → Get proxy with liveness check
├── async_fetcher.py         → Async HTTP fetching (proxy required)
└── redis_keys.py            → Key patterns: scraping:{job_id}:*

DELETED FILES (Session 57):
├── proxies/proxies_main.py  → Was facades (all dead code)
└── proxies/mubeng_manager.py → Was mubeng server control (dead)
```

---

## Celery Tasks

### Proxy Refresh Tasks (proxies/tasks.py)

| Task | Location | Trigger | Action |
|------|----------|---------|--------|
| scrape_new_proxies_task | :51 | Chain | Runs PSC binary |
| check_scraped_proxies_task | :93 | Chain | Dispatcher - chunks + chord |
| check_proxy_chunk_task | :280 | Chord group | Worker - liveness + quality |
| process_check_results_task | :391 | Chord callback | Aggregate + save |
| scrape_and_check_chain_task | :418 | Manual | Meta-task (on-demand) |

### Scraping Tasks (scraping/tasks.py) - Only if PARALLEL_SCRAPING_ENABLED

| Task | Location | Action |
|------|----------|--------|
| dispatch_site_scraping | :40 | Collect URLs, dispatch workers |
| scrape_chunk | :126 | Scrape listing URLs |
| aggregate_results | :189 | Save to database |
| scrape_all_sites | :253 | Dispatch all sites in parallel |

---

## Redis Usage

### Database Allocation

- DB 0: Celery Broker (message queue)
- DB 1: Celery Result Backend (task results)

### Proxy Refresh Keys (proxies/redis_keys.py)

| Key Pattern | Type | TTL | Description |
|-------------|------|-----|-------------|
| proxy_refresh:{job_id}:total_chunks | int | 1h | Total chunk count |
| proxy_refresh:{job_id}:completed | int | 1h | Chunks completed |
| proxy_refresh:{job_id}:status | string | 1h | DISPATCHED/PROCESSING/COMPLETE/FAILED |
| proxy_refresh:{job_id}:started_at | int | 1h | Unix timestamp |
| proxy_refresh:{job_id}:completed_at | int | 1h | Unix timestamp |
| proxy_refresh:{job_id}:result_count | int | 1h | Final proxy count |

### Scraping Keys (scraping/redis_keys.py) - Only if PARALLEL_SCRAPING enabled

| Key Pattern | Type | TTL | Description |
|-------------|------|-----|-------------|
| scraping:{job_id}:status | string | 1h | COLLECTING/DISPATCHED/etc |
| scraping:{job_id}:total_chunks | int | 1h | URL chunk count |
| scraping:{job_id}:completed_chunks | int | 1h | Chunks done |
| scraping:{job_id}:total_urls | int | 1h | Total URLs found |
| scraping:{job_id}:result_count | int | 1h | Listings saved |
| scraping:{job_id}:error_count | int | 1h | Failed extractions |

---

## Findings

### Dead Code

#### 1. proxy_scorer.py - Solution F Code (~100 lines) ✅ DELETED

**Location**: proxies/proxy_scorer.py:63-351 (was)
**Status**: Deleted in Session 56

| Item | Status |
|------|--------|
| `_proxy_order: list[str]` | ✅ Deleted |
| `_index_map: dict[str, int]` | ✅ Deleted |
| `_mubeng_proxy_file: Optional[Path]` | ✅ Deleted |
| `set_proxy_order()` | ✅ Deleted |
| `get_proxy_index()` | ✅ Deleted |
| `set_mubeng_proxy_file()` | ✅ Deleted |
| `_rebuild_index_map()` | ✅ Deleted |
| `_save_proxy_file()` | ✅ Deleted |

#### 2. proxies_main.py - ENTIRE FILE DELETED ✅

**Location**: proxies/proxies_main.py (was ~192 lines)
**Status**: Deleted in Session 57

| Function | Status |
|----------|--------|
| `setup_mubeng_rotator()` | ✅ Deleted |
| `stop_mubeng_rotator()` | ✅ Deleted |
| `get_and_filter_proxies()` | ✅ Deleted |
| `_check_and_refresh_proxies()` | ✅ Deleted |
| `validate_proxy()` | ✅ Deleted |

**Reason**: All functions were dead code - only called by deleted code or not used anywhere.

#### 3. mubeng_manager.py - ENTIRE FILE DELETED ✅

**Location**: proxies/mubeng_manager.py (was ~114 lines)
**Status**: Deleted in Session 57

| Function | Status |
|----------|--------|
| `start_mubeng_rotator_server()` | ✅ Deleted |
| `stop_mubeng_rotator_server()` | ✅ Deleted |
| `find_free_port()` | ✅ Deleted |

**Reason**: Only imported by proxies_main.py (deleted). Mubeng binary is still used for `--check` mode in proxies/tasks.py but doesn't need these functions.

#### 5. get_free_proxies.py & get_paid_proxies.py

**Location**: proxies/get_free_proxies.py, proxies/get_paid_proxies.py

Only used in: tests/test_paid_proxies.py. Not used in production code.

### Remaining Inconsistencies

1. **MUBENG_PROXY Setting (settings.py:12)**
   - Now only used by ScraplingMixin in scrapling_base.py
   - Neither main.py nor scraping/tasks.py use MUBENG_PROXY
   - Consider removing if ScraplingMixin is updated

2. **ScraplingMixin vs Direct Fetcher**
   - ScraplingMixin.fetch_stealth() uses MUBENG_PROXY + Camoufox
   - main.py uses StealthyFetcher directly with proxy from pool
   - scraping/tasks.py uses async_fetcher with proxy from pool
   - Consider unifying to always use proxy pool

3. **Documentation References**
   - scrapling_base.py mentions "Integration with mubeng proxy rotation" but main scraping flow doesn't use mubeng

---

## Recommended Actions

### Priority 1 (Low Risk, High Impact) ✅ COMPLETE

| Action | Lines | Risk | Status |
|--------|-------|------|--------|
| Delete Solution F code from proxy_scorer.py | ~122 | LOW | ✅ Done (Session 56) |
| Delete unused facades from proxies_main.py | ~25 | LOW | ✅ Done (Session 56) |
| Remove 6-hour Beat schedule | ~12 | LOW | ✅ Done (Session 56) |

### Priority 2 (Medium Risk) ✅ COMPLETE

| Action | Lines | Risk | Status |
|--------|-------|------|--------|
| Delete mubeng_manager.py | ~114 | MED | ✅ Done (Session 57) |
| Delete proxies_main.py | ~192 | MED | ✅ Done (Session 57) |
| Fix async_fetcher.py to require proxy | - | MED | ✅ Done (Session 57) |
| Fix scraping/tasks.py to use proxy pool | - | MED | ✅ Done (Session 57) |

### Priority 3 (Optional - Future Enhancement)

| Action | Impact |
|--------|--------|
| Remove MUBENG_PROXY from settings | Only affects ScraplingMixin |
| Unify Fetcher Usage | Consolidate ScraplingMixin vs direct Fetcher approaches |

---

## Estimated Impact

- **Phase 1 Dead Code Removed**: ~159 lines (Session 56)
- **Phase 2 Dead Code Removed**: ~306 lines (Session 57)
- **Grand Total Removed**: ~465 lines
- **Test Impact**: None - all 1036 tests pass
- **Risk Level**: Low (verified)

---

## Status: COMPLETE

1. ~~Review this document~~ ✅
2. ~~Approve P1 cleanup tasks~~ ✅
3. ~~Execute P1 cleanup~~ ✅ (Session 56)
4. ~~Approve P2 cleanup tasks~~ ✅
5. ~~Execute P2 cleanup~~ ✅ (Session 57)
6. ~~Run pytest after each deletion~~ ✅ (1036 passed)
7. ~~Update research and tasks files~~ ✅

**Decision Made**: Keep parallel scraping mode but fix to use proxy pool (not MUBENG_PROXY).

**Remaining**: P3 is optional - unify ScraplingMixin to use proxy pool instead of MUBENG_PROXY.
