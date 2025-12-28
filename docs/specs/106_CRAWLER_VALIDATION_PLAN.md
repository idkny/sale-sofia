# 106: Crawler Validation & Enhancement Plan

**Status**: In Progress
**Created**: 2025-12-25
**Updated**: 2025-12-27
**Instance**: 2

---

## Executive Summary

This spec defines the step-by-step plan to validate existing scrapers, add missing capabilities, and build async orchestration with rate limiting.

**Key insight**: Canonical schema and base infrastructure already exist. Focus on validation, enhancement, and orchestration.

**Update 2025-12-27**: Status review after Specs 107-112 implementation:
- **Phase 0**: ✅ COMPLETE (Scrapling migration done)
- **Phase 1**: ✅ COMPLETE (46/46 tests passing, validation matrix documented)
- **Phase 2**: ⚠️ SUPERSEDED by LLM extraction (Specs 107/108/110 = 100% accuracy)
- **Phase 3**: ✅ COMPLETE (scrape_history + listing_changes tables, 30 tests)
- **Phase 3.5**: ❌ NOT STARTED
- **Phase 4**: 🔄 PARTIAL - Rate limiter done via Spec 112 (`resilience/rate_limiter.py`), orchestrator pending
- **Phase 5**: ❌ NOT STARTED

---

## Phase 0: Scrapling Integration (Foundation Upgrade) ✅ COMPLETE

**Goal**: Replace BeautifulSoup with Scrapling for adaptive, resilient scraping.

> **Status**: COMPLETE. Both imot.bg and bazar.bg scrapers migrated to Scrapling.

### Why Scrapling?

| Feature | Benefit |
|---------|---------|
| **Adaptive Scraping** | Auto-relocates selectors when sites change HTML |
| **StealthyFetcher** | Bypasses Cloudflare, fingerprint spoofing |
| **774x Faster** | Than BeautifulSoup for parsing |
| **Proxy Support** | Works with our mubeng rotation |
| **LLM Integration** | MCP server for AI extraction (Ollama) |

### 0.1 Installation & Setup

```bash
# Install Scrapling with all features
pip install "scrapling[all]"

# Install browser dependencies
scrapling install

# Add to requirements.txt
echo 'scrapling[all]>=0.2.9' >> requirements.txt
```

### 0.2 Create Base Scrapling Adapter

```python
# websites/scrapling_base.py
"""
Scrapling-based base scraper with adaptive element tracking.
Replaces BeautifulSoup while maintaining same interface.
"""

from scrapling import Adaptor
from scrapling.fetchers import StealthyFetcher, Fetcher
from pathlib import Path
from typing import Optional
import json

# Storage for adaptive selectors
SELECTOR_STORAGE = Path("data/scrapling_selectors")
SELECTOR_STORAGE.mkdir(parents=True, exist_ok=True)


class ScraplingBaseScraper:
    """Base class using Scrapling for parsing with adaptive selectors."""

    def __init__(self, site_name: str):
        self.site_name = site_name
        self.storage_path = SELECTOR_STORAGE / f"{site_name}_selectors.json"
        self._load_selectors()

    def _load_selectors(self):
        """Load saved selector patterns for adaptive matching."""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                self._selectors = json.load(f)
        else:
            self._selectors = {}

    def _save_selectors(self):
        """Save selector patterns for future adaptive matching."""
        with open(self.storage_path, "w") as f:
            json.dump(self._selectors, f, indent=2)

    def parse(self, html: str, url: str) -> Adaptor:
        """
        Parse HTML with Scrapling.
        Returns Adaptor object (similar to BeautifulSoup but faster).
        """
        return Adaptor(html, url=url, auto_save=True)

    def css(self, page: Adaptor, selector: str, adaptive: bool = True):
        """
        Select elements with optional adaptive matching.
        If site changed, Scrapling finds elements anyway.
        """
        return page.css(selector, adaptive=adaptive)

    def css_first(self, page: Adaptor, selector: str, adaptive: bool = True):
        """Select first matching element."""
        return page.css_first(selector, adaptive=adaptive)

    async def fetch_stealth(
        self,
        url: str,
        proxy: Optional[str] = None,
        solve_cloudflare: bool = True
    ) -> Adaptor:
        """
        Fetch page with StealthyFetcher (anti-bot bypass).
        Uses modified Firefox with fingerprint spoofing.
        """
        return StealthyFetcher.fetch(
            url,
            proxy=proxy or "http://localhost:8089",  # mubeng default
            solve_cloudflare=solve_cloudflare,
            humanize=True,
            geoip=True,
            block_webrtc=True,
            network_idle=True
        )

    async def fetch_fast(self, url: str, proxy: Optional[str] = None) -> Adaptor:
        """
        Fast HTTP fetch (no JS execution).
        Use for simple pages without protection.
        """
        return Fetcher.fetch(
            url,
            proxy=proxy or "http://localhost:8089"
        )
```

### 0.3 Migration: imot_scraper.py

**Before (BeautifulSoup):**
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
price_text = soup.select_one(".price").get_text()
```

**After (Scrapling with adaptive):**
```python
from scrapling import Adaptor

page = Adaptor(html, url=url, auto_save=True)
price_text = page.css_first(".price", adaptive=True).text
```

### 0.4 Migration: bazar_scraper.py

Same pattern as imot.bg - replace BeautifulSoup calls with Scrapling.

### 0.5 Enable Adaptive Mode

```python
# First run: Save baseline selectors
page = Adaptor(html, url=url, auto_save=True)
elements = page.css(".listing-card")  # Saves pattern

# Future runs: Find elements even if HTML changed
page = Adaptor(html, url=url)
elements = page.css(".listing-card", adaptive=True)  # Uses saved pattern
```

### 0.6 StealthyFetcher + Mubeng Integration

```python
from scrapling.fetchers import StealthyFetcher

# mubeng provides rotating proxy on localhost:8089
MUBENG_PROXY = "http://localhost:8089"

page = StealthyFetcher.fetch(
    "https://www.imot.bg/...",
    proxy=MUBENG_PROXY,
    solve_cloudflare=True,
    humanize=True,           # Human-like mouse movement
    geoip=True,              # Spoof location from IP
    block_webrtc=True,       # Prevent IP leak
    os_randomize=True,       # Random OS fingerprint
    disable_ads=True         # Block ads (faster)
)
```

### 0.7 Ollama LLM Integration for Description Extraction

```python
# websites/description_extractor_llm.py
"""
Use local Ollama LLM to extract structured data from descriptions.
Scrapling's MCP server integration.
"""

import ollama
import json
from typing import Optional
import hashlib
import redis

redis_client = redis.Redis()

EXTRACTION_PROMPT = """
Extract the following fields from this Bulgarian real estate listing description.
Return JSON only, no explanation.

Fields to extract:
- floor_number (int or null)
- floor_total (int or null)
- construction_year (int or null)
- orientation (string: N/S/E/W combinations or null)
- has_parking (bool or null)
- has_elevator (bool or null)
- metro_nearby (string: station name or null)
- renovation_year (int or null)

Description:
{description}

JSON:
"""

async def extract_from_description(description: str) -> dict:
    """
    Use Ollama to extract structured data from description text.
    Results cached in Redis by description hash.
    """
    if not description or len(description) < 20:
        return {}

    # Check cache first
    cache_key = f"desc_extract:{hashlib.md5(description.encode()).hexdigest()}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Call Ollama
    try:
        response = ollama.generate(
            model="llama3.2",  # or mistral, gemma2, etc.
            prompt=EXTRACTION_PROMPT.format(description=description),
            format="json"
        )

        result = json.loads(response["response"])

        # Cache for 7 days
        redis_client.setex(cache_key, 604800, json.dumps(result))

        return result

    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}")
        return {}
```

### 0.8 Test Plan

| Test | Command | Expected |
|------|---------|----------|
| Install | `pip install "scrapling[all]"` | Success |
| Browser setup | `scrapling install` | Browsers ready |
| Parse test | `python -c "from scrapling import Adaptor"` | No error |
| Fetch test | Test with imot.bg search page | Returns HTML |
| Proxy test | StealthyFetcher + mubeng | Rotated IP |
| Adaptive test | Change selector, still finds element | Success |

---

## Phase 1: Scraper Validation (Foundation) ✅ COMPLETE

**Goal**: Verify each scraper can complete the full crawl cycle.

> **Status**: COMPLETE. Test harness created (`tests/scrapers/`). 46 tests, all passing. Validation matrix documented in [106A_CRAWLER_VALIDATION_MATRIX.md](../../archive/specs/106A_CRAWLER_VALIDATION_MATRIX.md).

### 1.1 Create Test Harness

```
tests/scrapers/
├── conftest.py           # Shared fixtures
├── test_imot_bg.py       # imot.bg validation
├── test_bazar_bg.py      # bazar.bg validation
└── fixtures/
    ├── imot_listing.html     # Cached real page
    ├── imot_search.html      # Cached search results
    ├── bazar_listing.html
    └── bazar_search.html
```

**Why fixtures?** Test against cached HTML so tests don't hit live sites. Update fixtures periodically.

### 1.2 Per-Scraper Test Cases

For EACH scraper, test:

| Test | What it validates |
|------|-------------------|
| `test_reach_start_url` | Can navigate to search page |
| `test_extract_listing_urls` | Gets property URLs from search results |
| `test_pagination_detection` | Correctly identifies last page |
| `test_pagination_url_build` | Builds correct next page URL |
| `test_extract_listing_data` | Extracts all fields from property page |
| `test_normalize_to_schema` | Output matches `ListingData` schema |
| `test_db_save` | Can save to database without errors |

### 1.3 Validation Matrix Output

After Phase 1, produce this matrix:

| Site | Reach | Listings | Pagination | Extract | Normalize | Save |
|------|-------|----------|------------|---------|-----------|------|
| imot.bg | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| bazar.bg | ? | ? | ? | ? | ? | ? |
| homes.bg | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Deliverable**: All ✅ before proceeding to Phase 2.

---

## Phase 2: Description Extraction (Unstructured → Structured) ⚠️ SUPERSEDED

**Goal**: Extract valuable data hidden in description text.

> **Status**: SUPERSEDED. This phase proposed regex-based extraction. Instead, Specs 107/108/110 implemented LLM-based extraction with dictionary-first approach, achieving **100% accuracy**. The regex approach was never needed.
>
> See: `llm/dictionary.py`, `llm/llm_main.py`, `config/bulgarian_dictionary.yaml`

### 2.1 Fields to Extract from Description

| Field | Example in description | Regex pattern |
|-------|------------------------|---------------|
| `floor_number` | "Located on the 5th floor" | `(\d+)(?:st\|nd\|rd\|th)?\s*(?:floor\|етаж)` |
| `floor_total` | "of a 7-floor building" | `(?:of\s*(?:a\s*)?)(\d+)[-\s]*(?:floor\|етаж)` |
| `construction_year` | "Built in 2019" | `(?:built\|renovated\|година)\s*(?:in\s*)?(\d{4})` |
| `orientation` | "South-facing" | `(south\|north\|east\|west\|юг\|север\|изток\|запад)` |
| `metro_nearby` | "5 min to metro Vitosha" | `(\d+)\s*min.*metro\s*(\w+)` |
| `has_parking` | "Garage included" | `garage\|гараж\|паркомясто` |

### 2.2 Implementation

```python
# websites/description_extractor.py

class DescriptionExtractor:
    """Extract structured data from unstructured description text."""

    def __init__(self):
        self.patterns = self._load_patterns()

    def extract(self, description: str) -> dict:
        """Returns dict of extracted fields (may be empty)."""
        results = {}
        for field, pattern in self.patterns.items():
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                results[field] = self._parse_match(field, match)
        return results

    def merge_with_listing(self, listing: ListingData, extracted: dict) -> ListingData:
        """Merge extracted data. Structured fields win on conflict."""
        for field, value in extracted.items():
            # Only fill if listing doesn't already have this field
            if getattr(listing, field, None) is None:
                setattr(listing, field, value)
        return listing
```

### 2.3 Test Cases

| Test | Input | Expected |
|------|-------|----------|
| `test_extract_floor` | "на 3-ти етаж от 6" | `{floor_number: 3, floor_total: 6}` |
| `test_extract_year` | "Построена 2020 г." | `{construction_year: 2020}` |
| `test_no_false_positives` | "Call 0888123456" | `{}` (phone not a floor) |
| `test_merge_priority` | structured=5, extracted=3 | floor=5 (structured wins) |

### 2.4 Optional: LLM Fallback

For complex descriptions where regex fails:

```python
async def llm_extract(description: str) -> dict:
    """Use Claude to extract fields. Cache results by description hash."""
    cache_key = hashlib.md5(description.encode()).hexdigest()
    if cached := await redis.get(f"desc_extract:{cache_key}"):
        return json.loads(cached)

    # Call Claude API with structured output
    result = await claude.extract_fields(description, SCHEMA)
    await redis.setex(f"desc_extract:{cache_key}", 86400, json.dumps(result))
    return result
```

**Decision**: Start with regex only. Add LLM if extraction accuracy < 70%.

---

## Phase 3: Change Detection & History Tracking ✅ COMPLETE

**Goal**: Track ALL changes to properties (not just price), maintain full history.

> **Status**: COMPLETE. Tables and functions implemented in `data/data_store_main.py` and `data/change_detector.py`.
>
> **Implemented**:
> - `scrape_history` table - tracks URL metadata (first_seen, last_seen, content_hash, status)
> - `listing_changes` table - tracks ALL field changes (listing_id, field_name, old/new values)
> - 7 CRUD functions (upsert_scrape_history, record_field_change, get_listing_changes, etc.)
> - `detect_all_changes()` function with SKIP_FIELDS for volatile field exclusion
> - 30 tests in `tests/test_change_detection.py` - 100% pass

### 3.1 New Database Tables

```sql
-- Track scrape metadata per URL
CREATE TABLE scrape_history (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    last_changed TEXT,
    scrape_count INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active'       -- active/removed/sold
);

-- Track ALL field changes over time
CREATE TABLE listing_changes (
    id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    field_name TEXT NOT NULL,          -- Which field changed
    old_value TEXT,                    -- Previous value (JSON for complex types)
    new_value TEXT,                    -- New value
    changed_at TEXT NOT NULL,
    source_site TEXT NOT NULL,         -- Which site reported this change
    UNIQUE(listing_id, field_name, changed_at)
);

CREATE INDEX idx_changes_listing ON listing_changes(listing_id);
CREATE INDEX idx_changes_field ON listing_changes(field_name);
CREATE INDEX idx_changes_date ON listing_changes(changed_at);
```

### 3.2 Change Detection Logic

```python
class ChangeDetector:
    """Detect and record ALL changes to listings."""

    def detect_changes(self, listing_id: int, old_data: dict, new_data: dict, source: str) -> list[dict]:
        """
        Compare old vs new data, return list of changes.
        Records changes to listing_changes table.
        """
        changes = []

        # Fields to track (all important fields)
        tracked_fields = [
            'price_eur', 'price_per_sqm_eur', 'sqm_total', 'sqm_net',
            'rooms_count', 'floor_number', 'floor_total', 'has_elevator',
            'building_type', 'act_status', 'condition', 'heating_type',
            'has_balcony', 'has_parking', 'has_storage', 'description'
        ]

        for field in tracked_fields:
            old_val = old_data.get(field)
            new_val = new_data.get(field)

            if old_val != new_val and new_val is not None:
                change = {
                    'listing_id': listing_id,
                    'field_name': field,
                    'old_value': json.dumps(old_val) if old_val else None,
                    'new_value': json.dumps(new_val),
                    'changed_at': datetime.utcnow().isoformat(),
                    'source_site': source
                }
                changes.append(change)
                self._record_change(change)

        return changes

    def get_history(self, listing_id: int, field: str = None) -> list[dict]:
        """
        Get change history for a listing.
        If field specified, only changes for that field.
        """
        query = "SELECT * FROM listing_changes WHERE listing_id = ?"
        params = [listing_id]

        if field:
            query += " AND field_name = ?"
            params.append(field)

        query += " ORDER BY changed_at DESC"
        return self._execute(query, params)

    def get_price_history(self, listing_id: int) -> list[dict]:
        """Convenience method for price changes."""
        return self.get_history(listing_id, 'price_eur')

    def should_scrape(self, url: str, current_hash: str) -> tuple[bool, str]:
        """
        Returns (should_scrape, reason).
        Reasons: 'new', 'changed', 'unchanged', 'stale'
        """
        history = self.get_scrape_history(url)

        if not history:
            return True, 'new'

        if history.content_hash != current_hash:
            return True, 'changed'

        # Even if unchanged, re-scrape if > 7 days old
        if history.last_seen < now() - timedelta(days=7):
            return True, 'stale'

        return False, 'unchanged'

    def detect_removed(self, site: str, active_urls: set[str]):
        """Mark URLs not in active_urls as removed."""
        known_urls = self.get_known_urls(site)
        removed = known_urls - active_urls
        for url in removed:
            self.mark_removed(url)
```

### 3.3 Dashboard: View Change History

```python
def get_listing_timeline(listing_id: int) -> list[dict]:
    """Get full timeline of changes for dashboard display."""
    changes = get_all_changes(listing_id)
    return [
        {
            'date': c['changed_at'],
            'field': c['field_name'],
            'from': json.loads(c['old_value']) if c['old_value'] else None,
            'to': json.loads(c['new_value']),
            'source': c['source_site']
        }
        for c in changes
    ]

# Example output:
# [
#   {'date': '2025-12-25', 'field': 'price_eur', 'from': 150000, 'to': 145000, 'source': 'imot.bg'},
#   {'date': '2025-12-24', 'field': 'has_parking', 'from': None, 'to': True, 'source': 'bazar.bg'},
#   {'date': '2025-12-20', 'field': 'price_eur', 'from': 160000, 'to': 150000, 'source': 'imot.bg'},
# ]
```

---

## Phase 3.5: Cross-Site Duplicate Detection & Smart Merging

**Goal**: Identify same property across sites, merge data to maximize info, track all sources.

### 3.5.1 Database Changes

```sql
-- Track which sites list each property
CREATE TABLE listing_sources (
    id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    source_site TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_external_id TEXT,           -- Site's ID for this listing
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    price_on_site REAL,                -- Price on THIS site (may differ!)
    UNIQUE(listing_id, source_site)
);

-- Add fingerprint column to listings for dedup matching
ALTER TABLE listings ADD COLUMN fingerprint TEXT;
ALTER TABLE listings ADD COLUMN is_merged BOOLEAN DEFAULT 0;

CREATE INDEX idx_sources_listing ON listing_sources(listing_id);
CREATE INDEX idx_sources_site ON listing_sources(source_site);
CREATE INDEX idx_listings_fingerprint ON listings(fingerprint);
```

### 3.5.2 Fingerprint Generation

```python
class PropertyFingerprinter:
    """Generate fingerprints to identify same property across sites."""

    def generate(self, listing: ListingData) -> str:
        """
        Create fingerprint from stable property attributes.
        NOT from price (changes) or source-specific data.
        """
        components = []

        # Location is most stable
        if listing.address:
            components.append(self._normalize_address(listing.address))
        if listing.neighborhood:
            components.append(listing.neighborhood.lower())

        # Physical attributes rarely change
        if listing.sqm_total:
            components.append(f"sqm:{int(listing.sqm_total)}")
        if listing.floor_number and listing.floor_total:
            components.append(f"floor:{listing.floor_number}/{listing.floor_total}")
        if listing.rooms_count:
            components.append(f"rooms:{listing.rooms_count}")

        # Agent phone is often unique to listing
        if listing.agent_phone:
            components.append(f"phone:{self._normalize_phone(listing.agent_phone)}")

        fingerprint_str = "|".join(sorted(components))
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def _normalize_address(self, addr: str) -> str:
        """Normalize address for matching."""
        addr = addr.lower()
        # Remove common variations
        addr = re.sub(r'\s+', ' ', addr)
        addr = re.sub(r'ул\.|улица|str\.|street', '', addr)
        addr = re.sub(r'бл\.|блок|block', 'bl', addr)
        return addr.strip()

    def _normalize_phone(self, phone: str) -> str:
        """Keep only digits."""
        return re.sub(r'\D', '', phone)[-9:]  # Last 9 digits
```

### 3.5.3 Smart Merge Strategy

```python
class PropertyMerger:
    """Merge data from multiple sites into single comprehensive record."""

    # Field priority: which source wins on conflict
    # Higher number = higher priority
    FIELD_PRIORITY = {
        # imot.bg often has best structured data
        'imot.bg': 3,
        'homes.bg': 2,
        'bazar.bg': 1,
    }

    def merge(self, existing: ListingData, new: ListingData) -> ListingData:
        """
        Merge new listing data into existing.

        Rules:
        1. If existing field is None → use new value
        2. If new field is None → keep existing
        3. If both have value → use higher priority source
        4. Always keep ALL source URLs
        """
        merged = existing

        for field in ListingData.__dataclass_fields__:
            existing_val = getattr(existing, field, None)
            new_val = getattr(new, field, None)

            if existing_val is None and new_val is not None:
                # Fill missing data
                setattr(merged, field, new_val)
            elif existing_val is not None and new_val is not None:
                # Both have value - check if we should update
                if self._should_prefer_new(field, existing, new):
                    # Record as change before updating
                    self._record_merge_change(existing.id, field, existing_val, new_val, new.source_site)
                    setattr(merged, field, new_val)

        merged.is_merged = True
        return merged

    def _should_prefer_new(self, field: str, existing: ListingData, new: ListingData) -> bool:
        """Decide if new value should override existing."""
        existing_priority = self.FIELD_PRIORITY.get(existing.source_site, 0)
        new_priority = self.FIELD_PRIORITY.get(new.source_site, 0)

        # Higher priority source wins
        return new_priority > existing_priority

    def track_price_discrepancy(self, listing_id: int, site: str, price: float):
        """
        Record when same property has different prices on different sites.
        This is VALUABLE info - shows negotiation room or listing staleness.
        """
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO listing_sources (listing_id, source_site, price_on_site, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(listing_id, source_site) DO UPDATE SET
                price_on_site = excluded.price_on_site,
                last_seen = excluded.last_seen
        """, (listing_id, site, price, datetime.utcnow().isoformat()))
        conn.commit()
```

### 3.5.4 Query: Where is Property Listed?

```python
def get_listing_sources(listing_id: int) -> list[dict]:
    """Get all sites where this property is listed."""
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT source_site, source_url, price_on_site, first_seen, last_seen, is_active
        FROM listing_sources
        WHERE listing_id = ?
        ORDER BY source_site
    """, (listing_id,))

    return [dict(row) for row in cursor.fetchall()]

# Example output:
# [
#   {'source_site': 'imot.bg', 'source_url': 'https://...', 'price_on_site': 150000, 'is_active': True},
#   {'source_site': 'bazar.bg', 'source_url': 'https://...', 'price_on_site': 148000, 'is_active': True},
# ]
# ^ Same property, €2000 cheaper on bazar.bg!
```

### 3.5.5 Dashboard: Cross-Site View

| Field | imot.bg | bazar.bg | homes.bg | Merged |
|-------|---------|----------|----------|--------|
| Price | €150,000 | €148,000 | - | €148,000 (lowest) |
| Floor | 3/6 | 3 | 3/6 | 3/6 |
| Parking | ✓ | - | ✓ | ✓ |
| Metro | 500m | - | near | 500m |

**Value**: User sees which site has best price + combined info from all sources.

---

## Phase 4: Rate Limiting & Async Orchestration 🔄 PARTIAL

**Goal**: Scrape multiple sites in parallel while respecting per-site limits.

> **Status**: PARTIAL.
>
> **Rate Limiter**: ✅ COMPLETE via Spec 112 Phase 2. Use `resilience/rate_limiter.py` (DomainRateLimiter with token bucket per domain). Config in `DOMAIN_RATE_LIMITS` in settings.py.
>
> **Orchestrator**: ❌ NOT STARTED. Still need async orchestrator for parallel site crawling.
>
> **Celery integration**: ❌ NOT STARTED.

### 4.1 Rate Limit Configuration

```yaml
# config/rate_limits.yaml
sites:
  imot.bg:
    requests_per_minute: 10
    requests_per_hour: 200
    concurrent_connections: 2
    delay_between_requests_ms: 6000
    daily_limit: 1000

  bazar.bg:
    requests_per_minute: 5
    requests_per_hour: 100
    concurrent_connections: 1
    delay_between_requests_ms: 12000
    daily_limit: 500

  homes.bg:
    requests_per_minute: 8
    requests_per_hour: 150
    concurrent_connections: 2
    delay_between_requests_ms: 7500
    daily_limit: 800
```

### 4.2 Rate Limiter Implementation

> ⚠️ **SUPERSEDED**: Do NOT implement this. Use `resilience/rate_limiter.py` (DomainRateLimiter) instead.
> The resilience rate limiter provides token bucket per domain with configurable rates.
> If Redis support is needed for distributed Celery workers, enhance the resilience rate limiter.

```python
# DEPRECATED - Use resilience/rate_limiter.py instead
# proxies/rate_limiter.py

class SiteRateLimiter:
    """Token bucket rate limiter per site using Redis."""

    def __init__(self, redis_client, config: dict):
        self.redis = redis_client
        self.config = config

    async def acquire(self, site: str) -> bool:
        """
        Try to acquire a request token for site.
        Returns True if allowed, False if rate limited.
        """
        key = f"ratelimit:{site}"
        config = self.config[site]

        # Check minute limit
        minute_key = f"{key}:minute:{int(time.time() / 60)}"
        minute_count = await self.redis.incr(minute_key)
        await self.redis.expire(minute_key, 120)

        if minute_count > config['requests_per_minute']:
            return False

        # Check hour limit
        hour_key = f"{key}:hour:{int(time.time() / 3600)}"
        hour_count = await self.redis.incr(hour_key)
        await self.redis.expire(hour_key, 7200)

        if hour_count > config['requests_per_hour']:
            return False

        return True

    async def wait_for_slot(self, site: str) -> None:
        """Block until a request slot is available."""
        while not await self.acquire(site):
            await asyncio.sleep(1)
```

### 4.3 Async Orchestrator

```python
# orchestrator_async.py

class AsyncCrawlOrchestrator:
    """Coordinate crawling across multiple sites."""

    def __init__(self, sites: list[str], rate_limiter: SiteRateLimiter):
        self.sites = sites
        self.rate_limiter = rate_limiter
        self.task_queue = asyncio.Queue()
        self.results = []

    async def run(self):
        """Main entry point."""
        # Start workers for each site
        workers = [
            asyncio.create_task(self.site_worker(site))
            for site in self.sites
        ]

        # Wait for all to complete
        await asyncio.gather(*workers)

        return self.results

    async def site_worker(self, site: str):
        """Worker for a single site."""
        scraper = get_scraper(site)
        page = 1

        while True:
            # Wait for rate limit slot
            await self.rate_limiter.wait_for_slot(site)

            # Get search page
            html = await self.fetch(scraper.get_search_url(page))
            urls = await scraper.extract_search_results(html)

            if not urls or scraper.is_last_page(html, page):
                break

            # Queue property URLs for processing
            for url in urls:
                await self.task_queue.put((site, url))

            page += 1

        logger.info(f"{site}: Finished pagination at page {page}")
```

### 4.4 Integration with Celery

```python
# Use Celery for distributed processing
@celery_app.task(bind=True, rate_limit='10/m')
def scrape_property(self, site: str, url: str):
    """Celery task with built-in rate limiting."""
    scraper = get_scraper(site)
    # ... scrape and save
```

---

## Phase 5: Full Pipeline Integration ❌ NOT STARTED

**Goal**: Connect all components into working pipeline.

> **Status**: NOT STARTED. Depends on Phase 4 orchestrator completion.

### 5.1 Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        Orchestrator                               │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ For each site (parallel):                                   │ │
│  │                                                             │ │
│  │   1. Rate Limiter → check slot available                   │ │
│  │   2. Fetch search page → via proxy (mubeng)                │ │
│  │   3. Extract listing URLs                                   │ │
│  │   4. For each URL:                                          │ │
│  │      a. Change Detector → skip if unchanged                │ │
│  │      b. Fetch property page                                │ │
│  │      c. Scraper → extract raw data                         │ │
│  │      d. Description Extractor → enrich                     │ │
│  │      e. Field Normalizer → canonical schema                │ │
│  │      f. Validator → check required fields                  │ │
│  │      g. Database → save (upsert)                           │ │
│  │      h. Update scrape_history                               │ │
│  │   5. Check pagination → next page or done                  │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Component Dependency Order

```
1. Scrapers (per site) ─────────┐
2. Description Extractor ───────┼──→ 5. Orchestrator ──→ 6. Monitoring
3. Change Detector ─────────────┤
4. Rate Limiter ────────────────┘
```

### 5.3 Test Strategy

| Test Level | What it tests | How |
|------------|---------------|-----|
| Unit | Each component in isolation | pytest with mocks |
| Integration | Components work together | pytest with fixtures |
| E2E | Full pipeline with real sites | Manual + limited runs |
| Stress | Rate limiting, concurrency | Synthetic load |

---

## Implementation Order (Prioritized)

### Week 1: Validation & Testing

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Create test harness | `tests/scrapers/` structure |
| 2-3 | Test imot.bg scraper | All tests passing |
| 3-4 | Test bazar.bg scraper | Fix any issues found |
| 4-5 | Create validation matrix | Document what works |

### Week 2: Enhancement

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Build description extractor | `websites/description_extractor.py` |
| 2-3 | Test extraction accuracy | > 70% on test set |
| 3-4 | Build change detector | `scrape_history` table + class |
| 4-5 | Integrate into scraper flow | Working change detection |

### Week 3: Orchestration

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Build rate limiter | Redis-backed limiter |
| 2-3 | Build async orchestrator | Parallel site crawling |
| 3-4 | Integrate with Celery | Distributed processing |
| 4-5 | E2E testing | Full pipeline working |

### Week 4: Polish

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Add homes.bg scraper | Third site working |
| 2-3 | Add monitoring/alerting | Dashboards, alerts |
| 3-4 | Documentation | Runbooks, troubleshooting |
| 4-5 | Production deploy | Running in production |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Site structure changes | Scraper breaks | Monitor extraction success rate, alert on drops |
| IP blocking | Can't scrape | Proxy rotation (already have mubeng) |
| Rate limit too aggressive | Miss data | Start conservative, tune up gradually |
| Description extraction low accuracy | Missing data | LLM fallback, manual review for high-value |
| Database performance | Slow queries | Indexes already in place, monitor |

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Scraper test coverage | > 90% |
| Field extraction rate | > 80% of available fields |
| Description extraction accuracy | > 70% |
| Redundant scrapes avoided | > 50% reduction |
| Rate limit compliance | 0 blocks |
| Pipeline uptime | > 99% |

---

## Questions to Resolve

1. **LLM for descriptions?** Cost vs accuracy tradeoff - test regex first
2. **How often to re-scrape unchanged?** 7 days proposed - confirm
3. **Price change alert threshold?** 5%? 10%? Any change?
4. **homes.bg priority?** Before or after orchestration?

---

## Appendix: Existing Code Reference

| Component | Location | Status |
|-----------|----------|--------|
| Base scraper | `websites/base_scraper.py` | Complete |
| ListingData schema | `websites/base_scraper.py:17-91` | Complete |
| imot.bg scraper | `websites/imot_bg/imot_scraper.py` | Complete |
| bazar.bg scraper | `websites/bazar_bg/bazar_scraper.py` | Needs verification |
| Database | `data/data_store_main.py` | Complete |
| Celery | `celery_app.py` | Complete |
| Proxy system | `proxies/` | Complete |
