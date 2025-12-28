# Proxy System Specifications

> Investigation Status: ORCHESTRATION COMPLETE
> Last Updated: 2025-12-23
> Sources Analyzed: Scraper, AutoBiz, Competitor-Intel, sale-sofia (current)

---

## Executive Summary

This document captures findings from analyzing 3 existing proxy implementations to design an improved proxy system for sale-sofia.

**Key Finding:** The orchestration (how tools work together) is as important as individual tool functionality. Each repo has different coordination patterns with distinct strengths/weaknesses.

---

## 1. Current Implementation Analysis

### 1.1 What We Have (sale-sofia)

**Files:**
- `proxies/tasks.py` - Celery tasks (scrape, check chunks, process results)
- `proxies/proxy_validator.py` - Pre-flight check with scoring
- `proxies/anonymity_checker.py` - Header-based anonymity detection
- `proxies/mubeng_manager.py` - Mubeng process management
- `proxies/proxies_main.py` - Setup/teardown functions
- `orchestrator.py` - Service lifecycle management

**Current Flow:**
```
scrape_new_proxies_task (proxy-scraper-checker, 5 min)
    → check_scraped_proxies_task (dispatcher)
        → group(check_proxy_chunk_task * N) (mubeng --check, parallel)
            → process_check_results_task (save to live_proxies.json)
```

**Known Issues:**
1. `wait_for_proxies()` doesn't wait for refresh completion (FIXED - mtime tracking)
2. Pre-flight check was scoring rotator URL instead of proxies (FIXED)
3. No runtime scoring/pruning of bad proxies
4. No proper header-based anonymity verification at runtime

---

## 2. External Implementation Analysis

### 2.1 Scraper Repository

**Architecture:**
- ProxyChecker (pycurl-based validation)
- ProxyService (pool management)
- PaidProxyService (PacketStream.io)
- ProxyOrchestrator (strategy rotation)

**Strengths:**
- Header-based anonymity detection (VIA, X-FORWARDED-FOR, CLIENT-IP, etc.)
- Multi-protocol support (http, https, socks4, socks5)
- Multiple judge URLs with fallback
- ip2c.org country lookup

**Weaknesses:**
- No Celery integration
- Fixed 10-second sleep for refresh (brittle)
- No scoring system
- No async support

**Key Code Pattern - Anonymity Detection:**
```python
PRIVACY_HEADERS = [
    'VIA', 'X-FORWARDED-FOR', 'X-FORWARDED', 'FORWARDED-FOR',
    'FORWARDED-FOR-IP', 'FORWARDED', 'CLIENT-IP', 'PROXY-CONNECTION'
]

def parse_anonymity(self, response_body: str) -> str:
    if self.real_ip in response_body:
        return 'Transparent'
    if any(header in response_body.upper() for header in PRIVACY_HEADERS):
        return 'Anonymous'
    return 'Elite'
```

**Judge URLs:**
- https://azenv.net/
- https://httpbin.org/get
- https://api.myip.com/
- https://ipapi.co/json/

---

### 2.2 AutoBiz Repository

**Architecture:**
- Celery-based multi-stage pipeline
- Mubeng for fast liveness checks
- requests library for quality checks

**Strengths:**
- 3-stage validation pipeline:
  1. Mubeng --check (fast liveness)
  2. ipify.org check (simple liveness)
  3. Google.com check (quality/block detection)
- Celery chord pattern for parallel processing
- Chunked processing (100 proxies per task)

**Weaknesses:**
- No wait for task completion
- Hardcoded values (chunk_size=100, timeout=30s)
- No scoring system
- Relies on scraper output for anonymity (no verification)

**Key Code Pattern - Multi-Stage Pipeline:**
```python
# Stage 1: Fast mubeng check
mubeng_tasks = group(mubeng_check_chunk_task.s(chunk) for chunk in chunks)

# Stage 2+3: Quality checks
quality_tasks = group(sequential_quality_check_task.s(proxy) for proxy in live_proxies)

# Chain with callback
chord(mubeng_tasks)(combine_results | dispatch_quality | process_final)
```

**Validation Targets:**
- Stage 2: https://api.ipify.org?format=json
- Stage 3: https://www.google.com (checks for `<title>Google</title>`)

---

### 2.3 Competitor-Intel Repository

**Architecture:**
- ProxyManager (orchestrator)
- ProxyValidator (async httpx validation)
- RobustProxyTransport (scored pool with auto-pruning)
- PaidProxyService (PacketStream.io)

**Strengths:**
- Weighted random selection based on score
- Automatic pruning (3 failures OR score < 0.01)
- Async validation with httpx
- Exponential backoff on failures

**Weaknesses:**
- Celery tasks referenced but not implemented
- No wait for refresh completion
- No header-based anonymity detection
- Scores not persisted (reset on restart)

**Key Code Pattern - Scoring System:**
```python
class RobustProxyTransport:
    def _initial_score(self, response_time: float) -> float:
        return 1.0 / max(response_time, 0.1)  # Faster = higher score

    def _update_proxy_score(self, proxy: dict, success: bool):
        if success:
            proxy["score"] *= 1.1   # +10% reward
            proxy["failures"] = 0
        else:
            proxy["score"] *= 0.5   # -50% penalty
            proxy["failures"] += 1

        # Auto-prune
        if proxy["failures"] >= 3 or proxy["score"] < 0.01:
            self._proxies.remove(proxy)

    def _select_proxy(self) -> dict:
        total = sum(p["score"] for p in self._proxies)
        weights = [p["score"] / total for p in self._proxies]
        return random.choices(self._proxies, weights=weights, k=1)[0]
```

**IP Check URLs:**
- https://ipinfo.io/json
- https://api.ipify.org?format=json
- https://ifconfig.co/json

---

## 3. Comparison Matrix

| Feature | sale-sofia | Scraper | AutoBiz | Competitor-Intel |
|---------|------------|---------|---------|------------------|
| Celery Integration | ✅ | ❌ | ✅ | ⚠️ Partial |
| Async Validation | ❌ | ❌ | ❌ | ✅ |
| Header Anonymity | ✅ | ✅ | ❌ | ❌ |
| Runtime Scoring | ❌ | ❌ | ❌ | ✅ |
| Auto-Pruning | ❌ | ❌ | ❌ | ✅ |
| Multi-Stage Validation | ❌ | ❌ | ✅ | ❌ |
| Wait for Refresh | ✅ (fixed) | ❌ | ❌ | ❌ |
| Google Quality Check | ❌ | ❌ | ✅ | ❌ |
| Weighted Selection | ❌ | ❌ | ❌ | ✅ |
| Persistent Scores | ❌ | ❌ | ❌ | ❌ |

---

## 4. Recommended Architecture

### 4.1 Hybrid Design

Take the best from each implementation:

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROXY SYSTEM v2                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STAGE 1: Scraping (from AutoBiz)                         │   │
│  │ - proxy-scraper-checker binary                           │   │
│  │ - Celery task: scrape_new_proxies_task                   │   │
│  │ - Output: raw candidates (~1000s)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STAGE 2: Fast Liveness (from AutoBiz)                    │   │
│  │ - mubeng --check (parallel chunks)                       │   │
│  │ - Celery group: check_proxy_chunk_task * N               │   │
│  │ - Output: live proxies (~100-200)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STAGE 3: Anonymity Verification (from Scraper)           │   │
│  │ - Header inspection via judge URLs                       │   │
│  │ - Detect: Transparent / Anonymous / Elite                │   │
│  │ - Filter out Transparent proxies                         │   │
│  │ - Output: anonymous proxies with verified level          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STAGE 4: Quality Check (from AutoBiz)                    │   │
│  │ - Test against target site (or Google)                   │   │
│  │ - Detect blocks/captchas                                 │   │
│  │ - Set google_passed / target_passed flag                 │   │
│  │ - Output: quality-verified proxies                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STAGE 5: Pool Management (from Competitor-Intel)         │   │
│  │ - Initial score = 1.0 / response_time                    │   │
│  │ - Weighted random selection                              │   │
│  │ - Score update: success *= 1.1, failure *= 0.5           │   │
│  │ - Auto-prune: failures >= 3 OR score < 0.01              │   │
│  │ - Persist scores to JSON/Redis                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ RUNTIME: Mubeng Rotator + Pre-flight                     │   │
│  │ - mubeng -a localhost:8089 --rotate-on-error             │   │
│  │ - Pre-flight check before browser (no scoring)           │   │
│  │ - Auto-refresh on failure (wait for mtime change)        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Key Components to Implement

#### 4.2.1 Runtime Proxy Scorer (NEW)
```python
class ProxyScorer:
    """
    Runtime scoring and selection for proxies.
    Inspired by Competitor-Intel's RobustProxyTransport.
    """

    SCORE_SUCCESS_MULTIPLIER = 1.1
    SCORE_FAILURE_MULTIPLIER = 0.5
    MAX_FAILURES = 3
    MIN_SCORE = 0.01

    def __init__(self, proxies: list, scores_file: Path):
        self.proxies = proxies
        self.scores_file = scores_file
        self._load_scores()

    def select_proxy(self) -> dict:
        """Weighted random selection based on score."""
        pass

    def record_success(self, proxy_url: str, response_time: float):
        """Increase score on success."""
        pass

    def record_failure(self, proxy_url: str):
        """Decrease score and potentially prune on failure."""
        pass

    def _prune_if_needed(self, proxy: dict):
        """Remove proxy if failures >= 3 or score < 0.01."""
        pass
```

#### 4.2.2 Enhanced Anonymity Checker (IMPROVE)
```python
class AnonymityChecker:
    """
    Header-based anonymity verification.
    Inspired by Scraper's ProxyChecker.
    """

    PRIVACY_HEADERS = [
        'VIA', 'X-FORWARDED-FOR', 'X-FORWARDED', 'FORWARDED-FOR',
        'FORWARDED-FOR-IP', 'FORWARDED', 'CLIENT-IP', 'PROXY-CONNECTION',
        'X-REAL-IP', 'X-PROXY-ID', 'X-ORIGINATING-IP'
    ]

    JUDGE_URLS = [
        'https://httpbin.org/headers',
        'https://azenv.net/',
        'https://api.myip.com/',
    ]

    def __init__(self):
        self.real_ip = self._get_real_ip()

    def check_anonymity(self, proxy_url: str) -> str:
        """Returns: 'Transparent', 'Anonymous', or 'Elite'"""
        pass

    def _parse_response(self, response_body: str) -> str:
        """Inspect headers in response to determine anonymity."""
        pass
```

#### 4.2.3 Quality Checker (NEW)
```python
class QualityChecker:
    """
    Test proxies against real targets to detect blocks.
    Inspired by AutoBiz's Google check.
    """

    def check_google(self, proxy_url: str) -> bool:
        """Test if proxy can access Google without captcha."""
        pass

    def check_target(self, proxy_url: str, target_url: str) -> bool:
        """Test if proxy can access target site."""
        pass
```

---

## 5. Configuration Parameters

### 5.1 Thresholds (make configurable)

```python
# proxies/config.py

# Pool management
PROXY_VALID_THRESHOLD = 50       # Trigger refresh when pool < this
MIN_LIVE_PROXIES = 5             # Minimum to start scraping
CHUNK_SIZE = 100                 # Proxies per Celery task

# Timeouts
MUBENG_CHECK_TIMEOUT = "5s"      # Fast liveness check
REQUESTS_TIMEOUT = 30            # Quality check timeout
PREFLIGHT_TIMEOUT = 15           # Pre-flight check timeout

# Scoring
SCORE_SUCCESS_MULTIPLIER = 1.1   # +10% on success
SCORE_FAILURE_MULTIPLIER = 0.5   # -50% on failure
MAX_FAILURES = 3                 # Remove after N consecutive failures
MIN_SCORE = 0.01                 # Remove if score below this

# Mubeng rotator
MUBENG_PORT = 8089
MUBENG_MAX_ERRORS = 3
MUBENG_ROTATION_MODE = "random"

# Refresh
REFRESH_TIMEOUT = 600            # Max wait for refresh (10 min)
SCRAPE_INTERVAL = 21600          # Celery beat: every 6 hours
CHECK_INTERVAL = 7200            # Celery beat: every 2 hours
```

### 5.2 Judge URLs (make configurable)

```python
# proxies/config.py

JUDGE_URLS = [
    ("https://httpbin.org/headers", "json"),
    ("https://httpbin.org/ip", "json"),
    ("https://azenv.net/", "text"),
    ("https://api.myip.com/", "json"),
]

IP_CHECK_URLS = [
    ("https://httpbin.org/ip", "json"),
    ("https://icanhazip.com", "text"),
    ("https://checkip.amazonaws.com", "text"),
    ("https://ifconfig.me/ip", "text"),
    ("https://ident.me", "text"),
    ("https://api.ipify.org", "text"),
]
```

---

## 6. Data Structures

### 6.1 Proxy Object (enhanced)

```json
{
  "host": "123.45.67.89",
  "port": 8080,
  "protocol": "http",
  "url": "http://123.45.67.89:8080",

  "timeout": 1.234,
  "country": "US",
  "country_code": "US",

  "anonymity": "Elite",
  "anonymity_verified": true,
  "anonymity_check_time": 1703361600,

  "google_passed": true,
  "target_passed": true,

  "score": 1.5,
  "failures": 0,
  "successes": 10,
  "last_check": 1703361600,
  "last_success": 1703361600,
  "last_failure": null
}
```

### 6.2 Proxy Scores File

```json
{
  "http://123.45.67.89:8080": {
    "score": 1.5,
    "failures": 0,
    "successes": 10,
    "last_check": 1703361600,
    "avg_response_time": 1.234
  }
}
```

---

## 7. Open Questions

> These need to be resolved before implementation

1. **Should we persist scores to Redis instead of JSON file?**
   - Pro: Shared across workers, faster access
   - Con: Additional dependency, more complex

2. **Should runtime scoring be integrated into mubeng or separate?**
   - Option A: Use mubeng --rotate-on-error and track failures separately
   - Option B: Build custom rotator with scoring built-in

3. **How to handle anonymity re-verification?**
   - Option A: Check once during validation, trust forever
   - Option B: Periodic re-check (every N hours)
   - Option C: Re-check on failure

4. **Should we test against target site (imot.bg) or just Google?**
   - Pro: More accurate for our use case
   - Con: Might trigger rate limits/blocks

5. **How to handle paid proxies (PacketStream)?**
   - Current: Separate PaidProxyService
   - Should scoring apply to paid proxies too?

---

## 8. References

### 8.1 Source Repositories
- Scraper: `idkny/Scraper` → `/tmp/scraper-investigation/`
- AutoBiz: `idkny/Auto-Biz` → `/tmp/autobiz-investigation/`
- Competitor-Intel: `idkny/Competitor-Intel` → `/tmp/competitor-investigation/`

### 8.2 Extraction Docs
- `/home/wow/Projects/sale-sofia/extraction/proxies/proxies_Scraper.md`
- `/home/wow/Projects/sale-sofia/extraction/proxies/proxies_AutoBiz.md`
- `/home/wow/Projects/sale-sofia/extraction/proxies/proxies_CompetitorIntel.md`

### 8.3 External Tools
- Mubeng: https://github.com/kitabisa/mubeng
- proxy-scraper-checker: https://github.com/monosans/proxy-scraper-checker
- PacketStream: https://packetstream.io/

---

---

## 10. ORCHESTRATION ANALYSIS

> This section documents HOW tools work together - the coordination, timing, data flow, and synchronization patterns.

### 10.1 Orchestration Comparison

| Aspect | Scraper | AutoBiz | Competitor-Intel | sale-sofia |
|--------|---------|---------|------------------|------------|
| **Task System** | None (sync) | Celery (skeleton only) | Celery + asyncio | Celery |
| **Proxy Scraper** | proxy-scraper-checker | proxy-scraper-checker | proxy-scraper-checker | proxy-scraper-checker |
| **Validation Tool** | pycurl (custom) | mubeng --check | mubeng + httpx async | mubeng --check |
| **Rotator** | None | mubeng server | mubeng server | mubeng server |
| **Sync Mechanism** | sleep(10) | File mtime (intended) | asyncio.gather() | File mtime |
| **Wait for Completion** | Fixed sleep | N/A (not implemented) | Task result | File mtime polling |

### 10.2 Scraper Orchestration

**Pattern:** Sequential, blocking, no task queue

```
main.py
  └── ProxyService.get_proxy()
        ├── _valid_pool_below_threshold() → count lines in valid_proxies.txt
        │   └── If count < 10: trigger refresh
        │
        ├── _trigger_scraper()
        │   └── subprocess.Popen(proxy-scraper-checker)  # DETACHED, no wait
        │
        ├── time.sleep(10)  ← CRITICAL FLAW: Fixed wait, no completion detection
        │
        ├── _populate_valid_proxy_file()
        │   ├── Read outputs: http.txt, https.txt, socks4.txt, socks5.txt
        │   └── For each proxy: ProxyChecker.check_proxy() (SEQUENTIAL, blocking)
        │       └── pycurl request to judge URL
        │       └── Append to valid_proxies.txt
        │
        └── _filter_proxies() → random.choice() → return proxy
```

**Data Flow:**
```
proxy-scraper-checker
  └── WRITES: out/proxies/{http,https,socks4,socks5}.txt (plain text IPs)

ProxyService._populate_valid_proxy_file()
  ├── READS: out/proxies/*.txt
  └── WRITES: valid_proxies.txt (JSON Lines)

ProxyService.get_proxy()
  ├── READS: valid_proxies.txt
  └── REMOVES: used proxy from file (append-only delete BUG)
```

**Timing:** 10s fixed sleep + N×5s per proxy validation (sequential)

**Weakness:** No way to know if scraper finished. Could read incomplete data.

---

### 10.3 AutoBiz Orchestration

**Status:** SKELETON ONLY - main.py and graph.py are EMPTY (0 bytes)

**Intended Pattern (from docs):**
```
Celery beat
  └── scrape_new_proxies_task
        └── subprocess: proxy-scraper-checker
        └── chain → check_scraped_proxies_task

check_scraped_proxies_task
  └── Split into chunks
  └── group(mubeng_check_chunk_task * N)  # Parallel
        └── Each: mubeng --check on 100 proxies
  └── chord callback → process_final_results_task
        └── WRITES: live_proxies.json
```

**Data Flow (intended):**
```
proxy-scraper-checker → proxies.json
  ↓
chunks (in-memory split)
  ↓
mubeng --check (per chunk) → temp files
  ↓
merge results → live_proxies.json
```

**Gap:** No actual implementation exists.

---

### 10.4 Competitor-Intel Orchestration

**Pattern:** Async validation + sync mubeng + weighted transport

```
cli/main.py
  └── get_validated_proxies()
        ├── ProxyManager.__init__()
        ├── ProxyManager.validate_and_save_proxies()
        │   ├── json.load(proxies.json) ← from proxy-scraper-checker
        │   ├── Filter by protocol/anonymity
        │   ├── ProxyValidator(filtered_proxies)
        │   │   └── asyncio.gather(*[check_proxy(p) for p in proxies])  # PARALLEL
        │   │       └── httpx.AsyncClient(proxy=p).get(test_url)
        │   │       └── Measure response_time
        │   └── json.dump(validated_proxies.json)
        │
        └── fetch_and_parse_async(validated_proxies)
              ├── RobustProxyTransport(proxies)
              │   ├── For each proxy: create httpx.AsyncHTTPTransport
              │   ├── Initial score = 1.0 / response_time
              │   └── asyncio.Lock() for thread-safe scoring
              │
              └── asyncio.gather(*[fetch_one(url) for url in urls])
                    └── RobustProxyTransport.handle_async_request()
                          ├── _select_proxy() → weighted random
                          ├── Execute request
                          └── _update_proxy_score(success/fail)
                                ├── success: score *= 1.1
                                ├── fail: score *= 0.5, failures += 1
                                └── if failures >= 3: remove from pool
```

**Data Flow:**
```
proxy-scraper-checker → proxies.json
  ↓
ProxyValidator (async gather) → validated_proxies.json
  ↓
RobustProxyTransport (in-memory pool with scoring)
  ↓
httpx.AsyncClient → HTTP requests with proxy rotation
```

**Timing:**
- Validation: All proxies tested in parallel via asyncio.gather()
- Total validation time ≈ max(individual_timeout) not sum
- Runtime: Weighted selection + exponential backoff (0.5s × attempt)

**Strengths:**
- True parallel validation
- Runtime scoring adapts to proxy quality
- Auto-pruning removes bad proxies

**Weaknesses:**
- Scores not persisted (lost on restart)
- No automatic refresh during crawling

---

### 10.5 sale-sofia Current Orchestration

**Pattern:** Celery chain + file mtime polling

```
main.py:run_auto_mode()
  ├── Orchestrator.__enter__()
  │   └── _register_shutdown_handlers()
  │
  ├── orch.start_redis()
  │   └── subprocess.Popen(redis-server)
  │   └── Poll port 6379 every 0.5s × 10
  │
  ├── orch.start_celery()
  │   └── subprocess.Popen(celery -A celery_app worker --beat)
  │   └── Poll process.poll() every 0.5s × 10
  │
  ├── orch.wait_for_proxies(min_count=5)
  │   ├── If count >= 5: return immediately (FAST PATH)
  │   └── Else: trigger_proxy_refresh() + wait_for_refresh_completion()
  │
  ├── setup_mubeng_rotator(port=8089)
  │   ├── get_and_filter_proxies() → temp file
  │   └── subprocess.Popen(mubeng -a localhost:8089 -f temp_file)
  │
  ├── Pre-flight check (3 attempts × 2 refresh cycles)
  │   └── preflight_check() → requests.get(test_url, proxy=rotator)
  │
  └── scrape_from_start_url()
        └── Browser uses http://localhost:8089
```

**Celery Task Chain:**
```
trigger_proxy_refresh() [orchestrator.py:271]
  └── chain(scrape_new_proxies_task.s(), check_scraped_proxies_task.s()).delay()

scrape_new_proxies_task [tasks.py:18]
  ├── subprocess.run(proxy-scraper-checker, timeout=300)
  └── WRITES: proxies/out/proxies_pretty.json
  └── Returns: "Scraped N proxies"

check_scraped_proxies_task [tasks.py:63]
  ├── READS: proxies/out/proxies_pretty.json
  ├── Split into chunks of 100
  └── (group(check_proxy_chunk_task * N) | process_check_results_task).delay()

check_proxy_chunk_task [tasks.py:93]
  ├── Write temp file: /tmp/tmpXXXXXX.txt
  ├── subprocess.run(mubeng --check, timeout=120)
  ├── enrich_proxy_with_anonymity() for each live proxy
  └── Returns: list of enriched proxies

process_check_results_task [tasks.py:156]
  ├── Flatten all chunk results
  ├── Filter out Transparent
  ├── Sort by timeout
  └── WRITES: proxies/live_proxies.json + live_proxies.txt
```

**Data Flow:**
```
proxy-scraper-checker
  └── WRITES: proxies/out/proxies_pretty.json

check_scraped_proxies_task
  └── READS: proxies/out/proxies_pretty.json
  └── CREATES: chunks (in-memory)

mubeng --check (per chunk)
  ├── READS: /tmp/tmpXXXXXX.txt (temp input)
  └── WRITES: /tmp/tmpYYYYYY.txt (temp output)

process_check_results_task
  └── WRITES: proxies/live_proxies.json
  └── WRITES: proxies/live_proxies.txt

setup_mubeng_rotator
  ├── READS: proxies/live_proxies.json
  └── CREATES: proxies/tmpXXXXXX.txt (temp for mubeng server)

mubeng server
  └── READS: proxies/tmpXXXXXX.txt
  └── LISTENS: localhost:8089
```

**Timing:**
```
T=0:     main() starts
T+2:     Redis + Celery running
T+3:     wait_for_proxies() checks count
T+3-603: If refresh needed: 5-10 min for proxy-scraper-checker
T+N:     Chunks processed (2 at a time, ~2 min each)
T+N+1:   live_proxies.json written (mtime changes)
T+N+2:   wait_for_refresh_completion() detects mtime change
T+N+3:   Mubeng rotator started
T+N+18:  Pre-flight check (up to 15s timeout)
T+N+20:  Scraping begins
```

**Wait Mechanism:**
```python
# orchestrator.py:370
current_mtime = self.get_proxy_file_mtime()
if current_mtime > mtime_before:  # File was updated
    usable_count = self.get_usable_proxy_count()
    if usable_count >= min_count:
        return True
```

Polls every 15 seconds for up to 600 seconds.

---

### 10.6 Orchestration Gaps in sale-sofia

| Gap | Description | Impact | Fix Complexity |
|-----|-------------|--------|----------------|
| **Fire-and-forget auto-trigger** | `scrape_new_proxies_task` calls `check_scraped_proxies_task.delay()` without chain | Task might not run | Low |
| **File-based sync is fragile** | Relies on mtime change, no task completion confirmation | Could miss updates | Medium |
| **Beat schedule conflicts** | Scrape (6h) and check (2h) tasks run independently | Check might read stale data | Low |
| **No task result validation** | Tasks return strings, never verified | Silent failures | Low |
| **No progress reporting** | User sees only "[WAIT]..." for 10 minutes | Poor UX | Medium |
| **All-or-nothing Mubeng restart** | Pre-flight failure triggers full refresh | Slow recovery | Medium |
| **No runtime scoring** | Proxies validated once, never re-scored during crawl | Quality degrades | High |
| **No health monitoring** | No periodic re-validation during long scrapes | Dead proxies accumulate | Medium |

---

### 10.7 Recommended Orchestration Improvements

**Priority 1: Fix synchronization**
```python
# Instead of: check_scraped_proxies_task.delay() (fire-and-forget)
# Use: chain or apply_async with link

# Option A: Always use chain (from Orchestrator)
chain(scrape.s(), check.s()).delay()

# Option B: Use Celery result to confirm completion
result = scrape_new_proxies_task.delay()
result.get(timeout=600)  # Block until complete
check_scraped_proxies_task.delay()
```

**Priority 2: Add runtime scoring (from Competitor-Intel)**
```python
class ScoredProxyPool:
    def select_proxy(self) -> str:
        weights = [p["score"] for p in self.proxies]
        return random.choices(self.proxies, weights=weights)[0]

    def record_result(self, proxy: str, success: bool):
        if success:
            self.proxies[proxy]["score"] *= 1.1
        else:
            self.proxies[proxy]["score"] *= 0.5
            if self.proxies[proxy]["failures"] >= 3:
                self.remove(proxy)
```

**Priority 3: Fix beat schedule**
```python
# Remove separate check task from beat schedule
# Let scrape task auto-trigger check via proper chain
beat_schedule = {
    "refresh-proxies-every-6h": {
        "task": "proxies.tasks.scrape_new_proxies_task",
        "args": [True],  # auto_check=True triggers chain
    },
    # Remove check-proxies-every-2h
}
```

**Priority 4: Add progress events**
```python
# Use Celery's update_state for progress
@celery_app.task(bind=True)
def check_proxy_chunk_task(self, chunk):
    for i, proxy in enumerate(chunk):
        # ... check proxy ...
        self.update_state(state='PROGRESS', meta={'current': i, 'total': len(chunk)})
```

---

## Appendix A: Full Agent Reports

See investigation session for complete agent reports covering all 10 sections per repo.

## Appendix B: Orchestration Agent Reports

See investigation session for detailed orchestration analysis of each repo:
- Scraper: Sequential blocking with fixed sleep
- AutoBiz: Empty skeleton (not implemented)
- Competitor-Intel: Async validation + weighted transport
- sale-sofia: Celery chain + file mtime polling
