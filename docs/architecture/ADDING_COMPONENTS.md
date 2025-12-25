# Adding New Components

> Step-by-step guides for extending the system. Read when adding scrapers, browsers, or proxy sources.

---

## Adding a New Scraper

### 1. Create folder structure

```
websites/newsite_bg/
├── __init__.py      # Empty
├── selectors.py     # CSS/regex patterns
└── newsite_scraper.py
```

### 2. Create selectors.py

```python
# CSS selectors for the site
LISTING_CONTAINER = "div.listing-item"
PRICE_SELECTOR = "span.price"
SQM_SELECTOR = "span.area"
# ... add all needed selectors
```

### 3. Create scraper class

```python
from ..base_scraper import BaseSiteScraper, ListingData

class NewsiteBgScraper(BaseSiteScraper):
    def __init__(self):
        super().__init__()
        self.site_name = "newsite.bg"
        self.base_url = "https://www.newsite.bg"

    async def extract_listing(self, html, url) -> Optional[ListingData]:
        # Implement extraction using selectors
        pass

    async def extract_search_results(self, html) -> List[str]:
        # Return list of listing URLs from search page
        pass
```

### 4. Register in websites/__init__.py

```python
AVAILABLE_SITES["newsite.bg"] = {
    "description": "New site description",
    "implemented": True,
    "url": "https://www.newsite.bg",
}

def get_scraper(site: str):
    # ... existing code ...
    elif site == "newsite.bg":
        from .newsite_bg.newsite_scraper import NewsiteBgScraper
        return NewsiteBgScraper()
```

### 5. Add URLs to config/start_urls.yaml

```yaml
newsite.bg:
  - "https://www.newsite.bg/search?type=apartment&city=sofia"
```

---

## Adding a New Browser Strategy

### 1. Create strategy file

**Location**: `browsers/strategies/newbrowser.py`

```python
from .base import BaseBrowserStrategy
from typing import Tuple
from playwright.async_api import Browser, BrowserContext

class NewBrowserStrategy(BaseBrowserStrategy):
    async def launch(self) -> Tuple[Browser, BrowserContext]:
        # Launch and configure browser
        # Return (browser, context)
        pass

    async def close(self) -> None:
        # Cleanup resources
        pass
```

### 2. Auto-discovery

Strategy is **auto-discovered** via naming convention:
- Class must end with `Strategy`
- File must be in `browsers/strategies/`

No manual registration needed.

### 3. Usage

```python
from browsers.browsers_main import create_instance

handle = await create_instance("newbrowser", proxy=proxy_url)
```

---

## Adding a New Proxy Source

### 1. Create fetcher module

**Location**: `proxies/get_newproxy.py`

```python
from typing import List, Dict
import httpx

def fetch_proxies() -> List[Dict]:
    """Fetch proxies from new source.

    Returns:
        List of proxy dicts with keys: ip, port, protocol
    """
    response = httpx.get("https://proxy-source.com/api")
    proxies = []
    for item in response.json():
        proxies.append({
            "ip": item["ip"],
            "port": item["port"],
            "protocol": "http"  # or socks5
        })
    return proxies
```

### 2. Integrate into tasks.py

**Location**: `proxies/tasks.py`

```python
from .get_newproxy import fetch_proxies as fetch_newproxy

@app.task
def scrape_all_proxies():
    # Existing sources
    proxies = []
    proxies.extend(run_psc())

    # Add new source
    proxies.extend(fetch_newproxy())

    return proxies
```

---

## Key Files Reference

| Component | Key Files |
|-----------|-----------|
| Scrapers | `websites/__init__.py`, `websites/base_scraper.py` |
| Browsers | `browsers/browsers_main.py`, `browsers/strategies/base.py` |
| Proxies | `proxies/tasks.py`, `proxies/proxies_main.py` |
| Config | `config/start_urls.yaml`, `config/loader.py` |
