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
