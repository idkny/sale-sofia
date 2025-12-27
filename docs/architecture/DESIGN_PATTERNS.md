# Design Patterns

> Patterns used in the sale-sofia codebase. Read when you need to understand or extend a specific pattern.

---

## 1. Strategy Pattern (browsers/)

Different browser implementations share a common interface.

```python
# Base strategy (browsers/strategies/base.py)
class BaseBrowserStrategy(ABC):
    @abstractmethod
    async def launch(self) -> Tuple[Browser, BrowserContext]: ...

    @abstractmethod
    async def close(self) -> None: ...

# Concrete strategies
class ChromiumStrategy(BaseBrowserStrategy): ...
class FirefoxStrategy(BaseBrowserStrategy): ...
class ChromiumStealthStrategy(BaseBrowserStrategy): ...
```

**Usage**: `create_instance("chromiumstealth")` returns the right strategy.

---

## 2. Template Method Pattern (websites/)

Base scraper defines the skeleton; subclasses implement specifics.

```python
# Base class (websites/base_scraper.py)
class BaseSiteScraper(ABC):
    @abstractmethod
    async def extract_listing(self, html, url) -> ListingData: ...

    @abstractmethod
    async def extract_search_results(self, html) -> List[str]: ...

    # Helper methods (non-abstract)
    def _parse_price(self, text) -> float: ...
    def _parse_sqm(self, text) -> float: ...

# Concrete implementation
class ImotBgScraper(BaseSiteScraper):
    async def extract_listing(self, html, url) -> ListingData:
        # Site-specific extraction
        price = self._parse_price(text)  # Uses inherited helper
```

---

## 3. Factory Pattern

Object creation abstracted behind factory functions.

```python
# Scraper factory (websites/__init__.py)
def get_scraper(site: str) -> Optional[BaseSiteScraper]:
    if site == "imot.bg":
        return ImotBgScraper()
    elif site == "bazar.bg":
        return BazarBgScraper()

# Browser factory (browsers/browsers_main.py)
async def create_instance(browser_type: str, ...) -> BrowserHandle:
    strategy_class = _strategy_registry[browser_type]
    return BrowserHandle(strategy_class())
```

---

## 4. Facade Pattern (proxies/proxies_main.py)

Simple interface to complex proxy subsystem.

```python
# Complex internal operations hidden behind simple facade
def setup_mubeng_rotator(port, min_live_proxies) -> Tuple[url, process, temp_file]:
    """Handles: load proxies, filter, write temp file, start mubeng, return URL"""

def scrape_proxies():
    """Triggers Celery task for proxy scraping"""
```

---

## 5. Orchestrator Pattern (orchestrator.py)

Manages lifecycle of multiple services.

```python
class Orchestrator:
    def __enter__(self):
        self._register_shutdown_handlers()
        return self

    def __exit__(self, ...):
        self.stop_all()

    def start_redis(self) -> bool: ...
    def start_celery(self) -> bool: ...
    def wait_for_proxies(self) -> bool: ...
    def stop_all(self): ...
```

**Usage**:
```python
with Orchestrator() as orch:
    orch.start_redis()
    orch.start_celery()
    orch.wait_for_proxies()
    # ... scraping work ...
# Automatic cleanup on exit
```

---

## 6. Pipeline Pattern (Data Processing)

Data flows through sequential processing stages.

```
Proxy Pipeline:
  Scrape (PSC) → Liveness (mubeng) → Anonymity → Quality → live_proxies.json

Scraping Pipeline:
  URLs → Browser → HTML → Parser → ListingData → SQLite

Evaluation Pipeline:
  Listing → Deal Breakers → Scoring → Display
```

---

## 7. Registry Pattern (browsers/)

Dynamic strategy discovery and registration.

```python
_strategy_registry: Dict[str, Type[BaseBrowserStrategy]] = {}

def _discover_strategies():
    """Auto-discovers strategy classes via pkgutil"""
    for module in strategies:
        if issubclass(item, BaseBrowserStrategy):
            register_strategy(name, item)
```

---

## 8. Data Transfer Objects (DTOs)

Dataclasses for structured data passing.

```python
@dataclass
class ListingData:
    external_id: str
    url: str
    price_eur: Optional[float]
    sqm_total: Optional[float]
    # ... 30+ fields

@dataclass
class SiteConfig:
    limit: int = 100
    delay: float = 6.0
    timeout: int = 30
```

---

## 9. Mixin Pattern (ScraplingMixin)

Adds Scrapling parsing capabilities to scrapers via composition.

```python
# Mixin class (websites/scrapling_base.py)
class ScraplingMixin:
    """Adds fast parsing with adaptive selectors."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adaptive_mode = True

    def parse(self, html: str, url: str = "") -> Adaptor: ...
    def css(self, page, selector, identifier="", auto_save=False, auto_match=False) -> List: ...
    def css_first(self, page, selector, ...) -> Optional[Element]: ...
    def get_text(self, element) -> str: ...
    def get_attr(self, element, attr) -> str: ...

# Usage in scraper (websites/imot_bg/imot_scraper.py)
class ImotBgScraper(ScraplingMixin, BaseSiteScraper):
    """Inherits both parsing capabilities and scraper interface."""
```

**Adaptive Mode** (selector resilience):
- First run: `auto_save=True` saves element signatures to `data/scrapling_selectors/`
- Subsequent runs: `auto_match=True` finds elements even if CSS selectors break
- Toggle via: `scraper.adaptive_mode = True/False`

**Benefits over BeautifulSoup**:
- 774x faster parsing
- Auto-encoding detection (windows-1251, UTF-8 for Bulgarian sites)
- Adaptive selectors survive site HTML changes

---

## 10. Retry Pattern with Exponential Backoff (resilience/)

Automatic retry of failed operations with increasing delays between attempts.

```python
# Decorator-based retry (resilience/retry.py)
@retry_with_backoff(max_attempts=5, base_delay=2.0)
def fetch_page(url):
    return requests.get(url)

@retry_with_backoff_async(max_attempts=5)
async def fetch_page_async(url):
    async with aiohttp.ClientSession() as session:
        return await session.get(url)
```

**Key Features**:
- **Exponential backoff**: `delay = base * (2^attempt)`
- **Jitter**: Random delay added to prevent thundering herd
- **Smart classification**: Uses `classify_error()` to determine if error is retryable
- **Configurable**: Max attempts, base delay, jitter factor

**Calculation**:
```python
# Base delay: 2.0s, jitter factor: 0.5
# Attempt 0: 2.0s + (0-1.0s jitter) = 2.0-3.0s
# Attempt 1: 4.0s + (0-2.0s jitter) = 4.0-6.0s
# Attempt 2: 8.0s + (0-4.0s jitter) = 8.0-12.0s
```

---

## 11. Error Classification Pattern (resilience/)

Maps exceptions and HTTP codes to recovery strategies.

```python
# Error classification (resilience/error_classifier.py)
class ErrorType(Enum):
    NETWORK_TIMEOUT = "network_timeout"
    HTTP_RATE_LIMIT = "http_rate_limit"
    HTTP_BLOCKED = "http_blocked"
    PARSE_ERROR = "parse_error"
    # ... 10 total types

class RecoveryAction(Enum):
    RETRY_IMMEDIATE = "retry_immediate"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RETRY_WITH_PROXY = "retry_with_proxy"
    SKIP = "skip"
    CIRCUIT_BREAK = "circuit_break"
    MANUAL_REVIEW = "manual_review"

# Usage
error_type = classify_error(exception, http_status=429)
action, is_recoverable, max_retries = get_recovery_info(error_type)
```

**Decision Map**:
| Error Type | Recovery Action | Retries | Notes |
|-----------|----------------|---------|-------|
| `NETWORK_TIMEOUT` | `RETRY_WITH_BACKOFF` | 3 | Transient network issue |
| `HTTP_RATE_LIMIT` (429) | `RETRY_WITH_BACKOFF` | 5 | Respect rate limits |
| `HTTP_BLOCKED` (403) | `CIRCUIT_BREAK` | 2 | Domain protection |
| `PARSE_ERROR` | `MANUAL_REVIEW` | 0 | Needs code fix |
| `NOT_FOUND` (404) | `SKIP` | 0 | Permanent failure |
| `PROXY_ERROR` | `RETRY_WITH_PROXY` | 5 | Rotate and retry |

---

## Key Components Using Patterns

| Pattern | Location | Key Classes/Functions |
|---------|----------|----------------------|
| Strategy | `browsers/strategies/` | `BaseBrowserStrategy`, `ChromiumStrategy` |
| Template | `websites/` | `BaseSiteScraper`, `ImotBgScraper` |
| Factory | `websites/__init__.py`, `browsers/browsers_main.py` | `get_scraper()`, `create_instance()` |
| Facade | `proxies/proxies_main.py` | `setup_mubeng_rotator()` |
| Orchestrator | `orchestrator.py` | `Orchestrator` class |
| Registry | `browsers/browsers_main.py` | `_strategy_registry` |
| DTO | `websites/base_scraper.py` | `ListingData` |
| Mixin | `websites/scrapling_base.py` | `ScraplingMixin` |
| Retry | `resilience/retry.py` | `retry_with_backoff()`, `retry_with_backoff_async()` |
| Error Classification | `resilience/error_classifier.py` | `classify_error()`, `get_recovery_info()` |
