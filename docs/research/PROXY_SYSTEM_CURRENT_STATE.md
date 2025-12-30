# Proxy System Current State (Post-Cleanup)

**Date**: 2025-12-30
**Updated**: Session 60 (PSC timeout fix)
**Context**: Deep analysis after sessions 53-58 cleanup (~470 lines removed)

---

## Executive Summary

The proxy system has been significantly simplified. It now consists of **6 core files** (~590 lines total) plus external tools. The architecture follows a clean separation:

1. **Refresh Pipeline** (Celery async) → Scrapes, validates, saves proxies
2. **Runtime Pool** (Thread-safe) → Selects proxies, tracks failures, auto-prunes
3. **Quality Checkers** → Anonymity detection, IP service validation

---

## File Structure

```
proxies/
├── __init__.py              # 3 lines   - proxy_to_url() helper
├── proxy_scorer.py          # 230 lines - ScoredProxyPool runtime class
├── tasks.py                 # 432 lines - Celery refresh pipeline
├── anonymity_checker.py     # 290 lines - Anonymity level detection
├── quality_checker.py       # 436 lines - IP service & target validation
├── redis_keys.py            # 39 lines  - Redis key patterns
├── get_free_proxies.py      # Stub (logic in tasks.py)
├── get_paid_proxies.py      # PacketStream.io (unused currently)
├── live_proxies.json        # Output: validated proxy list
├── live_proxies.txt         # Output: URL format list
└── external/
    ├── mubeng/              # Go binary for liveness checks
    └── proxy-scraper-checker/ # Rust binary for scraping free proxies
```

---

## Component Deep-Dive

### 1. ScoredProxyPool (`proxy_scorer.py`)

**Purpose**: Runtime proxy selection with failure tracking and auto-pruning.

**Thread Safety**: Uses `threading.RLock()` for concurrent access (Celery workers).

```python
class ScoredProxyPool:
    def __init__(self, proxies_file: Path):
        self.proxies: list[dict] = []       # Proxy dicts from JSON
        self.scores: dict[str, dict] = {}   # Failure tracking
        self.lock = threading.RLock()       # Thread-safe access
```

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `select_proxy()` | Random selection from pool (thread-safe) |
| `record_result(proxy_key, success)` | Track success/failure, auto-prune on threshold |
| `remove_proxy(proxy_key)` | Manual removal from pool |
| `get_proxy_url()` | Convenience: select + format to URL |
| `reload_proxies()` | Reload from JSON after refresh |
| `get_stats()` | Export statistics |

**Failure Tracking Logic**:
```python
def record_result(self, proxy_key: str, success: bool):
    if success:
        self.scores[proxy_key]["failures"] = 0  # Reset on success
    else:
        self.scores[proxy_key]["failures"] += 1
        if failures >= MAX_CONSECUTIVE_PROXY_FAILURES:
            self.remove_proxy(proxy_key)  # Auto-prune
```

**Settings**:
- `MAX_CONSECUTIVE_PROXY_FAILURES` (config/settings.py) - Threshold for auto-removal

---

### 2. Celery Refresh Pipeline (`tasks.py`)

**Purpose**: Async proxy refresh via scrape → validate → save pipeline.

**Architecture**:
```
scrape_new_proxies_task()
         │
         ▼
check_scraped_proxies_task()  ◄─── DISPATCHER
         │
         ├─────────────────────────────┐
         ▼                             ▼
check_proxy_chunk_task()    check_proxy_chunk_task()  (parallel)
         │                             │
         └──────────┬──────────────────┘
                    ▼
process_check_results_task()  ◄─── AGGREGATOR
         │
         ▼
live_proxies.json + live_proxies.txt
```

**Task Details**:

#### `scrape_new_proxies_task()`
- Runs `proxy-scraper-checker` (PSC) Rust binary
- PSC does **both scraping AND checking** internally:
  - Scrapes from 70+ proxy sources (HTTP, SOCKS4, SOCKS5)
  - Checks each proxy for liveness (4096 concurrent checks)
  - Determines anonymity, geolocation, ASN
  - Sorts by speed
- Output: `proxy_checker/out/proxies_pretty.json`
- Timeout: `PSC_TIMEOUT_SECONDS` (50 min) - PSC typically takes 20-40 minutes

#### `check_scraped_proxies_task()` [DISPATCHER]
- Splits proxies into chunks of 100
- Initializes Redis progress tracking
- Creates Celery chord: `group(workers) | callback`
- Returns: `{job_id, chord_id, total_chunks, status}`

#### `check_proxy_chunk_task()` [WORKER - runs in parallel]
- Timeout: 13min soft, 15min hard
- Pipeline per chunk:
  1. **Liveness** → `_run_mubeng_liveness_check()` - mubeng binary, 45s/proxy
  2. **Anonymity** → `_enrich_with_anonymity()` - judge URLs
  3. **Subnet Filter** → `_filter_by_real_ip_subnet()` - reject same /24
  4. **Quality** → `_check_quality_for_non_transparent()` - IP services
  5. **Progress** → `_update_redis_progress()` - increment counter

#### `process_check_results_task()` [AGGREGATOR]
- Flattens results from all chunks
- Filters out Transparent proxies
- Merges with existing `live_proxies.json` (new overrides old)
- Sorts by timeout (fastest first)
- Saves to JSON and TXT files
- Marks job complete in Redis

#### `scrape_and_check_chain_task()` [META-TASK]
- Convenience: `chain(scrape.s(), check.s()).delay()`
- For manual refresh triggers

---

### 3. Anonymity Checker (`anonymity_checker.py`)

**Purpose**: Detect proxy anonymity level via HTTP header analysis.

**Anonymity Levels**:
| Level | Description | Quality |
|-------|-------------|---------|
| Transparent | Real IP visible in response | ❌ Worst (filtered out) |
| Anonymous | IP hidden but proxy headers present | ✓ Good |
| Elite | IP hidden, no proxy headers | ✓✓ Best |

**Detection Method**:
1. Send request to judge URL (httpbin.org/headers, etc.)
2. Check if real IP appears in response → Transparent
3. Check for privacy headers (VIA, X-FORWARDED-FOR, etc.) → Anonymous
4. No leaks → Elite

**Privacy Headers Checked**:
```python
PRIVACY_HEADERS = [
    "VIA", "X-FORWARDED-FOR", "X-FORWARDED", "FORWARDED-FOR",
    "FORWARDED-FOR-IP", "FORWARDED", "X-REAL-IP", "CLIENT-IP",
    "X-CLIENT-IP", "PROXY-CONNECTION", "X-PROXY-ID",
    "X-BLUECOAT-VIA", "X-ORIGINATING-IP",
]
```

**Judge URLs** (fallback chain):
1. httpbin.org/headers (HTTPS)
2. httpbin.org/headers (HTTP)
3. httpbin.io/headers (HTTPS)
4. httpbin.io/headers (HTTP)
5. ifconfig.me/all.json

**Key Functions**:
- `get_real_ip()` - Fetch real IP (cached for session)
- `check_proxy_anonymity()` - Check single proxy
- `enrich_proxy_with_anonymity()` - Add fields to proxy dict

---

### 4. Quality Checker (`quality_checker.py`)

**Purpose**: Validate proxies work with IP services (target site check disabled).

**IP Check Services** (fallback chain):
```python
IP_CHECK_SERVICES = [
    {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"},
    {"url": "https://icanhazip.com", "type": "text"},
    {"url": "https://ifconfig.me/ip", "type": "text"},
    {"url": "https://checkip.amazonaws.com", "type": "text"},
    {"url": "https://ipinfo.io/ip", "type": "text"},
]
```

**Critical Validation**:
- Reject if exit_ip matches real IP's /24 subnet (proxy broken, routing locally)

**Class: `QualityChecker`**:
| Method | Purpose |
|--------|---------|
| `check_ip_service(proxy_url)` | Test against IP services, return (passed, exit_ip) |
| `check_target_site(proxy_url)` | Test against imot.bg (DISABLED - too slow) |
| `check_all(proxy_url)` | Combined check (returns dict) |

**Note**: Target site check (`check_target_site`) is currently **skipped** in `check_all()` because free proxies are too slow/unreliable for imot.bg.

---

### 5. Redis Progress Tracking (`redis_keys.py`)

**Pattern**: `proxy_refresh:{job_id}:{suffix}`

| Key | Purpose |
|-----|---------|
| `:total_chunks` | Total chunks to process |
| `:completed_chunks` | Chunks completed (increments) |
| `:status` | DISPATCHED → PROCESSING → COMPLETE |
| `:started_at` | Unix timestamp |
| `:completed_at` | Unix timestamp |
| `:result_count` | Final proxy count |

**TTL**: 1 hour (auto-cleanup)

---

## Data Flow Diagrams

### Flow 1: Proxy Refresh (Async)

```
┌─────────────────┐
│  orchestrator   │  Triggers: chain(scrape.s(), check.s())
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ scrape_new_     │  Runs PSC Rust binary (20-40 min)
│ proxies_task    │  PSC: scrape 70+ sources + check 4096 concurrent
│                 │  → proxies_pretty.json
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ check_scraped_  │  Dispatcher: splits into chunks
│ proxies_task    │  Creates chord: group | callback
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│Chunk 1│ │Chunk 2│ │Chunk 3│ │Chunk N│  Parallel workers
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │        │        │
    │   Each chunk pipeline:    │
    │   1. Mubeng liveness     │
    │   2. Anonymity check     │
    │   3. Subnet filter       │
    │   4. Quality check       │
    │                          │
    └────────┬─────────────────┘
             ▼
┌─────────────────┐
│ process_check_  │  Aggregator: flatten, filter, merge
│ results_task    │  → live_proxies.json
└─────────────────┘
```

### Flow 2: Runtime Proxy Usage (Sync)

```
┌─────────────┐
│   main.py   │  _initialize_proxy_pool()
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   ScoredProxyPool   │  Loads live_proxies.json
│   (singleton)       │  Initializes failure tracking
└──────┬──────────────┘
       │
       ▼ For each page fetch:
┌─────────────────────┐
│  pool.select_proxy()│  Random selection (thread-safe)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ quick_liveness_     │  httpx request to imot.bg
│ check(proxy_url)    │
└──────┬──────────────┘
       │
       ├─── Success ──▶ Use proxy for scraping
       │                    │
       │                    ▼
       │               pool.record_result(key, success)
       │                    │
       │                    ├─── success=True: failures=0
       │                    └─── success=False: failures++
       │                              │
       │                              ├─── failures < threshold: continue
       │                              └─── failures >= threshold: auto-remove
       │
       └─── Failure ──▶ pool.remove_proxy(proxy_key)
                        Loop back to select_proxy()
```

---

## Entry Points

### 1. main.py (CLI)

```python
# Line 39: Import
from proxies.proxy_scorer import ScoredProxyPool

# Line 656-667: Initialize
def _initialize_proxy_pool() -> Optional[ScoredProxyPool]:
    proxy_pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")
    stats = proxy_pool.get_stats()
    return proxy_pool

# Line 671-707: Ensure minimum proxies
def _ensure_min_proxies(proxy_pool, orch):
    stats = proxy_pool.get_stats()
    if stats["total_proxies"] < MIN_PROXIES_FOR_SCRAPING:
        # Trigger refresh via orchestrator
        proxy_pool.reload_proxies()  # After refresh
```

**Usage in scraping**:
- `_fetch_search_page()` (lines 148-244): Select proxy, fetch, record result
- `_fetch_listing_page()` (lines 324-424): Select proxy, fetch, record result

### 2. scraping/tasks.py (Celery)

```python
# Line 21: Import
from proxies.proxy_scorer import ScoredProxyPool

# Line 27: Singleton
_proxy_pool: ScoredProxyPool | None = None

# Line 48-55: Get or init
def get_proxy_pool() -> ScoredProxyPool:
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ScoredProxyPool(proxy_file)
    return _proxy_pool

# Line 68-81: Get working proxy with liveness check
def get_working_proxy() -> str | None:
    pool = get_proxy_pool()
    for _ in range(MAX_PROXY_ATTEMPTS):
        proxy_url = pool.select_proxy()
        if quick_liveness_check(proxy_url):
            return proxy_url
        pool.remove_proxy(proxy_url)
```

### 3. orchestrator.py

```python
# Lines 36-41: Redis key imports
from proxies.redis_keys import (
    job_completed_chunks_key, job_result_count_key,
    job_status_key, job_total_chunks_key,
)

# Line 79-116: Progress tracking
def get_refresh_progress():
    # Query Redis for proxy refresh job status

# Line 505: Task imports
from proxies.tasks import check_scraped_proxies_task, scrape_new_proxies_task
```

---

## External Dependencies

### 1. Mubeng Binary (`external/mubeng/`)

**Purpose**: Fast parallel proxy liveness checking.

**Usage** (in `_run_mubeng_liveness_check()`):
```bash
mubeng --check -f input.txt -o output.txt -t 45s
```

**Why used**:
- Fast: Checks many proxies in parallel
- Reliable: Handles timeouts gracefully
- Note: Requires PTY wrapper (`script -q /dev/null -c`) to prevent hanging

### 2. Proxy-Scraper-Checker (`external/proxy-scraper-checker/`)

**Purpose**: Scrape AND check free proxies from multiple sources.

**What it does**:
- Scrapes from 70+ proxy list sources (HTTP, SOCKS4, SOCKS5)
- Checks each proxy for liveness (`max_concurrent_checks = 4096`)
- Determines anonymity level, geolocation, ASN
- Sorts by response speed
- Typical runtime: 20-40 minutes

**Usage** (in `scrape_new_proxies_task()`):
```bash
./proxy-scraper-checker -o proxies_pretty.json
```

**Config**: `external/proxy-scraper-checker/config.toml`

**Output**: JSON array of proxy dicts with host, port, protocol, timeout, geolocation, ASN.

**Note**: PSC already validates proxies, but our pipeline runs additional checks (mubeng liveness, anonymity, quality) because PSC's basic check doesn't guarantee the proxy works for real website scraping.

---

## Configuration

**From `config/settings.py`**:
| Setting | Value | Purpose |
|---------|-------|---------|
| `PSC_TIMEOUT_SECONDS` | 3000 (50 min) | PSC subprocess timeout |
| `PROXY_TIMEOUT_SECONDS` | 45 | HTTP request timeout per proxy |
| `MAX_CONSECUTIVE_PROXY_FAILURES` | 3 | Auto-remove threshold |
| `MIN_PROXIES_FOR_SCRAPING` | 10 | Minimum pool size to start |

**From `paths.py`**:
| Path | Purpose |
|------|---------|
| `PROXIES_DIR` | Proxy module directory |
| `MUBENG_EXECUTABLE_PATH` | Path to mubeng binary |
| `PSC_EXECUTABLE_PATH` | Path to proxy-scraper-checker |

---

## Proxy Data Structure

**In `live_proxies.json`**:
```json
{
    "host": "1.2.3.4",
    "port": 8080,
    "protocol": "http",
    "timeout": 2.5,
    "anonymity": "Elite",
    "anonymity_verified_at": "2025-12-30T10:00:00+00:00",
    "exit_ip": "5.6.7.8",
    "ip_check_passed": true,
    "ip_check_exit_ip": "5.6.7.8",
    "target_passed": null,
    "quality_checked_at": 1735560000.123
}
```

**In `ScoredProxyPool.scores`**:
```python
{
    "1.2.3.4:8080": {
        "failures": 0,
        "last_used": 1735560000.123
    }
}
```

---

## What Was Removed (Sessions 53-58)

| Component | Lines | Why Removed |
|-----------|-------|-------------|
| Solution F (parallel rotation) | ~122 | Unused complexity |
| `mubeng_manager.py` | ~114 | Replaced by direct binary calls |
| `proxies_main.py` | ~192 | Facades consolidated into tasks.py |
| `MUBENG_PROXY` setting | ~5 | No longer needed (param passed) |
| `MIN_PROXIES_TO_START` | ~5 | Dead code |
| 6-hour Beat schedule | ~12 | On-demand refresh only |
| Unused facade functions | ~25 | Dead code |

**Total removed**: ~470 lines

---

## Potential Future Improvements

1. **Remove Mubeng Binary** (TASKS.md)
   - Replace `mubeng --check` with pure Python httpx
   - Eliminates external Go binary dependency
   - See: `/docs/tasks/TASKS.md` - "Remove Mubeng Binary Dependency"

2. **Investigate PSC Anonymity Output** (TASKS.md)
   - PSC may already output anonymity level in `proxies_pretty.json`
   - If yes: remove duplicate `_enrich_with_anonymity()` call from pipeline
   - Would simplify code and reduce processing time

3. **Async Quality Checks**
   - Currently sequential per proxy
   - Could use `asyncio` for parallelism

4. **Target Site Check**
   - Currently disabled (`target_passed = None`)
   - Could re-enable with longer timeouts for premium proxies

---

## Test Coverage

**Unit Tests**:
- `tests/test_proxy_scorer.py` - ScoredProxyPool class
- `tests/test_quality_checker.py` - QualityChecker class
- `tests/test_anonymity_checker.py` - Anonymity detection

**Integration Tests**:
- `tests/conftest.py` - Mock proxy pool fixture
- `tests/test_circuit_breaker_celery_integration.py` - Patches proxy pool
- `tests/test_parallel_scraping_integration.py` - End-to-end with proxies

**Stress Tests**:
- `tests/stress/test_celery_psc.py` - PSC binary tests
- `tests/stress/test3_celery_mubeng.py` - Mubeng rotation tests

---

## Summary

The proxy system is now lean and focused:

| Responsibility | Component | Lines |
|---------------|-----------|-------|
| Runtime selection | `ScoredProxyPool` | 230 |
| Async refresh | `tasks.py` | 432 |
| Anonymity check | `anonymity_checker.py` | 290 |
| Quality check | `quality_checker.py` | 436 |
| Redis keys | `redis_keys.py` | 39 |
| Helper | `__init__.py` | 3 |
| **Total** | | **~1430** |

External tools:
- `mubeng` - Liveness checking (Go binary)
- `proxy-scraper-checker` - Proxy scraping (Rust binary)

The system provides:
- **Thread-safe** proxy selection for concurrent workers
- **Auto-pruning** of failing proxies
- **Async refresh** via Celery pipeline
- **Multi-level validation** (liveness, anonymity, quality)
- **Progress tracking** via Redis
