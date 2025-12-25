---
id: 20251201_scraper_scraper
type: extraction
subject: scraper
source_repo: Scraper
description: "Website scraping framework - manager, strategies, site configs"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, scraper, website, strategy-pattern, config]
---

# SUBJECT: scraper/

**Source**: `idkny/Scraper`
**Files Extracted**: 4 files
**Quality**: GOOD - Reusable patterns (but some stubs)

---

## 1. WebsiteManager (website.py)

Base class for site scraping with strategy pattern.

```python
# Scraper/website.py
import importlib
import json
import time
from pathlib import Path
from utils.sqlite_handler import SQLiteHandler

class WebsiteManager:
    """
    Manages scraping for a specific website.
    - Loads site-specific module dynamically
    - Executes strategies with proxy/fingerprint
    - Persists data to SQLite
    - Writes logs in JSONL format
    """

    def __init__(self, site_name, config):
        self.site_name = site_name
        self.config = config
        self.site_module = self.load_module(site_name)
        self.data = []
        self.sqlite = SQLiteHandler(site_name)
        self.logs = []

    def load_module(self, name):
        """Dynamically load site-specific scraper module."""
        return importlib.import_module(f"Website.{name}")

    async def scrape(self, strategy, proxy, fingerprint):
        """
        Execute scraping with given strategy.
        Returns result object with success flag.
        """
        try:
            result = await self.site_module.start_scrape(
                config=self.config,
                proxy=proxy,
                fingerprint=fingerprint,
                strategy=strategy
            )
            self.data.extend(result.data)
            self.logs.append(result.log)
            return result
        except Exception as e:
            self.logs.append({
                "strategy": strategy,
                "error": str(e),
                "timestamp": time.time()
            })
            return type("FailResult", (), {"success": False})

    def persist_data(self):
        """Save scraped data to SQLite."""
        self.sqlite.write_records(self.data)

    def write_logs(self):
        """Append logs to JSONL file."""
        log_path = Path(f"logs/scrape_log_{self.site_name}.jsonl")
        log_path.parent.mkdir(exist_ok=True)
        with log_path.open("a") as f:
            for entry in self.logs:
                f.write(json.dumps(entry) + "\n")
```

---

## 2. Site-Specific Scraper (bazar.py)

Example site scraper with multi-strategy support.

```python
# Website/bazar.py
import asyncio
from Scraper.methods.pcurl_scraper import scrape_with_pycurl
from Scraper.methods.playwright_scraper import scrape_with_playwright
from Scraper.methods.camoufox_scraper import scrape_with_camoufox

async def start_scrape(config, proxy, fingerprint, strategy):
    """
    Main interface to run the scraper. Strategy could be one of:
    "api", "pycurl", "playwright_stealth", "camoufox"
    """
    urls = config["start_urls"]
    extracted = []

    if strategy == "api":
        # hypothetical: just fetch data
        return await some_api_scraper(config)

    elif strategy == "pycurl":
        extracted = await scrape_with_pycurl(urls, config, proxy)

    elif strategy == "playwright_stealth":
        extracted = await scrape_with_playwright(urls, config, proxy, fingerprint)

    elif strategy == "camoufox":
        extracted = await scrape_with_camoufox(urls, config, proxy, fingerprint)

    standardized = [standardize_item(item) for item in extracted]
    return type("ScrapeResult", (), {
        "data": standardized,
        "log": {"strategy": strategy, "page_count": len(urls), "success": True},
        "success": True
    })


def standardize_item(item):
    """Normalize scraped item to common schema."""
    return {
        "title": item.get("title"),
        "price": item.get("price"),
        "url": item.get("url"),
        "location": item.get("location"),
        "date_posted": item.get("date_posted")
    }
```

---

## 3. Site Configuration (bazar.json)

JSON configuration for site-specific selectors and strategies.

```json
{
  "start_urls": ["https://bazar.bg/nedvizhimi-imoti"],
  "filters": {
    "rooms": "input[name='rooms']",
    "price_min": "#price-min",
    "price_max": "#price-max"
  },
  "pagination_selector": ".pagination .next",
  "listing_selector": ".list__item",
  "detail_selectors": {
    "title": "h1.ad__title",
    "price": ".ad__price",
    "location": ".ad__location",
    "date_posted": ".ad__date",
    "description": ".ad__description"
  },
  "scraping_strategies": ["pycurl", "playwright_stealth", "camoufox"],
  "preferred_proxies": ["BG", "EU"],
  "timeout_cooldown": 300,
  "referrer": "https://bazar.bg"
}
```

---

## 4. Main Entry Point (main.py)

CLI entry point with strategy fallback.

```python
# main.py
import argparse
import asyncio
import sys

from utils.cooldown_tracker import CooldownManager
from utils.config_loader import load_site_configs
from utils.fingerprint_manager import get_fingerprint
from Websites_to_Scrape.website import WebsiteManager
from Fingerprint.fingerprints import main as fingerprint_cli_entry


async def scrape_site(site_name: str):
    """
    Scrape a site with automatic strategy fallback.
    Tries each strategy in order, skipping those in cooldown.
    """
    config = load_site_configs(site_name)
    manager = WebsiteManager(site_name, config)
    cooldown = CooldownManager(site_name)

    for strategy in config["scraping_strategies"]:
        if cooldown.is_in_cooldown(strategy):
            continue

        proxy = None  # Set via ProxyService, if needed
        fingerprint = get_fingerprint(strategy, config)

        result = await manager.scrape(
            strategy=strategy,
            proxy=proxy,
            fingerprint=fingerprint
        )

        if result.success:
            cooldown.reset(strategy)
            break
        else:
            cooldown.bump(strategy)
            continue

    manager.persist_data()
    manager.write_logs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main Project Entry")
    parser.add_argument("module", help="Module to run: site or fingerprints")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the selected module")
    args = parser.parse_args()

    if args.module == "site":
        if not args.args:
            print("Missing site name. Example: python main.py site bazar")
            sys.exit(1)
        asyncio.run(scrape_site(args.args[0]))

    elif args.module == "fingerprints":
        # Proxy & fingerprint CLI delegation
        sys.argv = [sys.argv[0]] + args.args
        fingerprint_cli_entry()

    else:
        print(f"Unknown module '{args.module}'. Use 'site' or 'fingerprints'.")
```

---

## CONCLUSIONS

### What is GOOD / Usable (Direct Port)

1. **WebsiteManager Pattern**
   - Dynamic module loading via importlib
   - Strategy fallback with cooldown
   - Clean separation of scraping logic

2. **Site Configuration Schema**
   - Selectors (listing, pagination, detail)
   - Multiple strategies per site
   - Proxy preferences by country
   - Cooldown settings

3. **Standardization Pattern**
   - Common output schema for all scrapers
   - Easy to extend for new fields

4. **JSONL Logging**
   - Append-only log format
   - Per-site log files

### What is OUTDATED

- Missing scraper method files (`pcurl_scraper.py`, `playwright_scraper.py`, `camoufox_scraper.py`)
- `type("FailResult", ...)` pattern - should use dataclass/Pydantic
- Hardcoded paths for logs

### What Must Be REWRITTEN

1. **Replace dynamic type creation** - Use Pydantic models for ScrapeResult
2. **Add missing scraper methods** - Implement pycurl, playwright, camoufox scrapers
3. **Config path** - Use centralized config system
4. **Add retry decorator** - Wrap scrape method
5. **Add data validation** - Validate scraped items before persist

### How It Fits Into AutoBiz

**Location**: `autobiz/tools/scraper/`
- `website_manager.py` - Base manager class
- `site_configs/` - Site JSON configurations
- `methods/` - Scraper implementations (pycurl, playwright, etc.)
- `models.py` - ScrapeResult, ScrapedItem Pydantic models

**Integration Points**:
- Uses `autobiz/tools/browser/` for Playwright/Camoufox
- Uses `autobiz/tools/proxies/` for proxy rotation
- Persists to `autobiz/tools/data/` SQLite layer

### Conflicts/Duplicates

- **No direct conflicts** - First scraper framework
- MarketIntel has simpler API-only scraping
- SerpApi is specification only

### Best Version

**SCRAPER is the ONLY version** - Needs completion but patterns are solid

---

## Usage Example

```bash
# Scrape a site with automatic strategy fallback
python main.py site bazar

# Run fingerprint CLI
python main.py fingerprints --check
```

```python
# Programmatic usage
from Websites_to_Scrape.website import WebsiteManager
from utils.config_loader import load_site_configs

config = load_site_configs("bazar")
manager = WebsiteManager("bazar", config)

result = await manager.scrape(
    strategy="playwright_stealth",
    proxy="http://proxy:8080",
    fingerprint={"user_agent": "..."}
)

if result.success:
    manager.persist_data()
```
