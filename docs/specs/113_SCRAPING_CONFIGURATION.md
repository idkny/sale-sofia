# Spec 113: Scraping Configuration System

**Status**: Phase 4.1 Complete (config created, tests passing)
**Created**: 2025-12-27
**Phase**: 4.1 (Scraping Settings Configuration)

---

## Overview

Create a 2-level configuration system for scraping: global defaults + per-site overrides. Based on proven settings from Scrapy, Colly, and Crawlee.

**Goals**:
1. Single source of truth for scraping settings
2. Clear separation: global defaults vs site-specific overrides
3. Type-safe configuration with dataclasses
4. Clean merge logic: defaults <- site overrides

---

## Research Summary

**Sources**: Scrapy (Python), Colly (Go), Crawlee (Node.js)

| Setting | Scrapy Default | Industry Best Practice |
|---------|----------------|------------------------|
| Concurrent requests (global) | 16 | 8-16 |
| Concurrent per domain | 8 | 1-2 (polite) |
| Download delay | 0 | 2-3 seconds |
| Randomize delay | 0.5x-1.5x | Yes |
| Request timeout | 180s | 30-60s |
| Retry attempts | 2 | 2-3 |
| Retry HTTP codes | 500,502,503,504,522,524,408,429 | Same |

---

## Configuration Structure

### File Layout

```
config/
├── scraping_defaults.yaml    # Global defaults (NEW)
├── sites/                    # Per-site overrides (NEW)
│   ├── imot_bg.yaml
│   └── bazar_bg.yaml
├── scraping_config.py        # Loader + dataclass (NEW)
├── start_urls.yaml           # URLs only (SIMPLIFIED)
├── settings.py               # Other settings (CLEANUP)
├── loader.py                 # URL loader (KEEP)
└── __init__.py               # Package init (CLEANUP)
```

### Global Defaults: `config/scraping_defaults.yaml`

```yaml
# Scraping Configuration Defaults
# Based on Scrapy, Colly, Crawlee best practices
# Override per-site in config/sites/<site>.yaml

# --- Concurrency ---
concurrency:
  max_global: 16              # Max total concurrent requests
  max_per_domain: 2           # Max per domain (conservative)

# --- Timing ---
timing:
  delay_seconds: 2.0          # Base delay between requests
  randomize_delay: true       # Add 0.5x-1.5x randomization
  random_delay_min: 0.5       # Multiplier min (delay * 0.5)
  random_delay_max: 1.5       # Multiplier max (delay * 1.5)

# --- Timeouts ---
timeouts:
  request_seconds: 60         # HTTP request timeout
  page_load_seconds: 30       # Browser page load timeout
  navigation_seconds: 30      # Browser navigation timeout

# --- Retry ---
retry:
  max_attempts: 3             # Total attempts (1 initial + 2 retries)
  backoff_base: 1.0           # Initial backoff delay
  backoff_max: 300.0          # Max backoff (5 minutes)
  backoff_multiplier: 2.0     # Exponential multiplier
  http_codes:                 # Codes that trigger retry
    - 429                     # Too Many Requests
    - 500                     # Internal Server Error
    - 502                     # Bad Gateway
    - 503                     # Service Unavailable
    - 504                     # Gateway Timeout
    - 522                     # Cloudflare timeout
    - 524                     # Cloudflare timeout

# --- Fetcher Selection ---
fetcher:
  search_pages: http          # http | browser | stealth
  listing_pages: http         # http | browser | stealth

# --- Anti-Detection ---
anti_detection:
  rotate_user_agent: true     # Rotate UA per request
  block_webrtc: false         # Block WebRTC (browser only)
  humanize_actions: false     # Random mouse/scroll (browser only)

# --- Behavior ---
behavior:
  respect_robots_txt: true    # Honor robots.txt
  follow_crawl_delay: true    # Honor Crawl-Delay directive
  cookies_enabled: true       # Enable cookie handling
```

### Per-Site Override: `config/sites/imot_bg.yaml`

```yaml
# imot.bg - Less aggressive anti-bot
# Override only what differs from defaults

timing:
  delay_seconds: 1.5          # Faster OK for this site

concurrency:
  max_per_domain: 3           # Can handle more

fetcher:
  search_pages: http
  listing_pages: http
```

### Per-Site Override: `config/sites/bazar_bg.yaml`

```yaml
# bazar.bg - Has anti-bot protection
# More conservative settings

timing:
  delay_seconds: 3.0          # Slower to avoid detection

concurrency:
  max_per_domain: 1           # Single request at a time

fetcher:
  search_pages: stealth       # Use stealth browser
  listing_pages: http         # Regular HTTP OK for listings

anti_detection:
  rotate_user_agent: true
  humanize_actions: true      # More human-like
```

---

## Implementation

### Dataclass: `config/scraping_config.py`

```python
"""
Scraping configuration loader with merge logic.

Usage:
    from config.scraping_config import load_scraping_config

    config = load_scraping_config("imot.bg")
    print(config.timing.delay_seconds)  # 1.5 (site override)
    print(config.retry.max_attempts)    # 3 (from defaults)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class ConcurrencyConfig:
    max_global: int = 16
    max_per_domain: int = 2


@dataclass
class TimingConfig:
    delay_seconds: float = 2.0
    randomize_delay: bool = True
    random_delay_min: float = 0.5
    random_delay_max: float = 1.5


@dataclass
class TimeoutConfig:
    request_seconds: int = 60
    page_load_seconds: int = 30
    navigation_seconds: int = 30


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 300.0
    backoff_multiplier: float = 2.0
    http_codes: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504, 522, 524]
    )


@dataclass
class FetcherConfig:
    search_pages: str = "http"    # http | browser | stealth
    listing_pages: str = "http"


@dataclass
class AntiDetectionConfig:
    rotate_user_agent: bool = True
    block_webrtc: bool = False
    humanize_actions: bool = False


@dataclass
class BehaviorConfig:
    respect_robots_txt: bool = True
    follow_crawl_delay: bool = True
    cookies_enabled: bool = True


@dataclass
class ScrapingConfig:
    """Complete scraping configuration for a site."""
    site: str
    concurrency: ConcurrencyConfig = field(default_factory=ConcurrencyConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    anti_detection: AntiDetectionConfig = field(default_factory=AntiDetectionConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _normalize_site_name(site: str) -> str:
    """Convert site name to filename format: imot.bg -> imot_bg"""
    return site.replace(".", "_").replace("-", "_")


def load_scraping_config(site: str) -> ScrapingConfig:
    """
    Load scraping configuration with merge logic.

    Merge order: defaults <- site overrides

    Args:
        site: Site name (e.g., "imot.bg")

    Returns:
        ScrapingConfig with merged settings
    """
    config_dir = Path(__file__).parent

    # Load defaults
    defaults_path = config_dir / "scraping_defaults.yaml"
    if defaults_path.exists():
        with open(defaults_path, "r") as f:
            defaults = yaml.safe_load(f) or {}
    else:
        defaults = {}

    # Load site overrides
    site_filename = _normalize_site_name(site) + ".yaml"
    site_path = config_dir / "sites" / site_filename
    if site_path.exists():
        with open(site_path, "r") as f:
            site_config = yaml.safe_load(f) or {}
    else:
        site_config = {}

    # Merge: defaults <- site
    merged = _deep_merge(defaults, site_config)

    # Build dataclass
    return ScrapingConfig(
        site=site,
        concurrency=ConcurrencyConfig(**merged.get("concurrency", {})),
        timing=TimingConfig(**merged.get("timing", {})),
        timeouts=TimeoutConfig(**merged.get("timeouts", {})),
        retry=RetryConfig(**merged.get("retry", {})),
        fetcher=FetcherConfig(**merged.get("fetcher", {})),
        anti_detection=AntiDetectionConfig(**merged.get("anti_detection", {})),
        behavior=BehaviorConfig(**merged.get("behavior", {})),
    )
```

---

## Cleanup Tasks

### 1. Remove Dead Code: `config/__init__.py`

**Current** (line 4-8):
```python
SCRAPER_CONFIG = {
    "request_delay": 2,
    "timeout": 30,
    "max_retries": 3,
}
```

**Action**: Delete entire `SCRAPER_CONFIG` dict (never used).

### 2. Remove from `config/settings.py`

**Current** (line 134):
```python
DEFAULT_SCRAPE_DELAY = 6.0  # Default delay between requests (seconds)
```

**Action**: Delete - now in `scraping_defaults.yaml`.

### 3. Simplify `config/start_urls.yaml`

**Current**: Mixes URLs and config together.

**After**: URLs only (config moves to `config/sites/`):
```yaml
# Start URLs for automated crawling
# Site-specific config in config/sites/<site>.yaml

imot.bg:
  - https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/tristaen/?priceBuy_min=200000&priceBuy_max=270000
  - https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/chetiristaen/?priceBuy_min=200000&priceBuy_max=270000
  - https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/mnogostaen/?priceBuy_min=200000&priceBuy_max=270000

bazar.bg:
  - https://bazar.bg/obiavi/apartamenti/tristaini/sofia
  - https://bazar.bg/obiavi/apartamenti/chetiristaini/sofia
  - https://bazar.bg/obiavi/apartamenti/mnogostaini/sofia
```

### 4. Update `config/loader.py`

- Remove `SiteConfig` class (replaced by `ScrapingConfig`)
- Remove `get_site_config()` function (replaced by `load_scraping_config`)
- Remove import of `DEFAULT_SCRAPE_DELAY`
- Keep `get_start_urls()` function (still needed)
- Keep `get_implemented_sites()` function

### 5. Update `main.py`

- Replace `DEFAULT_SCRAPE_DELAY` import with `load_scraping_config`
- Update `scrape_from_start_url()` to use `ScrapingConfig`

---

## Migration Plan

1. Create `config/scraping_defaults.yaml`
2. Create `config/sites/` directory
3. Create `config/sites/imot_bg.yaml`
4. Create `config/sites/bazar_bg.yaml`
5. Create `config/scraping_config.py`
6. Write unit tests for config loading/merging
7. Update `main.py` to use new config
8. Clean up old code:
   - Delete `SCRAPER_CONFIG` from `config/__init__.py`
   - Delete `DEFAULT_SCRAPE_DELAY` from `config/settings.py`
   - Delete `SiteConfig` and `get_site_config` from `config/loader.py`
   - Simplify `config/start_urls.yaml`

---

## Testing

### Unit Tests: `tests/test_scraping_config.py`

```python
def test_load_defaults_only():
    """Config loads correctly when no site override exists."""
    config = load_scraping_config("unknown.com")
    assert config.timing.delay_seconds == 2.0
    assert config.concurrency.max_per_domain == 2

def test_site_override_merges():
    """Site override merges with defaults."""
    config = load_scraping_config("imot.bg")
    assert config.timing.delay_seconds == 1.5  # Override
    assert config.retry.max_attempts == 3      # Default

def test_deep_merge_nested():
    """Nested dicts merge correctly."""
    config = load_scraping_config("bazar.bg")
    assert config.fetcher.search_pages == "stealth"  # Override
    assert config.fetcher.listing_pages == "http"    # Override

def test_normalize_site_name():
    """Site names convert to filenames."""
    assert _normalize_site_name("imot.bg") == "imot_bg"
    assert _normalize_site_name("my-site.com") == "my_site_com"
```

---

## Acceptance Criteria

- [ ] `config/scraping_defaults.yaml` exists with all settings
- [ ] `config/sites/imot_bg.yaml` exists with site-specific overrides
- [ ] `config/sites/bazar_bg.yaml` exists with site-specific overrides
- [ ] `config/scraping_config.py` loads and merges configs correctly
- [ ] All unit tests pass
- [ ] `SCRAPER_CONFIG` removed from `config/__init__.py`
- [ ] `DEFAULT_SCRAPE_DELAY` removed from `config/settings.py`
- [ ] `SiteConfig` removed from `config/loader.py`
- [ ] `main.py` uses new `load_scraping_config()`
- [ ] No hardcoded scraping values in codebase

---

## References

- Scrapy Settings: https://docs.scrapy.org/en/latest/topics/settings.html
- Scrapy AutoThrottle: https://docs.scrapy.org/en/latest/topics/autothrottle.html
- Colly Configuration: https://go-colly.org/docs/introduction/configuration/
- Crawlee Configuration: https://crawlee.dev/js/api/core/interface/ConfigurationOptions
