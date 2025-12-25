---
id: 20251201_error_handling_scraper
type: extraction
subject: error_handling
source_repo: Scraper
description: "Retry decorator, cooldown manager, rate limiting patterns"
created_at: 2025-12-01
updated_at: 2025-12-01
tags: [extraction, error_handling, retry, cooldown, rate-limit]
---

# SUBJECT: error_handling/

**Source**: `idkny/Scraper`
**Files Extracted**: 2 files
**Quality**: GOOD - Clean implementations

---

## 1. Async Retry Decorator (retry_decorator.py)

Exponential backoff with jitter for async functions.

```python
import asyncio
import functools
import random
import time

def retry_async(max_attempts=3, base_delay=1.0, max_delay=10.0, exceptions=(Exception,)):
    """
    Async retry decorator with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exceptions to catch and retry

    Usage:
        @retry_async(max_attempts=5, base_delay=2.0)
        async def my_flaky_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    # Exponential backoff: base * 2^(attempt-1) + random jitter
                    delay = min(base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1), max_delay)
                    print(f"[retry_async] Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
```

---

## 2. Cooldown Manager (cooldown_tracker.py)

Per-strategy cooldown tracking for rate limiting.

```python
import time

class CooldownManager:
    """
    Tracks cooldown periods per strategy.
    Used to temporarily disable strategies that have failed.

    Usage:
        cooldown = CooldownManager("bazar")

        if cooldown.is_in_cooldown("playwright"):
            skip_strategy()
        else:
            try:
                result = scrape()
                if result.success:
                    cooldown.reset("playwright")
                else:
                    cooldown.bump("playwright")  # 5 min cooldown
            except:
                cooldown.bump("playwright", cooldown_time=600)  # 10 min for errors
    """

    def __init__(self, site_name):
        self.site_name = site_name
        self.cooldowns = {}

    def is_in_cooldown(self, strategy: str) -> bool:
        """Check if strategy is currently in cooldown."""
        now = time.time()
        expire = self.cooldowns.get(strategy, 0)
        return now < expire

    def bump(self, strategy: str, cooldown_time: int = 300):
        """Put strategy in cooldown for specified seconds (default 5 min)."""
        self.cooldowns[strategy] = time.time() + cooldown_time

    def reset(self, strategy: str):
        """Remove strategy from cooldown (on success)."""
        self.cooldowns.pop(strategy, None)
```

---

## 3. URL Safety Checker (url_safety_checker.py) - Security Pattern

Sync and async URL validation against malware databases.

```python
import requests
import hashlib
import json
import time
import asyncio
import aiohttp
from functools import lru_cache
from urllib.parse import urlparse

# CONFIGURATION
GOOGLE_API_KEY = "your_google_api_key"
VT_API_KEY = "your_virustotal_api_key"

# CACHE - in-memory set of known unsafe domains
unsafe_domains = set()

@lru_cache(maxsize=5000)
def is_url_cached_safe(domain_hash: str) -> bool:
    """Check if domain hash is in unsafe cache."""
    return domain_hash not in unsafe_domains


# GOOGLE SAFE BROWSING (Sync)
def is_url_safe_google(url: str, api_key: str) -> bool:
    """Check URL against Google Safe Browsing API."""
    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    body = {
        "client": {"clientId": "scraper", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    resp = requests.post(endpoint, json=body)
    matches = resp.json().get("matches", [])
    return len(matches) == 0


# VIRUSTOTAL (Sync)
def is_url_safe_virustotal(url: str, api_key: str) -> bool:
    """Check URL against VirusTotal API."""
    headers = {"x-apikey": api_key}
    post_resp = requests.post(
        "https://www.virustotal.com/api/v3/urls",
        headers=headers,
        data={"url": url},
    )
    url_id = post_resp.json()["data"]["id"]
    time.sleep(1.5)  # VirusTotal rate limit
    get_resp = requests.get(
        f"https://www.virustotal.com/api/v3/analyses/{url_id}", headers=headers
    )
    stats = get_resp.json()["data"]["attributes"]["stats"]
    return stats.get("malicious", 0) == 0


# MAIN (Sync)
def is_url_safe(url: str) -> bool:
    """Check URL safety against multiple services."""
    domain = urlparse(url).netloc
    domain_hash = hashlib.md5(domain.encode()).hexdigest()

    if is_url_cached_safe(domain_hash):
        return True

    try:
        safe_google = is_url_safe_google(url, GOOGLE_API_KEY)
        safe_vt = is_url_safe_virustotal(url, VT_API_KEY)
        safe = safe_google and safe_vt
    except Exception as e:
        print(f"[WARN] Safety check failed for {url}: {e}")
        safe = False

    if not safe:
        unsafe_domains.add(domain_hash)
    return safe


# ASYNC VERSION
async def is_url_safe_async(url: str) -> bool:
    """Async version of URL safety check."""
    domain = urlparse(url).netloc
    domain_hash = hashlib.md5(domain.encode()).hexdigest()

    if is_url_cached_safe(domain_hash):
        return True

    try:
        async with aiohttp.ClientSession() as session:
            safe_google = await is_url_safe_google_async(session, url)
            safe_vt = await is_url_safe_virustotal_async(session, url)
            safe = safe_google and safe_vt
    except Exception as e:
        print(f"[WARN] Async safety check failed for {url}: {e}")
        safe = False

    if not safe:
        unsafe_domains.add(domain_hash)
    return safe


# Optional: heuristic check for suspicious TLDs
def is_url_suspicious(url: str) -> bool:
    """Quick heuristic check for suspicious URL patterns."""
    netloc = urlparse(url).netloc
    return any(
        netloc.endswith(ext) for ext in [".ru", ".su", ".kp", ".top", ".xyz"]
    ) or netloc.replace(".", "").isdigit()
```

---

## CONCLUSIONS

### What is GOOD / Usable (Direct Port)

1. **retry_async Decorator**
   - Exponential backoff formula: `base * 2^(attempt-1)`
   - Jitter: `+ random.uniform(0, 1)`
   - Max delay cap
   - Configurable exception types
   - Clean decorator pattern

2. **CooldownManager**
   - Simple, effective rate limiting
   - Per-strategy tracking
   - Easy bump/reset API

3. **URL Safety Checker**
   - Multi-service validation (Google + VirusTotal)
   - LRU cache for performance
   - Both sync and async versions
   - Suspicious TLD heuristic

### What is OUTDATED

- Print statements instead of logging
- Hardcoded API keys (should be config)
- MD5 for domain hashing (could use SHA256)

### What Must Be REWRITTEN

1. **Add logging** - Replace print with proper logging
2. **Config integration** - Move API keys to config
3. **Persistence** - CooldownManager should persist across restarts
4. **Add sync retry** - retry_async is async-only, need sync version

### Cross-Repo Comparison

| Feature | Scraper | MarketIntel | SerpApi | Best |
|---------|---------|-------------|---------|------|
| Async retry | ✅ Clean | ✅ More params | ❌ Basic | MarketIntel (more features) |
| Cooldown | ✅ Per-strategy | ❌ None | ❌ None | **SCRAPER** |
| URL Safety | ✅ Complete | ❌ None | ❌ None | **SCRAPER** |

**MERGE RECOMMENDATION**: Combine MarketIntel's retry (more params, sync+async) with Scraper's cooldown

### How It Fits Into AutoBiz

**Location**: `autobiz/core/error_handling/`
- `retry.py` - Retry decorators (sync + async)
- `cooldown.py` - CooldownManager
- `url_safety.py` - URL validation (optional security module)

**Integration Points**:
- All API clients use retry decorators
- Scraper uses cooldown for strategy rotation
- URL safety for user-submitted URLs

---

## Usage Examples

```python
# Retry decorator
@retry_async(max_attempts=5, base_delay=2.0, exceptions=(ConnectionError, TimeoutError))
async def fetch_api_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

# Cooldown manager
cooldown = CooldownManager("target_site")

for strategy in ["api", "pycurl", "playwright"]:
    if cooldown.is_in_cooldown(strategy):
        continue
    try:
        result = await scrape(strategy)
        cooldown.reset(strategy)
        break
    except RateLimitError:
        cooldown.bump(strategy, cooldown_time=600)  # 10 min

# URL safety
if is_url_suspicious(user_url):
    print("URL flagged as suspicious")
elif not await is_url_safe_async(user_url):
    print("URL blocked by safety check")
else:
    proceed_with_scraping(user_url)
```
