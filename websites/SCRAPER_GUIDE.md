# Website Scraper Development Guide

## Overview

This guide explains how to create a new website scraper for the sale-sofia project. Each website lives in its own folder under `websites/` and follows a consistent pattern.

## Current Architecture

```
websites/
├── __init__.py              # Registry + get_scraper() factory
├── base_scraper.py          # BaseSiteScraper ABC + ListingData dataclass
├── scrapling_base.py        # ScraplingMixin - fast parsing with encoding support
├── http_client.py           # [TODO] Shared HTTP wrapper
├── SCRAPER_GUIDE.md         # This file
└── {site_name}/
    ├── __init__.py
    ├── {site_name}_scraper.py  # Main scraper class (e.g., imot_scraper.py)
    ├── selectors.py            # [Optional] CSS/XPath selectors
    └── tests/               # [Optional] Test HTML fixtures
```

### Scrapling vs BeautifulSoup

We use **Scrapling** instead of BeautifulSoup for:
- **774x faster** parsing performance
- **Auto-encoding detection** (windows-1251, UTF-8 for Bulgarian sites)
- **Adaptive selectors** that survive site changes
- **StealthyFetcher** for anti-bot bypass

---

## Step 1: Analyze the Target Website

Before writing any code, manually analyze the website:

### 1.1 Identify URL Patterns

```
[ ] Search/listing page URL structure
    Example: https://example.com/apartments/sofia?page=1

[ ] Individual property page URL structure
    Example: https://example.com/property/12345-apartment-sofia

[ ] How is the property ID encoded in the URL?

[ ] Pagination pattern
    - Query param: ?page=2
    - Path segment: /p-2 or /page/2
    - POST request with offset
```

### 1.2 Identify Page Structure

```
Search Results Page:
[ ] Container element for all listings (CSS selector or XPath)
[ ] Individual listing card selector
[ ] Link to property detail page
[ ] Any preview data shown (price, sqm, thumbnail)
[ ] Pagination controls location
[ ] "Next page" button/link selector
[ ] How to detect LAST page (no next button? empty results? page count?)

Property Detail Page:
[ ] Price location and format
[ ] Size (sqm) location and format
[ ] Room count location
[ ] Floor info location
[ ] Building type indicators
[ ] Location/neighborhood info
[ ] Features list (balcony, elevator, parking, etc.)
[ ] Image gallery structure
[ ] Agent/agency contact info
[ ] Description text container
```

### 1.3 Check for Anti-Scraping Measures

```
[ ] Does it require JavaScript rendering? (Use browser vs requests)
[ ] Does it have rate limiting?
[ ] Does it require cookies/session?
[ ] Does it detect bots (Cloudflare, captcha)?
[ ] Does it have an API? (Check Network tab for JSON responses)
```

---

## Step 2: Create the Folder Structure

```bash
mkdir -p websites/{site_name}
touch websites/{site_name}/__init__.py
touch websites/{site_name}/{site_name}_scraper.py
```

---

## Step 3: Implement the Scraper Class

### 3.1 Minimal Template

```python
"""
{site_name} scraper implementation.

Site structure:
- Search URL: {search_url_pattern}
- Pagination: {pagination_pattern}
- Listing URL: {listing_url_pattern}
"""

import re
from typing import List, Optional
from scrapling import Adaptor
from loguru import logger

from ..base_scraper import BaseSiteScraper, ListingData
from ..scrapling_base import ScraplingMixin

# LLM integration (optional - enabled via use_llm flag)
try:
    from llm import extract_description as llm_extract, get_confidence_threshold
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def get_confidence_threshold(): return 0.7  # Fallback


class {SiteName}Scraper(ScraplingMixin, BaseSiteScraper):
    """{Site description}."""

    def __init__(self):
        super().__init__()
        self.site_name = "{site_name}"
        self.base_url = "https://www.{site_domain}"
        self.search_base = "https://www.{site_domain}/{search_path}"
        self.use_llm = False  # Set True to enable LLM gap-filling

    # =========================================
    # REQUIRED: Implement these abstract methods
    # =========================================

    async def extract_listing(self, html: str, url: str) -> Optional[ListingData]:
        """Extract listing data from a single property page."""
        page = self.parse(html, url)  # Scrapling Adaptor
        text = self.get_page_text(page)  # Full page text for regex

        # 1. Extract external ID from URL
        external_id = self._extract_id_from_url(url)
        if not external_id:
            logger.warning(f"Could not extract ID from: {url}")
            return None

        # 2. Extract all fields (implement _extract_* methods below)
        # ...

        return ListingData(
            external_id=external_id,
            url=url,
            source_site=self.site_name,
            # ... other fields
        )

    async def extract_search_results(self, html: str) -> List[str]:
        """Extract listing URLs from search results page."""
        page = self.parse(html)
        listing_urls = []

        # Find all listing links using CSS selectors
        for link in self.css(page, "CSS_SELECTOR_HERE"):
            href = self.get_attr(link, "href")
            if href:
                listing_urls.append(href)

        logger.info(f"Found {len(listing_urls)} listings")
        return listing_urls

    # =========================================
    # REQUIRED: Pagination methods
    # =========================================

    def get_search_url(self, page: int = 1) -> str:
        """Get search URL for given page number."""
        if page == 1:
            return self.search_base
        # TODO: Implement pagination URL pattern
        return f"{self.search_base}?page={page}"

    def get_next_page_url(self, current_url: str, current_page: int) -> str:
        """Get URL for next page of results."""
        return self.get_search_url(current_page + 1)

    def is_last_page(self, html: str, current_page: int) -> bool:
        """
        Detect if this is the last page of results.

        Common patterns:
        - No "next" button
        - Empty listing results
        - Current page >= total pages shown
        - "No results" message appears
        """
        page = self.parse(html)
        text = self.get_page_text(page)

        # Pattern 1: Check if next button exists
        # next_btn = self.css_first(page, ".pagination .next")
        # if not next_btn:
        #     return True

        # Pattern 2: Check if results are empty
        # listings = self.css(page, ".listing-card")
        # if len(listings) == 0:
        #     return True

        # Pattern 3: Compare current page to total
        # total_pages = self._extract_total_pages(text)
        # if current_page >= total_pages:
        #     return True

        return False

    # =========================================
    # PRIVATE: Site-specific extraction methods
    # =========================================

    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract listing ID from URL."""
        # TODO: Implement regex for this site's URL pattern
        match = re.search(r"/property/(\d+)", url)
        return match.group(1) if match else None

    # Add more _extract_* methods as needed...
```

### 3.2 ScraplingMixin Methods Reference

| Method | Purpose | Example |
|--------|---------|---------|
| `self.parse(html, url)` | Parse HTML → Adaptor | `page = self.parse(html, url)` |
| `self.css(page, sel)` | Select multiple elements | `links = self.css(page, "a.listing")` |
| `self.css_first(page, sel)` | Select first element | `title = self.css_first(page, "h1")` |
| `self.get_text(el)` | Get element text | `text = self.get_text(title)` |
| `self.get_attr(el, attr)` | Get attribute | `href = self.get_attr(link, "href")` |
| `self.get_page_text(page)` | Full page text | `text = self.get_page_text(page)` |
| `self.fetch(url, proxy)` | Fetch with encoding | `page = self.fetch(url)` |
| `self.fetch_stealth(url)` | Anti-bot fetch (no proxy by default) | `page = self.fetch_stealth(url)` |

### 3.3 Adaptive Mode (Selector Resilience)

Scrapling's adaptive mode allows selectors to auto-heal when site HTML structure changes.

**How it works:**
1. **First run**: `auto_save=True` saves element signatures to `data/scrapling_selectors/`
2. **Subsequent runs**: `auto_match=True` finds elements even if CSS selectors break
3. **Toggle**: `scraper.adaptive_mode = True/False`

**Usage in selectors:**

```python
class MyScraper(ScraplingMixin, BaseSiteScraper):
    def __init__(self):
        super().__init__()
        self.adaptive_mode = True  # Enable adaptive matching

    def _extract_title(self, page: Adaptor) -> str:
        # With adaptive mode - selector can survive site changes
        title = self.css_first(
            page,
            "h1.listing-title",
            identifier="mysite_title",      # Unique ID for this selector
            auto_save=True,                  # Save signature on first run
            auto_match=self.adaptive_mode,   # Use fuzzy matching when enabled
        )
        return self.get_text(title) if title else ""
```

**Key parameters:**
| Parameter | Purpose |
|-----------|---------|
| `identifier` | Unique ID for this selector (e.g., "imot_title") |
| `auto_save` | Save element signature for future matching |
| `auto_match` | Enable fuzzy matching when selector breaks |

**Current adaptive selectors:**
- `imot_scraper.py`: 8 selectors (listing_links, pagination, images, title, h1, description, contact_links, image_links)
- `bazar_scraper.py`: 7 selectors (listing_links, pagination, images, title, h1, description, image_links)

**Selector storage location:** `data/scrapling_selectors/{site_name}_selectors.json`

---

### 3.4 LLM Integration (Optional)

The LLM module can fill gaps in CSS extraction by analyzing the description text. This is useful when CSS selectors can't extract certain fields.

**How it works:**
1. CSS extraction runs first (fast, reliable)
2. If `use_llm = True` and description exists, LLM analyzes description
3. LLM fills gaps - only overrides fields that CSS returned `None`
4. Confidence threshold prevents bad extractions from being used

**Enable LLM in your scraper:**

```python
class MyScraper(ScraplingMixin, BaseSiteScraper):
    def __init__(self):
        super().__init__()
        self.use_llm = True  # Enable LLM gap-filling
```

**Use LLM in extract_listing():**

```python
async def extract_listing(self, html: str, url: str) -> Optional[ListingData]:
    # ... CSS extraction first ...
    rooms_count = self._extract_rooms(page_text)
    orientation = self._extract_orientation(page_text)
    description = self._extract_description(page)

    # LLM enrichment: fill gaps in CSS extraction
    if self.use_llm and LLM_AVAILABLE and description:
        try:
            llm_result = llm_extract(description)
            if llm_result.confidence >= get_confidence_threshold():
                # Fill gaps - only override if CSS returned None
                if rooms_count is None and llm_result.rooms:
                    rooms_count = llm_result.rooms
                if orientation is None and llm_result.orientation:
                    orientation = llm_result.orientation
                # ... more fields ...
                logger.debug(f"LLM enriched listing (confidence: {llm_result.confidence:.2f})")
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")

    return ListingData(...)
```

**LLM Configuration:**

The confidence threshold is configurable in `config/ollama.yaml`:

```yaml
ollama:
  confidence_threshold: 0.7  # Min confidence to accept LLM results
```

**LLM Metrics:**

Track extraction performance with:

```python
from llm import get_metrics, reset_metrics

metrics = get_metrics()
# Returns:
#   extractions_total: int
#   extractions_success: int
#   cache_hits: int
#   avg_time_ms: float
#   avg_confidence: float
#   cache_hit_rate: float
```

**LLM-extracted fields:**
- rooms, bedrooms, bathrooms
- orientation, heating_type, condition
- has_elevator, has_parking, has_balcony, has_storage
- furnishing, has_view, view_type, parking_type

**When to use LLM:**
- Bulgarian descriptions with complex formatting
- Fields that can't be reliably extracted with CSS/regex
- Sites with inconsistent HTML structure

**When NOT to use LLM:**
- Fields available via structured CSS (price, sqm)
- High-frequency scraping (LLM adds ~2-5s per listing)
- When CSS extraction is reliable

---

### 3.5 Required Methods Checklist

```
[ ] extract_listing(html, url) -> ListingData
[ ] extract_search_results(html) -> List[str]
[ ] get_search_url(page) -> str
[ ] get_next_page_url(current_url, current_page) -> str
[ ] is_last_page(html, current_page) -> bool
```

---

## Step 4: Register the Scraper

### 4.1 Update `websites/__init__.py`

```python
# Add to AVAILABLE_SITES dict
AVAILABLE_SITES = {
    # ... existing sites ...
    "{site_name}": {
        "description": "Description of the site",
        "implemented": True,  # Set to True when ready
        "url": "https://www.{site_domain}",
    },
}

# Add to get_scraper() function
def get_scraper(site: str) -> Optional[BaseSiteScraper]:
    # ... existing code ...
    elif site == "{site_name}":
        from .{site_name}.{site_name}_scraper import {SiteName}Scraper
        return {SiteName}Scraper()
```

---

## Step 5: HTTP Response Wrapper (TODO - NOT YET IMPLEMENTED)

All scrapers need consistent HTTP response handling. This wrapper should be created in `websites/http_client.py`.

### 5.1 Proposed Interface

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class ResponseStatus(Enum):
    """Categorized HTTP response status."""
    SUCCESS = "success"           # 2xx - got content
    REDIRECT = "redirect"         # 3xx - need to follow
    CLIENT_ERROR = "client_error" # 4xx - our fault (bad URL, auth)
    SERVER_ERROR = "server_error" # 5xx - their fault (retry later)
    TIMEOUT = "timeout"           # Connection/read timeout
    BLOCKED = "blocked"           # Captcha, rate limit, ban
    PARSE_ERROR = "parse_error"   # Got HTML but can't parse


@dataclass
class ScraperResponse:
    """Standardized response from any HTTP request."""

    status: ResponseStatus
    status_code: Optional[int] = None
    html: Optional[str] = None
    url: str = ""                    # Final URL after redirects
    error_message: Optional[str] = None
    retry_after: Optional[int] = None  # Seconds to wait before retry
    headers: Dict[str, str] = None

    @property
    def is_success(self) -> bool:
        return self.status == ResponseStatus.SUCCESS

    @property
    def should_retry(self) -> bool:
        """Whether this error is temporary and worth retrying."""
        return self.status in (
            ResponseStatus.SERVER_ERROR,
            ResponseStatus.TIMEOUT,
        )

    @property
    def is_blocked(self) -> bool:
        """Whether we hit anti-bot protection."""
        return self.status == ResponseStatus.BLOCKED


class HttpClient:
    """
    Shared HTTP client with:
    - Automatic retry with backoff
    - Proxy support
    - Response categorization
    - Rate limiting
    """

    def __init__(
        self,
        proxy_pool=None,
        max_retries: int = 3,
        timeout: int = 30,
        rate_limit_delay: float = 1.0,
    ):
        self.proxy_pool = proxy_pool
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay

    async def fetch(self, url: str, **kwargs) -> ScraperResponse:
        """
        Fetch a URL with automatic error categorization.

        Returns:
            ScraperResponse with categorized status
        """
        # TODO: Implement with:
        # - httpx or aiohttp
        # - Proxy rotation from proxy_pool
        # - Automatic retries for 5xx/timeout
        # - Captcha/block detection
        # - Rate limiting between requests
        pass

    def _categorize_response(
        self,
        status_code: int,
        html: str
    ) -> ResponseStatus:
        """Categorize HTTP response into our status enum."""

        if 200 <= status_code < 300:
            # Check for soft blocks (captcha in 200 response)
            if self._is_blocked_page(html):
                return ResponseStatus.BLOCKED
            return ResponseStatus.SUCCESS

        elif 300 <= status_code < 400:
            return ResponseStatus.REDIRECT

        elif status_code == 403:
            return ResponseStatus.BLOCKED

        elif status_code == 429:
            return ResponseStatus.BLOCKED  # Rate limited

        elif 400 <= status_code < 500:
            return ResponseStatus.CLIENT_ERROR

        elif 500 <= status_code < 600:
            return ResponseStatus.SERVER_ERROR

        return ResponseStatus.CLIENT_ERROR

    def _is_blocked_page(self, html: str) -> bool:
        """Detect captcha/block pages that return 200."""
        block_indicators = [
            "captcha",
            "cloudflare",
            "access denied",
            "rate limit",
            "too many requests",
            "please verify",
            "are you a robot",
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in block_indicators)
```

### 5.2 Usage in Scrapers

```python
from websites.http_client import HttpClient, ResponseStatus

class MyScraper(BaseSiteScraper):
    def __init__(self, http_client: HttpClient = None):
        super().__init__()
        self.http = http_client or HttpClient()

    async def scrape_search_page(self, page: int) -> List[str]:
        url = self.get_search_url(page)
        response = await self.http.fetch(url)

        if response.is_blocked:
            logger.warning(f"Blocked on {url}, switching proxy")
            # Handle block...
            return []

        if response.should_retry:
            logger.info(f"Temporary error on {url}, will retry")
            # Retry logic handled by http_client
            return []

        if not response.is_success:
            logger.error(f"Failed to fetch {url}: {response.error_message}")
            return []

        return await self.extract_search_results(response.html)
```

---

## Step 6: Scraping Flow

The complete scraping flow for any website:

```
┌─────────────────────────────────────────────────────────────────┐
│                        SCRAPING FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. START                                                       │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────┐                          │
│  │ get_search_url(page=1)           │                          │
│  │ → "https://site.com/search"      │                          │
│  └──────────────────────────────────┘                          │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────┐                          │
│  │ http_client.fetch(url)           │  ◄─── Proxy + Retry      │
│  │ → ScraperResponse                │                          │
│  └──────────────────────────────────┘                          │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────┐                          │
│  │ Check response.status            │                          │
│  │ SUCCESS? → continue              │                          │
│  │ BLOCKED? → rotate proxy, retry   │                          │
│  │ ERROR?   → log, skip             │                          │
│  └──────────────────────────────────┘                          │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────┐                          │
│  │ extract_search_results(html)     │                          │
│  │ → ["url1", "url2", "url3", ...]  │                          │
│  └──────────────────────────────────┘                          │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────┐                          │
│  │ For each listing_url:            │                          │
│  │   fetch(listing_url)             │                          │
│  │   extract_listing(html, url)     │                          │
│  │   → ListingData                  │                          │
│  │   save to database               │                          │
│  └──────────────────────────────────┘                          │
│     │                                                           │
│     ▼                                                           │
│  ┌──────────────────────────────────┐                          │
│  │ is_last_page(html, page)?        │                          │
│  │ YES → DONE                       │                          │
│  │ NO  → page++, go to step 2       │                          │
│  └──────────────────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 7: Testing Your Scraper

### 7.1 Save Test HTML

```bash
# Save a search results page
curl "https://site.com/search" > websites/{site_name}/tests/search_page.html

# Save a listing page
curl "https://site.com/property/12345" > websites/{site_name}/tests/listing_page.html
```

### 7.2 Write Unit Tests

```python
# websites/{site_name}/tests/test_scraper.py

import pytest
from pathlib import Path
from ..scraper import {SiteName}Scraper

@pytest.fixture
def scraper():
    return {SiteName}Scraper()

@pytest.fixture
def search_html():
    path = Path(__file__).parent / "search_page.html"
    return path.read_text()

@pytest.fixture
def listing_html():
    path = Path(__file__).parent / "listing_page.html"
    return path.read_text()

@pytest.mark.asyncio
async def test_extract_search_results(scraper, search_html):
    urls = await scraper.extract_search_results(search_html)
    assert len(urls) > 0
    assert all("site.com" in url for url in urls)

@pytest.mark.asyncio
async def test_extract_listing(scraper, listing_html):
    listing = await scraper.extract_listing(
        listing_html,
        "https://site.com/property/12345"
    )
    assert listing is not None
    assert listing.external_id == "12345"
    assert listing.price_eur is not None
    assert listing.sqm_total is not None
```

---

## Appendix A: ListingData Fields Reference

From `base_scraper.py`:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| external_id | str | YES | Site's unique ID |
| url | str | YES | Full listing URL |
| source_site | str | YES | e.g., "imot.bg" |
| title | str | no | Page title |
| description | str | no | Full description text |
| price_eur | float | no | Price in EUR |
| price_per_sqm_eur | float | no | Calculated if price+sqm known |
| sqm_total | float | no | Total area |
| sqm_net | float | no | Net usable area |
| rooms_count | int | no | Number of rooms |
| bathrooms_count | int | no | Number of bathrooms |
| floor_number | int | no | Floor of apartment |
| floor_total | int | no | Total floors in building |
| has_elevator | bool | no | None = unknown |
| building_type | str | no | brick/panel/new_construction |
| construction_year | int | no | Year built |
| act_status | str | no | act14/act15/act16/old_building |
| district | str | no | City district |
| neighborhood | str | no | Specific neighborhood |
| address | str | no | Street address if shown |
| metro_station | str | no | Nearest metro |
| metro_distance_m | int | no | Distance in meters |
| orientation | str | no | E/S/W/N combinations |
| has_balcony | bool | no | None = unknown |
| has_garden | bool | no | None = unknown |
| has_parking | bool | no | None = unknown |
| has_storage | bool | no | None = unknown |
| heating_type | str | no | central/gas/electric/fireplace |
| condition | str | no | ready/renovation/bare_walls |
| image_urls | List[str] | no | All image URLs |
| main_image_url | str | no | Primary image |
| agency | str | no | Agency name |
| agent_name | str | no | Agent name |
| agent_phone | str | no | Contact phone |
| listing_date | datetime | no | When listed |
| scraped_at | datetime | auto | Auto-set on creation |
| features | List[str] | no | Raw features list |
| fingerprint | str | no | For deduplication |

---

## Appendix B: Common Bulgarian Real Estate Terms

```python
# Room types
ROOM_MAPPINGS = {
    "едностаен": 1,      # 1-room (studio)
    "двустаен": 2,       # 2-room
    "тристаен": 3,       # 3-room
    "четиристаен": 4,    # 4-room
    "многостаен": 5,     # 5+ rooms
    "мезонет": 3,        # Maisonette (2-floor apt)
}

# Building types
BUILDING_TYPES = {
    "панел": "panel",           # Panel (prefab concrete)
    "епк": "panel",             # Large panel
    "тухла": "brick",           # Brick
    "гредоред": "brick",        # Beam construction
    "ново строителство": "new", # New construction
}

# Features
FEATURES = {
    "асансьор": "elevator",
    "балкон": "balcony",
    "тераса": "terrace",
    "гараж": "garage",
    "паркомясто": "parking",
    "мазе": "basement_storage",
    "таван": "attic",
}

# Orientation
ORIENTATION = {
    "изток": "E",
    "запад": "W",
    "север": "N",
    "юг": "S",
    "югоизток": "SE",
    "югозапад": "SW",
    "североизток": "NE",
    "северозапад": "NW",
}
```

---

## Appendix C: Checklist for New Website

```
ANALYSIS PHASE
[ ] Identified search URL pattern
[ ] Identified listing URL pattern
[ ] Identified pagination pattern
[ ] Identified last-page detection method
[ ] Checked for JS rendering requirements
[ ] Checked for anti-bot protection
[ ] Noted rate limiting behavior

IMPLEMENTATION PHASE
[ ] Created websites/{site_name}/ folder
[ ] Created __init__.py
[ ] Created {site_name}_scraper.py with class
[ ] Implemented extract_listing()
[ ] Implemented extract_search_results()
[ ] Implemented get_search_url()
[ ] Implemented get_next_page_url()
[ ] Implemented is_last_page()
[ ] Added LLM import (optional)
[ ] Set use_llm flag (optional)
[ ] Added LLM gap-filling in extract_listing() (optional)
[ ] Added to AVAILABLE_SITES registry
[ ] Added to get_scraper() factory

TESTING PHASE
[ ] Saved test HTML files
[ ] Wrote unit tests for extraction
[ ] Tested pagination manually
[ ] Tested with proxies
[ ] Verified ListingData fields populated

DEPLOYMENT PHASE
[ ] Added rate limiting config
[ ] Configured proxy requirements
[ ] Added to main.py CLI options
```

---

## TODO / Missing Components

1. ~~**Scrapling integration**~~ ✅ DONE (2025-12-25)
   - `scrapling_base.py` with ScraplingMixin
   - Auto-encoding detection for Bulgarian sites
   - 774x faster parsing than BeautifulSoup

2. ~~**LLM integration**~~ ✅ DONE (2025-12-26)
   - `llm/` module with Ollama client
   - `use_llm` flag in ScraplingMixin
   - Gap-filling for fields CSS can't extract
   - Redis cache (7-day TTL, 3700+ extractions/sec on hit)
   - Configurable confidence threshold (`config/ollama.yaml`)
   - Metrics tracking (`get_metrics()`, `reset_metrics()`)

3. **HTTP Client wrapper** (`http_client.py`)
   - Standardized response handling
   - Automatic retry logic
   - Proxy integration
   - Block detection

4. **Orchestrator integration**
   - How scrapers connect to Celery tasks
   - Progress reporting
   - Error aggregation

5. **Rate limiter**
   - Per-site configuration
   - Adaptive delays

6. **Deduplication**
   - Fingerprint generation
   - Cross-site duplicate detection
