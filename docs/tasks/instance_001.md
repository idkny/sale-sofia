# Instance 1 Session

**You are Instance 1.** Work independently.

---

## Workflow: Research → Specs → Code

**Single source of truth at each stage:**

```
docs/research/  →  docs/specs/  →  TASKS.md  →  code
(discovery)        (blueprint)     (tracking)    (truth)
      ↓                 ↓                           ↓
archive/research/  archive/specs/          (code supersedes)
```

**Rules:**
1. Research done → create spec + task → archive research
2. Spec done → implement code → archive spec
3. Code is source of truth (specs become historical)
4. New features = new specs (don't update archived)

---

## How to Work

1. Read [TASKS.md](TASKS.md) coordination table
2. Claim task with `[Instance 1]` in that file
3. If task needs research → create file in `docs/research/`
4. If task needs spec → create file in `docs/specs/`, link in task
5. Implement code following spec
6. Mark complete with `[x]}`, archive spec
7. On `/ess` - run checklist, update session history

---

## Task Linking Examples

```markdown
# Research task
- [ ] [Instance 1] Research proxy rotation
  (research: [proxy_research.md](../research/proxy_research.md))

# Spec task
- [ ] [Instance 1] Write proxy rotation spec
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# Implementation task
- [ ] [Instance 1] Implement proxy rotation
  (spec: [101_PROXY_ROTATION.md](../specs/101_PROXY_ROTATION.md))

# After complete (spec archived, link removed)
- [x] Implement proxy rotation
```

---

## CRITICAL RULES

1. **NEVER WRITE "NEXT STEPS" IN THIS FILE**
2. **TASKS.md IS THE SINGLE SOURCE OF TRUTH FOR TASKS**
3. **THIS FILE IS FOR SESSION HISTORY ONLY**
4. **KEEP ONLY LAST 3 SESSIONS**
5. **CODE IS SOURCE OF TRUTH, NOT SPECS**

---

## Instance Rules

1. **One task at a time** - Finish before claiming another
2. **Check coordination table FIRST** - Re-read TASKS.md before claiming
3. **Claim in TASKS.md** - Add `[Instance 1]` to task BEFORE starting
4. **Link specs** - Every implementation task should link to a spec
5. **Archive when done** - Move completed research/specs to archive/
6. **Don't touch instance_002.md** - Other instance file is off-limits

---

## Session History

### 2025-12-27 (Session 28 - Scraper Resilience Research)

| Task | Status |
|------|--------|
| Analyze current scraper error handling | ✅ Complete |
| Research best practices (web search) | ✅ Complete |
| Explore AutoBiz codebase for patterns | ✅ Complete |
| Create research document | ✅ Complete |
| Create spec document (112) | ✅ Complete |
| Add tasks to TASKS.md | ✅ Complete |

**Summary**: Comprehensive research on scraper resilience. Analyzed current codebase (has basic retry but missing backoff, circuit breaker, rate limiting). Found production-grade patterns in AutoBiz codebase that can be directly ported. Created spec 112 with 18 implementation tasks across 4 phases.

---

#### Current State Analysis

**What EXISTS in sale-sofia:**
| Feature | Location | Status |
|---------|----------|--------|
| Basic retry (3 attempts) | `main.py:119-149` | No backoff, immediate retry |
| Proxy scoring | `proxies/proxy_validator.py` | Works, tracks success/failure |
| Preflight checks (3-level) | `main.py:398-486` | Good recovery pattern |
| CSS selector fallback | `websites/scrapling_base.py` | Basic exception catch |

**What's MISSING (Critical Gaps):**
- NO exponential backoff - retries happen immediately
- NO jitter - creates thundering herd
- NO circuit breaker - keeps hammering blocked sites
- NO domain rate limiting - no throttle per target
- NO error classification - all errors treated same
- NO graceful degradation - component failure = crash
- NO session recovery - no checkpoint/resume
- NO 429/Retry-After handling

---

#### AutoBiz Patterns Found (READY TO PORT)

Explored `/home/wow/Documents/ZohoCentral/autobiz` and found 5 production-grade modules:

**1. DomainCircuitBreaker** (`core/_domain_circuit_breaker.py`, 360 lines)
```
CLOSED → 10 failures → OPEN → 5 min cooldown → HALF_OPEN → test → CLOSED
```
- Fail-open design (errors allow requests, never blocks on bugs)
- Block type tracking: cloudflare, captcha, rate_limit, ip_ban
- Metrics: blocked/allowed counts, open circuits list
- Config: `failure_threshold=10`, `recovery_timeout=300`, `half_open_max_calls=2`

**2. Error System** (`core/_scraper_errors.py`, 556 lines)

ErrorType enum (20+ categories):
- Network: `NETWORK_TIMEOUT`, `NETWORK_CONNECTION`, `NETWORK_DNS`
- HTTP: `HTTP_CLIENT_ERROR`, `HTTP_SERVER_ERROR`, `HTTP_RATE_LIMIT`, `HTTP_BLOCKED`
- Parsing: `PARSE_JSON`, `PARSE_HTML`, `PARSE_SELECTOR`
- Service: `SERVICE_OLLAMA`, `SERVICE_REDIS`, `SERVICE_PROXY`, `SERVICE_BROWSER`
- Database: `DATABASE_LOCKED`, `DATABASE_CORRUPT`

RecoveryAction enum:
- `RETRY_IMMEDIATE`, `RETRY_WITH_BACKOFF`, `RETRY_WITH_PROXY`
- `ESCALATE_STRATEGY`, `SKIP`, `CIRCUIT_BREAK`, `MANUAL_REVIEW`

ERROR_RECOVERY_MAP (maps error → action + max_retries):
```python
ErrorType.NETWORK_TIMEOUT: (RETRY_WITH_BACKOFF, recoverable=True, max_retries=3)
ErrorType.HTTP_RATE_LIMIT: (RETRY_WITH_BACKOFF, recoverable=True, max_retries=5)
ErrorType.HTTP_BLOCKED: (ESCALATE_STRATEGY, recoverable=True, max_retries=3)
ErrorType.PARSE_JSON: (MANUAL_REVIEW, recoverable=False, max_retries=0)
```

ScraperError dataclass - full context for debugging:
- error_id, timestamp, url, domain, error_type
- http_status, message, stack_trace
- retry_count, max_retries, next_retry_delay (backoff calculated)
- recovery_action, is_recoverable, proxy_ip, strategy

ScraperErrorLogger - JSONL logging for analysis

**3. Rate Limiter** (`tools/scraping/_rate_limiter.py`, 99 lines)
- Per-domain delay tracking
- Randomized delays (min to max)
- **Automatic backoff on blocks**: `delay *= 1 + (consecutive_blocks * 0.5)`

**4. Bulkhead** (`core/_domain_bulkhead.py`, 426 lines)
- Concurrency limiter using semaphores
- Prevents slow domains from monopolizing workers
- Configurable limits per domain
- Fail-open design
- Context manager: `with bulkhead.acquire("imot.bg"):`

**5. Timeout Budget** (`core/_timeout_budget.py`, 221 lines)
- Hierarchical timeout management
- Child operations can't exceed parent's remaining time
- `budget.child_budget(max_seconds=120)` returns bounded child
- Constants: TASK=270s, BROWSER=120s, HTTP=30s

---

#### Documents Created

| Document | Path |
|----------|------|
| Research | `docs/research/SCRAPER_RESILIENCE_RESEARCH.md` |
| Spec | `docs/specs/112_SCRAPER_RESILIENCE.md` |
| Tasks | `docs/tasks/TASKS.md` (18 tasks added) |

---

#### Implementation Plan (from Spec 112)

**Proposed File Structure:**
```
resilience/                # NEW MODULE
├── __init__.py
├── circuit_breaker.py    # Port from AutoBiz _domain_circuit_breaker.py
├── errors.py             # Port from AutoBiz _scraper_errors.py
├── rate_limiter.py       # Port from AutoBiz _rate_limiter.py
├── bulkhead.py           # Port from AutoBiz _domain_bulkhead.py
├── timeout_budget.py     # Port from AutoBiz _timeout_budget.py
├── retry.py              # NEW: retry decorator with backoff + jitter
├── checkpoint.py         # NEW: session recovery
└── response_validator.py # NEW: soft block detection
```

**Phase 1: Foundation (P1 - Critical)**
- [ ] Create `resilience/` module structure
- [ ] Implement `resilience/exceptions.py` (exception hierarchy)
- [ ] Implement `resilience/error_classifier.py`
- [ ] Implement `resilience/retry.py` (sync + async with backoff + jitter)
- [ ] Add resilience settings to `config/settings.py`
- [ ] Integrate retry decorator into `main.py`
- [ ] Write unit tests for Phase 1

**Phase 2: Domain Protection (P2)**
- [ ] Implement `resilience/circuit_breaker.py`
- [ ] Implement `resilience/rate_limiter.py` (token bucket)
- [ ] Integrate circuit breaker into scraper
- [ ] Integrate rate limiter into scraper
- [ ] Write unit tests for Phase 2

**Phase 3: Session Recovery (P2)**
- [ ] Implement `resilience/checkpoint.py`
- [ ] Add checkpoint save/restore to main.py
- [ ] Add SIGTERM/SIGINT graceful shutdown handlers
- [ ] Write unit tests for Phase 3

**Phase 4: Detection (P3)**
- [ ] Implement `resilience/response_validator.py` (CAPTCHA/soft block detection)
- [ ] Add 429/Retry-After header handling
- [ ] Write unit tests for Phase 4

---

#### Config Settings to Add (`config/settings.py`)

```python
# Retry settings
RETRY_MAX_ATTEMPTS = 5
RETRY_BASE_DELAY = 2.0       # seconds
RETRY_MAX_DELAY = 60.0       # seconds cap
RETRY_JITTER_FACTOR = 0.5    # 50% random jitter

# Circuit breaker settings
CIRCUIT_BREAKER_FAIL_MAX = 5
CIRCUIT_BREAKER_RESET_TIMEOUT = 60  # seconds

# Rate limiting (requests per minute per domain)
DOMAIN_RATE_LIMITS = {
    "imot.bg": 10,
    "bazar.bg": 10,
    "default": 10,
}

# Checkpoint settings
CHECKPOINT_BATCH_SIZE = 10  # Save every N URLs
CHECKPOINT_DIR = "data/checkpoints"
```

---

#### Key Code References

**AutoBiz files to port:**
- `/home/wow/Documents/ZohoCentral/autobiz/core/_domain_circuit_breaker.py`
- `/home/wow/Documents/ZohoCentral/autobiz/core/_scraper_errors.py`
- `/home/wow/Documents/ZohoCentral/autobiz/tools/scraping/_rate_limiter.py`
- `/home/wow/Documents/ZohoCentral/autobiz/core/_domain_bulkhead.py`
- `/home/wow/Documents/ZohoCentral/autobiz/core/_timeout_budget.py`

**Archived patterns (already in sale-sofia):**
- `archive/extraction/error_handling/error_handling_Scraper.md` - retry_async decorator, CooldownManager

**Integration points in sale-sofia:**
- `main.py:119-149` - Replace simple retry with decorated functions
- `main.py:189-278` - `_scrape_listings()` needs circuit breaker + rate limiter
- `websites/base_scraper.py` - Add domain extraction for rate limiting
- `orchestrator.py` - Add checkpoint save/restore

---

#### Best Practices Sources

- [ScrapFly - Automatic Failover Strategies](https://scrapfly.io/blog/posts/automatic-failover-strategies-for-reliable-data-extraction)
- [ScrapingAnt - Exception Handling](https://scrapingant.com/blog/python-exception-handling)
- [ScrapeUnblocker - 10 Best Practices 2025](https://www.scrapeunblocker.com/post/10-web-scraping-best-practices-for-developers-in-2025)
- [FireCrawl - Stop Getting Blocked](https://www.firecrawl.dev/blog/web-scraping-mistakes-and-fixes)

---

#### Recommendation for Implementation

**Option A: Direct Port** (Faster, ~2-3 hours)
- Copy AutoBiz files with minor import modifications
- Well-tested, production-ready code

**Option B: Clean Rewrite** (Cleaner, ~5-7 hours)
- Use AutoBiz as reference
- Follow sale-sofia conventions

**Recommended**: Option A for complex patterns (circuit breaker, error system), Option B for simpler ones (retry decorator).

---

### 2025-12-27 (Session 26 - TASKS.md Cleanup + Centralized Proxy Settings)

| Task | Status |
|------|--------|
| Clean up TASKS.md (remove duplicates, stale tasks) | ✅ Complete |
| Centralize proxy settings in config/settings.py | ✅ Complete |
| Fix inconsistent MIN_PROXIES values | ✅ Complete |

**Summary**: Cleaned up TASKS.md by removing duplicate JIT Proxy Validation (already in Solution F), homes.bg task, and P3 research tasks. Centralized proxy settings (`MUBENG_PROXY`, `MIN_PROXIES_TO_START`, `MIN_PROXIES_FOR_SCRAPING`, `MAX_PROXY_RETRIES`) in config/settings.py.

**Key Changes:**
- `config/settings.py` - Added proxy constants
- `main.py`, `websites/scrapling_base.py`, `proxies/proxies_main.py` - Import from config.settings

---

### 2025-12-26 (Session 13 - Service Lifecycle + TimeLimitExceeded Fix)

| Task | Status |
|------|--------|
| Implement automatic service lifecycle management | ✅ Complete |
| Fix TimeLimitExceeded (chunk tasks killed after 8min) | ✅ Complete |
| Run live test to verify | ✅ Complete (both chords succeeded) |

**Summary**: Implemented automatic cleanup of stale processes on startup, fixed TimeLimitExceeded by adjusting timeouts (8min→15min).

**Key Changes:**
- `orchestrator.py` - Added `cleanup_stale_processes()`, health checks
- `proxies/tasks.py` - Task limits: 13min/15min

---

*(Sessions 11, 12 archived to `archive/sessions/`)*

---

## Quick Links

- [TASKS.md](TASKS.md) - Task tracker (single source of truth)
- [instance_002.md](instance_002.md) - Other instance (don't edit)
- [../research/](../research/) - Active research files
- [../specs/](../specs/) - Active spec files
