# Scraper Resilience Research

**Date**: 2025-12-27
**Purpose**: Comprehensive analysis of error handling and resilience patterns for web scrapers

---

## Executive Summary

Our scraper currently has **basic** error handling (retry loops, proxy validation) but lacks **production-grade resilience**. This research identifies gaps and proposes a multi-layer resilience architecture.

### Current State Assessment

| Feature | Status | Location |
|---------|--------|----------|
| Basic retry (3 attempts) | Exists | `main.py:119-149` |
| Proxy scoring | Exists | `proxies/proxy_validator.py` |
| Preflight checks (3-level) | Exists | `main.py:398-486` |
| CSS selector fallback | Exists | `websites/scrapling_base.py` |
| **Exponential backoff** | Missing | - |
| **Circuit breaker** | Missing | - |
| **Domain rate limiting** | Missing | - |
| **Error classification** | Missing | - |
| **Session checkpoint/resume** | Missing | - |
| **Soft block detection** | Missing | - |

---

## Error Classification (From Best Practices)

### HTTP Errors

| Code | Type | Retry? | Strategy |
|------|------|--------|----------|
| 403 | Blocked/Banned | No | Circuit breaker + rotate proxy + domain cooldown |
| 404 | Page gone | No | Skip permanently |
| 429 | Rate limited | Yes | Exponential backoff + honor Retry-After header |
| 500-503 | Server error | Yes | Retry with backoff |
| 520-530 | Cloudflare | Yes | Longer delay + different proxy |

### Network Errors

| Error | Retry? | Strategy |
|-------|--------|----------|
| ConnectionError | Yes | Retry with backoff |
| Timeout | Yes | Retry with longer timeout |
| SSLError | Skip proxy | Try different proxy |
| ProxyError | Skip proxy | Rotate proxy, mark as failed |

### Parsing Errors

| Error | Retry? | Strategy |
|-------|--------|----------|
| AttributeError (missing element) | No | Return partial data |
| ValueError (bad format) | No | Log, return None |

### Infrastructure Failures

| Failure | Strategy |
|---------|----------|
| Redis down | Retry connection + fallback to file |
| Celery down | Detect + auto-restart |
| Internet down | Pause + exponential retry |
| Power failure | Checkpoint system for resume |

---

## Best Practices (From Web Research)

### 1. Exponential Backoff with Jitter

**Formula**: `delay = min(base_delay * 2^attempt + random.uniform(0, delay/2), max_delay)`

**Example** (base=2s, max=60s):
- Attempt 1: 2s + jitter
- Attempt 2: 4s + jitter
- Attempt 3: 8s + jitter
- Attempt 4: 16s + jitter
- Attempt 5: 32s + jitter

**Why jitter?** Prevents "thundering herd" when multiple scrapers retry simultaneously.

**Sources**:
- [ScrapFly - Automatic Failover Strategies](https://scrapfly.io/blog/posts/automatic-failover-strategies-for-reliable-data-extraction)
- [ScrapingAnt - Exception Handling](https://scrapingant.com/blog/python-exception-handling)

### 2. Circuit Breaker Pattern

**Concept**: Stop sending requests to a struggling target after consecutive failures.

**States**:
- **Closed** (normal): Requests flow through
- **Open** (triggered): Requests blocked for cooldown period
- **Half-Open** (testing): Allow one test request

**Typical config**: 5 failures → 60s cooldown

**Library**: `pybreaker`

```python
import pybreaker

breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
def fetch_page(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text
```

### 3. Domain-Level Rate Limiting

**Token Bucket Algorithm**:
- Each domain gets N tokens per minute
- Request consumes 1 token
- If no tokens, wait until refill

**Per-site config**:
```python
DOMAIN_RATE_LIMITS = {
    "imot.bg": 10,      # 10 requests/minute
    "bazar.bg": 10,
    "homes.bg": 5,      # More aggressive protection
}
```

### 4. Retry-After Header Handling

When server returns 429, it often includes `Retry-After` header.

```python
if response.status_code == 429:
    retry_after = response.headers.get('Retry-After', 60)
    time.sleep(int(retry_after))
```

### 5. Proxy Rotation on Failure

**From our archived code** (`archive/extraction/error_handling/error_handling_Scraper.md`):

```python
proxy_stats = defaultdict(lambda: {"fails": 0, "ok": 0})

def fetch_with_rotation(url):
    for proxy in proxy_pool:
        if proxy_stats[proxy]["fails"] >= 3:
            continue  # Skip dead proxies
        try:
            resp = requests.get(url, proxies={"http": proxy})
            proxy_stats[proxy]["ok"] += 1
            return resp
        except:
            proxy_stats[proxy]["fails"] += 1
```

### 6. Session Checkpoint/Resume

Save progress after each batch to handle crashes:

```python
class CheckpointManager:
    def __init__(self, checkpoint_file):
        self.file = checkpoint_file

    def save(self, scraped_urls, pending_urls):
        with open(self.file, 'w') as f:
            json.dump({
                "scraped": list(scraped_urls),
                "pending": list(pending_urls),
                "timestamp": time.time()
            }, f)

    def load(self):
        if self.file.exists():
            with open(self.file) as f:
                return json.load(f)
        return None
```

---

## Existing Code Assets (From Archive)

### 1. Async Retry Decorator

**Location**: `archive/extraction/error_handling/error_handling_Scraper.md`

```python
def retry_async(max_attempts=3, base_delay=1.0, max_delay=10.0, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1), max_delay)
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
```

### 2. Cooldown Manager

**Location**: `archive/extraction/error_handling/error_handling_Scraper.md`

```python
class CooldownManager:
    def __init__(self, site_name):
        self.cooldowns = {}

    def is_in_cooldown(self, strategy: str) -> bool:
        return time.time() < self.cooldowns.get(strategy, 0)

    def bump(self, strategy: str, cooldown_time: int = 300):
        self.cooldowns[strategy] = time.time() + cooldown_time

    def reset(self, strategy: str):
        self.cooldowns.pop(strategy, None)
```

---

## Proposed Architecture

### Layer 1: Request Level
- Retry decorator with exponential backoff + jitter
- Error classifier (categorize exceptions)
- Response validator (detect CAPTCHAs, empty pages)

### Layer 2: Proxy Level (Partially Exists)
- ScoredProxyPool (EXISTS)
- Auto-rotation on failure (EXISTS)
- **NEW**: Immediate proxy circuit breaker

### Layer 3: Domain Level (NEW)
- DomainCircuitBreaker (stop hammering blocked sites)
- DomainRateLimiter (token bucket per domain)
- DomainCooldownManager (cooldown per site)

### Layer 4: Session Level (NEW)
- CheckpointManager (save/resume progress)
- Graceful shutdown (SIGTERM/SIGINT handling)

### Layer 5: Infrastructure Level (Partially Exists)
- Health checks (EXISTS for Redis/Celery)
- Auto-restart (EXISTS in preflight)
- **NEW**: Watchdog for hung processes

---

## Proposed File Structure

```
resilience/                # NEW MODULE
├── __init__.py
├── retry.py              # retry_with_backoff decorator (sync + async)
├── circuit_breaker.py    # DomainCircuitBreaker class
├── rate_limiter.py       # DomainRateLimiter (token bucket)
├── cooldown.py           # CooldownManager (ported from archive)
├── exceptions.py         # Custom exception hierarchy
├── error_classifier.py   # classify_error(exception) → ErrorType
├── checkpoint.py         # CheckpointManager for session recovery
└── response_validator.py # detect_soft_block(html) → bool
```

---

## Implementation Priority

### P1 - Critical (High Impact)
1. Retry with exponential backoff + jitter
2. Error classification
3. Domain circuit breaker

### P2 - Important (Medium-High Impact)
4. Domain rate limiter
5. Checkpoint/resume system
6. 429/Retry-After handling

### P3 - Nice to Have
7. Soft block detector (CAPTCHA detection)
8. Watchdog for hung processes

---

## Sources

- [ScrapFly - Automatic Failover Strategies](https://scrapfly.io/blog/posts/automatic-failover-strategies-for-reliable-data-extraction)
- [ScrapingAnt - Exception Handling Strategies](https://scrapingant.com/blog/python-exception-handling)
- [ScrapeUnblocker - 10 Web Scraping Best Practices 2025](https://www.scrapeunblocker.com/post/10-web-scraping-best-practices-for-developers-in-2025)
- [FireCrawl - Stop Getting Blocked](https://www.firecrawl.dev/blog/web-scraping-mistakes-and-fixes)
- [BrightData - Distributed Web Crawling Guide](https://brightdata.com/blog/web-data/distributed-web-crawling)
- Archived code: `archive/extraction/error_handling/error_handling_Scraper.md`

---

## AutoBiz Codebase Analysis

Explored `/home/wow/Documents/ZohoCentral/autobiz` and found **production-grade resilience patterns** we can directly port:

### 1. DomainCircuitBreaker (`core/_domain_circuit_breaker.py`)

Full implementation with:
- **3 states**: CLOSED → OPEN → HALF_OPEN
- **Fail-open design**: Errors in circuit breaker allow requests (never blocks on bugs)
- **Configurable thresholds**: `failure_threshold=10`, `recovery_timeout=300s`
- **Block type tracking**: cloudflare, captcha, rate_limit, ip_ban
- **Metrics**: blocked/allowed counts, open circuits list

```python
class DomainCircuitBreaker:
    def __init__(self, failure_threshold=10, recovery_timeout=300, half_open_max_calls=2):
        ...

    def can_request(self, domain: str) -> bool:
        """FAIL-OPEN: Returns True on any error"""

    def record_success(self, domain: str): ...
    def record_failure(self, domain: str, block_type: str): ...
    def get_state(self, domain: str) -> CircuitState: ...
```

### 2. Comprehensive Error System (`core/_scraper_errors.py`)

**ErrorType enum** with 20+ categories:
- Network: `NETWORK_TIMEOUT`, `NETWORK_CONNECTION`, `NETWORK_DNS`
- HTTP: `HTTP_CLIENT_ERROR`, `HTTP_SERVER_ERROR`, `HTTP_RATE_LIMIT`, `HTTP_BLOCKED`
- Parsing: `PARSE_JSON`, `PARSE_HTML`, `PARSE_SELECTOR`
- Service: `SERVICE_OLLAMA`, `SERVICE_REDIS`, `SERVICE_PROXY`, `SERVICE_BROWSER`
- Database: `DATABASE_LOCKED`, `DATABASE_CORRUPT`

**RecoveryAction enum**:
- `RETRY_IMMEDIATE`, `RETRY_WITH_BACKOFF`, `RETRY_WITH_PROXY`
- `ESCALATE_STRATEGY`, `SKIP`, `CIRCUIT_BREAK`, `MANUAL_REVIEW`, `RESTART_SERVICE`

**ERROR_RECOVERY_MAP** - Maps each error type to (action, is_recoverable, max_retries):
```python
ERROR_RECOVERY_MAP = {
    ErrorType.NETWORK_TIMEOUT: (RecoveryAction.RETRY_WITH_BACKOFF, True, 3),
    ErrorType.HTTP_RATE_LIMIT: (RecoveryAction.RETRY_WITH_BACKOFF, True, 5),
    ErrorType.HTTP_BLOCKED: (RecoveryAction.ESCALATE_STRATEGY, True, 3),
    ErrorType.PARSE_JSON: (RecoveryAction.MANUAL_REVIEW, False, 0),
    ...
}
```

**ScraperError dataclass** - Full context for debugging:
```python
@dataclass
class ScraperError:
    error_id: str
    timestamp: datetime
    url: str
    domain: str
    error_type: ErrorType
    http_status: int | None
    message: str
    stack_trace: str
    retry_count: int
    max_retries: int
    next_retry_delay: float  # Exponential backoff calculated
    recovery_action: RecoveryAction
    is_recoverable: bool
    proxy_ip: str | None
    strategy: str | None
```

**ScraperErrorLogger** - JSONL logging for analysis.

### 3. Domain Rate Limiter (`tools/scraping/_rate_limiter.py`)

Simple but effective:
- Per-domain delay tracking
- Randomized delays (min to max)
- **Automatic backoff on blocks**: `delay *= 1 + (consecutive_blocks * 0.5)`

```python
def get_delay_for_domain(domain: str) -> float:
    config = scraper_db.get_domain_config(domain)
    delay = uniform(min_delay, max_delay)
    if consecutive_blocks > 0:
        delay *= 1 + (consecutive_blocks * 0.5)  # Backoff!
    return delay

def wait_if_needed(domain: str) -> float:
    """Block if rate limit requires waiting."""
```

### 4. Domain Bulkhead (`core/_domain_bulkhead.py`)

**Concurrency limiter** - prevents slow domains from monopolizing workers:
- Uses semaphores per domain
- Configurable limits per domain
- **Fail-open design**: Errors allow requests
- Timeout on acquire (default 60s)
- Metrics: in_use, timeouts, wait times

```python
class DomainBulkhead:
    def __init__(self, default_limit=3):
        ...

    @contextmanager
    def acquire(self, domain: str, timeout: float = 60.0):
        """Acquire slot, block if limit reached."""
        ...

    def set_limit(self, domain: str, limit: int):
        """Set custom limit per domain."""
```

### 5. Timeout Budget (`core/_timeout_budget.py`)

**Hierarchical timeout management** - child operations can't exceed parent's remaining time:

```python
@dataclass
class TimeoutBudget:
    total_seconds: float
    started_at: float

    @property
    def remaining(self) -> float: ...
    @property
    def remaining_ms(self) -> int: ...  # For browser APIs
    @property
    def has_time(self) -> bool: ...

    def child_budget(self, max_seconds: float) -> TimeoutBudget:
        """Create child bounded by parent's remaining time."""

    def check_time(self, operation: str):
        """Raise TimeoutExhausted if insufficient."""
```

**Hierarchy constants**:
```python
TASK_TIMEOUT = 270    # Celery soft limit
BROWSER_TIMEOUT = 120 # Browser ops
HTTP_TIMEOUT = 30     # Direct HTTP
CAPTCHA_TIMEOUT = 180 # CAPTCHA solving
```

---

## Key Patterns to Adopt from AutoBiz

| Pattern | AutoBiz File | Priority | Notes |
|---------|--------------|----------|-------|
| Circuit Breaker | `_domain_circuit_breaker.py` | P1 | Production-ready, fail-open |
| Error Classification | `_scraper_errors.py` | P1 | 20+ error types, recovery map |
| Rate Limiter | `_rate_limiter.py` | P2 | Simple, backoff on blocks |
| Bulkhead | `_domain_bulkhead.py` | P2 | Concurrency limiting |
| Timeout Budget | `_timeout_budget.py` | P3 | Hierarchical timeouts |

### Recommended Approach

**Option A: Direct Port** (Faster)
- Copy AutoBiz files with minor modifications
- Adapt imports to sale-sofia structure
- Estimated: 2-3 hours

**Option B: Clean Rewrite** (Cleaner)
- Use AutoBiz as reference
- Write fresh code following our conventions
- Estimated: 5-7 hours

**Recommendation**: Option A for circuit breaker and error system (complex, well-tested), Option B for simpler patterns.

---

## Updated File Structure

Based on AutoBiz patterns:

```
resilience/
├── __init__.py
├── circuit_breaker.py    # Port from AutoBiz _domain_circuit_breaker.py
├── errors.py             # Port from AutoBiz _scraper_errors.py
├── rate_limiter.py       # Port from AutoBiz _rate_limiter.py
├── bulkhead.py           # Port from AutoBiz _domain_bulkhead.py
├── timeout_budget.py     # Port from AutoBiz _timeout_budget.py
├── retry.py              # New: retry decorator with backoff
├── checkpoint.py         # New: session recovery
└── response_validator.py # New: soft block detection
```

---

## Next Steps

1. ~~Create spec document (112_SCRAPER_RESILIENCE.md)~~ DONE
2. ~~Add tasks to TASKS.md~~ DONE
3. Port AutoBiz patterns (circuit breaker, errors, rate limiter)
4. Implement remaining patterns (retry, checkpoint)
5. Integrate into scraper

---

*Research conducted: 2025-12-27*
*Updated: 2025-12-27 (Added AutoBiz analysis)*
