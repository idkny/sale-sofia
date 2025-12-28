# Orchestration Research: Scraping & Fetching Module

## Executive Summary

The scraping module is well-architected for orchestration. Scrapers are modular, config-driven, and have clear interfaces. The async_fetcher provides true async HTTP with rate limiting and circuit breaker integration. **Key gap**: No Celery tasks for scraping - only sequential execution in main.py.

---

## 1. How Scrapers Work (URL → Extracted Data)

### Flow Overview
```
Search URL → fetch_search_page() → extract_search_results()
  ↓
Listing URLs (queue/checkpoint)
  ↓
fetch_listing_page() → extract_listing() → ListingData object
  ↓
Change detection → save_to_db() → deduplication & tracking
```

### Key Files
- `websites/base_scraper.py` - Base abstraction with ListingData dataclass
- `websites/imot_bg/imot_scraper.py` - imot.bg implementation (600+ lines)
- `websites/bazar_bg/bazar_scraper.py` - bazar.bg implementation (640+ lines)
- `websites/__init__.py` - `get_scraper(site)` factory

### Core Methods
| Method | Purpose |
|--------|---------|
| `extract_listing(html, url)` | ListingData with 30+ fields |
| `extract_search_results(html)` | List[str] of listing URLs |
| `is_last_page(html, page_num)` | Pagination detection |
| `get_next_page_url(current_url, page_num)` | URL building |
| `get_search_url(page)` | Start URL for page N |

---

## 2. Async Fetcher Integration

**Location**: `scraping/async_fetcher.py`

### Key Functions
```python
async fetch_page(url, proxy=None, timeout=60) → str
  - Uses httpx.AsyncClient
  - Checks circuit breaker before request
  - Acquires rate limit token via get_rate_limiter()
  - Detects soft blocks (403, CAPTCHA patterns)

async fetch_pages_concurrent(urls, proxy=None, max_concurrent=5) → List[(url, result)]
  - Controls parallelism with asyncio.Semaphore
  - Returns (url, html|Exception) tuples
```

### Integration Points
- Uses `resilience/circuit_breaker.py` - per-domain blocking
- Uses `resilience/rate_limiter.py` - token bucket rate limiting
- Uses `resilience/response_validator.py` - soft block detection
- Default proxy: `MUBENG_PROXY` from settings

---

## 3. Scraper Configuration

### Config Files
- `config/scraping_defaults.yaml` - Global defaults
- `config/sites/imot_bg.yaml` - imot.bg overrides
- `config/sites/bazar_bg.yaml` - bazar.bg overrides

### Configuration Structure
```yaml
concurrency:
  max_global: 16
  max_per_domain: 2
timing:
  delay_seconds: 2.0
  randomize_delay: true
timeouts:
  request_seconds: 60
  page_load_seconds: 30
retry:
  max_attempts: 3
  backoff_base: 1.0
  backoff_max: 300.0
fetcher:
  search_pages: http|browser|stealth
  listing_pages: http|browser|stealth
```

### Site-Specific Overrides
| Site | Delay | Per-Domain | Search Method |
|------|-------|------------|---------------|
| imot.bg | 1.5s | 3 | HTTP |
| bazar.bg | 3.0s | 1 | Stealth |

---

## 4. Resources & Dependencies

### Proxies
- Mubeng rotator at `MUBENG_PROXY` (localhost:8089)
- Minimum: `MIN_PROXIES_FOR_SCRAPING` (default: 10)
- ScoredProxyPool for fallback rotation

### Browser (Anti-Bot)
- Camoufox (modified Firefox) via Scrapling library
- `ScraplingMixin.fetch_stealth()` for search pages
- Requires: `data/certs/mubeng-ca.pem`

### Parsing
- Scrapling library (not BeautifulSoup) - faster
- Adaptive selector tracking in `data/scrapling_selectors/`
- Auto-encoding detection (windows-1251, UTF-8)

---

## 5. Error Handling & Retries

### Exception Hierarchy
```
ScraperException
├── NetworkException (connection, timeout)
├── RateLimitException (429 response)
├── BlockedException (403, CAPTCHA)
├── ParseException (HTML parsing failed)
├── ProxyException (proxy error)
└── CircuitOpenException (domain blocked)
```

### Retry Strategy
- Exponential backoff: `base * (2^attempt)` capped at max
- Jitter: random 0-50% of delay added
- Respects `Retry-After` header for rate limits
- Default: 5 attempts, 2s base, 60s max

---

## 6. What Orchestrator Needs

### Scraper Access
```python
from websites import get_scraper, AVAILABLE_SITES
scraper = get_scraper("imot.bg")
```

### Configuration Access
```python
from config.scraping_config import load_scraping_config
config = load_scraping_config("imot.bg")
```

### Key Methods for Orchestration
| Method | Use |
|--------|-----|
| `scraper.get_search_url(page)` | Build paginated URLs |
| `scraper.extract_search_results(html)` | Parse search pages |
| `scraper.is_last_page(html, page)` | Detect pagination end |
| `scraper.extract_listing(html, url)` | Parse listings |

---

## 7. Gaps for Parallel Site Scraping

### Current Limitations
1. **Sequential Site Loop** - main.py iterates sites one at a time
2. **Single Proxy Context** - one proxy pool for all sites
3. **No Task Queue** - searches aren't enqueued as distributed tasks
4. **Limited Concurrency Control** - max_global=16 doesn't map to multi-site

### What's Missing
1. **Task Distribution** - Need `scrape_search_page_task`, `scrape_listing_task`
2. **Site-Aware Rate Limiting** - per-site task prioritization
3. **Concurrent Search Pagination** - parallel page fetches
4. **Multi-Site Listing Queue** - Redis list or Celery chains
5. **Progress Tracking** - Redis keys per-site (like proxy tasks)
6. **Resource Pooling** - proxy/browser pooling across sites

---

## Key Stats & Configs

| Parameter | Value | Source |
|-----------|-------|--------|
| Max Global Concurrency | 16 | scraping_defaults.yaml |
| Max Per Domain | 2 | scraping_defaults.yaml |
| Base Delay | 2.0s | scraping_defaults.yaml |
| Max Retry Attempts | 3 | scraping_defaults.yaml |
| Circuit Breaker Fail Max | 5 | circuit_breaker.py |
| Circuit Breaker Recovery | 60s | circuit_breaker.py |
| Async Fetcher Max Concurrent | 5 | async_fetcher.py |

---

## Recommended Phase 4.3 Structure

```
scraping/
├── async_fetcher.py (existing)
├── __init__.py
├── tasks.py (NEW)
│   ├── scrape_search_pages_task()
│   ├── scrape_listing_task()
│   ├── chain builders
│   └── progress tracking
└── orchestrator_integration.py (NEW)
    └── ScrappingDispatcher class
```

**What Phase 4.3 Must Do**:
1. Create Celery tasks for scraping (mirroring proxy task patterns)
2. Implement task chains: search → list URLs → scrape listings
3. Add Redis progress tracking per site
4. Distribute tasks across workers
5. Coordinate circuit breaker + rate limiting globally
