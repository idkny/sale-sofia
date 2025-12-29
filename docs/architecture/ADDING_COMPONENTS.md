# Adding New Components

> Step-by-step guides for extending the system. Read when adding scrapers or proxy sources.

---

## Adding a New Scraper

You have two options for adding a new website scraper:

1. **Config-driven (Generic Scraper)** - YAML only, no code (experimental)
2. **Custom Scraper** - Full Python implementation (production-ready)

---

## Option 1: Generic Scraper (Experimental)

**Best for**: Sites with standard HTML structure and stable selectors.

**Status**: Phase 1 complete (148 passing tests), not yet tested in production.

### 1. Create YAML Config

Create `config/sites/{site_name}.yaml`:

```yaml
site:
  name: example.bg
  domain: www.example.bg
  encoding: utf-8

urls:
  listing_pattern: "/listing/"
  id_pattern: "/listing/([^/]+)"

pagination:
  type: numbered
  param: page
  start: 1
  max_pages: 50

listing_page:
  container: ".listing-card"
  link: "a.listing-link"

detail_page:
  selectors:
    # Each field has a fallback chain - try in order
    price:
      - "span.price-main"
      - ".price-label strong"
      - "h3.css-price"
    sqm:
      - "li:contains('Квадратура') span"
      - "[data-code='m'] span"
    rooms:
      - "li:contains('Стаи') span"
    # ... add all needed fields

  field_types:
    price: currency_bgn_eur
    sqm: number
    rooms: integer
    floor: floor_pattern
    images: list
```

### 2. Use ConfigScraper

```python
from websites.generic import ConfigScraper

# Load scraper from config
scraper = ConfigScraper("config/sites/example_bg.yaml")

# Extract listing
html = fetch_page(url)
listing = await scraper.extract_listing(html, url)
```

### 3. Supported Field Types

| Type | Example Input | Parsed Output |
|------|---------------|---------------|
| `text` | "Студио в центъра" | "Студио в центъра" |
| `number` | "75.5 кв.м" | 75.5 |
| `integer` | "3 стаи" | 3 |
| `currency_bgn_eur` | "150 000 лв." | 76,500.0 (EUR) |
| `floor_pattern` | "3/6" or "3 от 6" | (3, 6) |
| `list` | Multiple images | ["url1", "url2"] |

### 4. Advantages

- No Python code required
- Fallback selector chains (resilient to site changes)
- Reuses existing infrastructure (Scrapling, resilience, Celery)
- Fast iteration (edit YAML, test immediately)

### 5. Limitations

- Experimental (not production-tested yet)
- Best for standard HTML structures
- Complex extraction logic requires custom scraper

For full documentation, see `docs/specs/116_GENERIC_SCRAPER_TEMPLATE.md`

---

## Option 2: Custom Scraper (Production-Ready)

**Best for**: Complex sites, special extraction logic, production use.

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

Use ScraplingMixin for DOM operations:

```python
from ..base_scraper import BaseSiteScraper, ListingData
from ..scrapling_base import ScraplingMixin

class NewsiteBgScraper(BaseSiteScraper, ScraplingMixin):
    def __init__(self):
        super().__init__()
        self.site_name = "newsite.bg"
        self.base_url = "https://www.newsite.bg"

    async def extract_listing(self, html, url) -> Optional[ListingData]:
        # Parse HTML with Scrapling Adaptor
        adaptor = self.parse_html(html)

        # Use CSS selectors
        price = adaptor.css_first("span.price")
        sqm = adaptor.css_first("span.area")

        return ListingData(
            price_eur=self.extract_number(price.text if price else None),
            sqm_total=self.extract_number(sqm.text if sqm else None),
            # ... other fields
        )

    async def extract_search_results(self, html) -> List[str]:
        # Return list of listing URLs from search page
        adaptor = self.parse_html(html)
        links = adaptor.css("a.listing-link")
        return [link.attrib.get("href") for link in links]
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

## Using Scrapling Fetchers

The system uses Scrapling for all HTTP fetching. Two fetchers are available:

### Fetcher (Fast HTTP)

For simple pages without anti-bot protection:

```python
from scrapling.fetchers import Fetcher

response = Fetcher.fetch(
    url="https://example.com/search",
    proxy="http://localhost:8089",
    timeout=15000
)
html = response.html_content
```

### StealthyFetcher (Anti-Bot Bypass)

For pages with Cloudflare or similar protection:

```python
from scrapling.fetchers import StealthyFetcher

response = StealthyFetcher.fetch(
    url="https://example.com/listing/123",
    proxy="http://localhost:8089",
    humanize=True,
    block_webrtc=True,
    network_idle=True,
    timeout=30000
)
html = response.html_content
```

**Important**: Always use a proxy. The mubeng rotator runs on `localhost:8089`.

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
| Scrapers | `websites/__init__.py`, `websites/base_scraper.py`, `websites/scrapling_base.py` |
| Fetching | Use `scrapling.fetchers.Fetcher` or `StealthyFetcher` in `main.py` |
| Proxies | `proxies/tasks.py`, `proxies/proxies_main.py` |
| Config | `config/start_urls.yaml`, `config/loader.py` |
