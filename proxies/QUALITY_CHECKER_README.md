# Proxy Quality Checker

A comprehensive proxy quality validation system that tests proxies against Google (captcha detection) and target sites (e.g., imot.bg).

## Overview

The Quality Checker complements the basic proxy validator by performing more sophisticated checks:

1. **Google Captcha Detection** - Identifies when Google blocks proxy traffic
2. **Target Site Validation** - Ensures proxies work with actual scraping targets
3. **Combined Quality Metrics** - Provides comprehensive proxy quality assessment

## Features

- Detects Google captcha pages (unusual traffic warnings)
- Validates proxy functionality with imot.bg
- Supports custom target site validation
- Batch processing for multiple proxies
- Proper timeout and error handling
- Uses httpx for modern async-capable requests

## Installation

The quality checker requires `httpx`:

```bash
pip install httpx>=0.28.1
```

This is already included in `requirements.txt`.

## Quick Start

### Basic Usage

```python
from proxies.quality_checker import QualityChecker

checker = QualityChecker(timeout=15)

# Check individual aspects
google_ok = checker.check_google("http://1.2.3.4:8080")
target_ok = checker.check_target_site("http://1.2.3.4:8080")

# Combined check
results = checker.check_all("http://1.2.3.4:8080")
# Returns: {"google_passed": bool, "target_passed": bool}
```

### Enrich Proxy Dictionary

```python
from proxies.quality_checker import enrich_proxy_with_quality

proxy = {
    "host": "1.2.3.4",
    "port": 8080,
    "protocol": "http",
}

enriched = enrich_proxy_with_quality(proxy, timeout=15)
# Adds: google_passed, target_passed, quality_checked_at
```

### Batch Processing

```python
from proxies.quality_checker import enrich_proxies_batch

proxies = [
    {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
    {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
]

enriched = enrich_proxies_batch(proxies, timeout=10)

# Filter for high-quality proxies
premium = [
    p for p in enriched
    if p["google_passed"] and p["target_passed"]
]
```

## API Reference

### QualityChecker Class

#### `__init__(self, timeout: int = 15)`

Initialize the quality checker.

**Parameters:**
- `timeout` (int): Request timeout in seconds (default: 15)

#### `check_google(self, proxy_url: str) -> bool`

Test proxy against Google and detect captcha.

**Parameters:**
- `proxy_url` (str): Full proxy URL (e.g., "http://1.2.3.4:8080")

**Returns:**
- `bool`: True if proxy works with Google (no captcha), False otherwise

**Captcha Indicators Detected:**
- "captcha"
- "unusual traffic"
- "i'm not a robot"
- "recaptcha"
- "automated queries"
- "/sorry/" (Google's captcha URL path)

#### `check_target_site(self, proxy_url: str, target_url: str = "https://www.imot.bg") -> bool`

Test proxy against target site.

**Parameters:**
- `proxy_url` (str): Full proxy URL
- `target_url` (str): URL to test (default: "https://www.imot.bg")

**Returns:**
- `bool`: True if proxy works with target site, False otherwise

**For imot.bg, validates presence of:**
- "imot.bg"
- "имоти" (properties in Bulgarian)
- "недвижими имоти" (real estate)

**For other sites:**
- Just validates 200 status code

#### `check_all(self, proxy_url: str) -> dict`

Run all quality checks on a proxy.

**Parameters:**
- `proxy_url` (str): Full proxy URL

**Returns:**
- `dict`: Results dictionary with keys:
  - `google_passed` (bool): Google check result
  - `target_passed` (bool): Target site check result

### Helper Functions

#### `enrich_proxy_with_quality(proxy: dict, timeout: int = 15) -> dict`

Add quality check results to a proxy dictionary.

**Parameters:**
- `proxy` (dict): Proxy dict with 'protocol', 'host', 'port' keys
- `timeout` (int): Request timeout in seconds

**Returns:**
- `dict`: Same proxy dict with added fields:
  - `google_passed` (bool or None)
  - `target_passed` (bool or None)
  - `quality_checked_at` (float): Unix timestamp

**Example:**
```python
proxy = {"host": "1.2.3.4", "port": 8080, "protocol": "http"}
enriched = enrich_proxy_with_quality(proxy)
# {
#     'host': '1.2.3.4',
#     'port': 8080,
#     'protocol': 'http',
#     'google_passed': True,
#     'target_passed': True,
#     'quality_checked_at': 1703123456.789
# }
```

#### `enrich_proxies_batch(proxies: list[dict], timeout: int = 15) -> list[dict]`

Add quality check results to a batch of proxies.

**Parameters:**
- `proxies` (list): List of proxy dicts
- `timeout` (int): Request timeout per proxy

**Returns:**
- `list`: Same list with quality fields added to each proxy

## Integration with Existing Proxy System

### With ProxyValidator

The Quality Checker complements the existing `ProxyValidator`:

```python
from proxies.proxy_validator import ProxyValidator
from proxies.quality_checker import enrich_proxy_with_quality

# Step 1: Basic liveness check
validator = ProxyValidator()
if validator.check_proxy_liveness("http://1.2.3.4:8080"):
    # Step 2: Quality check
    proxy = {"host": "1.2.3.4", "port": 8080, "protocol": "http"}
    enriched = enrich_proxy_with_quality(proxy)

    if enriched["google_passed"] and enriched["target_passed"]:
        print("Premium quality proxy!")
```

### With Anonymity Checker

Combine with anonymity checking for complete validation:

```python
from proxies.anonymity_checker import enrich_proxy_with_anonymity
from proxies.quality_checker import enrich_proxy_with_quality

proxy = {"host": "1.2.3.4", "port": 8080, "protocol": "http"}

# Add anonymity level
proxy = enrich_proxy_with_anonymity(proxy)

# Add quality metrics
proxy = enrich_proxy_with_quality(proxy)

# Now proxy has: anonymity, google_passed, target_passed, quality_checked_at
```

### Filtering Strategy

Recommended filtering strategy for production use:

```python
from proxies.quality_checker import enrich_proxies_batch

# 1. Get proxy pool
proxies = get_proxy_pool()  # Your proxy source

# 2. Enrich with quality data
enriched = enrich_proxies_batch(proxies, timeout=10)

# 3. Filter based on requirements
premium = [
    p for p in enriched
    if p.get("google_passed") and p.get("target_passed")
]

google_only = [
    p for p in enriched
    if p.get("google_passed") and not p.get("target_passed")
]

target_only = [
    p for p in enriched
    if not p.get("google_passed") and p.get("target_passed")
]

# 4. Use appropriate tier
if premium:
    use_proxies(premium)  # Best quality
elif target_only:
    use_proxies(target_only)  # Good for imot.bg
else:
    use_proxies(google_only)  # Fallback
```

## Error Handling

The Quality Checker handles errors gracefully:

- **Timeout**: Returns False, logs debug message
- **ProxyError**: Returns False, logs debug message
- **Other exceptions**: Returns False, logs debug message
- **Missing host/port**: Returns None for checks, logs warning

All exceptions are caught and logged, so batch processing continues even if individual proxies fail.

## Performance Considerations

### Timeout Settings

- **Default**: 15 seconds (balanced)
- **Fast screening**: 5-10 seconds (risk of false negatives)
- **Thorough validation**: 20-30 seconds (slower but more accurate)

### Batch Processing

For large batches, consider:

```python
from concurrent.futures import ThreadPoolExecutor

def check_proxy_quality(proxy):
    return enrich_proxy_with_quality(proxy, timeout=10)

# Parallel processing
with ThreadPoolExecutor(max_workers=10) as executor:
    enriched = list(executor.map(check_proxy_quality, proxies))
```

### Caching

For proxies checked recently, consider caching:

```python
import time

def is_recent_check(proxy, max_age_seconds=3600):
    checked_at = proxy.get("quality_checked_at", 0)
    return (time.time() - checked_at) < max_age_seconds

# Only re-check if stale
if not is_recent_check(proxy):
    proxy = enrich_proxy_with_quality(proxy)
```

## Testing

Run the test suite:

```bash
pytest tests/test_quality_checker.py -v
```

Run specific test:

```bash
pytest tests/test_quality_checker.py::test_check_google_success -v
```

## Examples

See `proxies/quality_checker_example.py` for comprehensive examples:

```bash
python proxies/quality_checker_example.py
```

## Troubleshooting

### High Failure Rate

If many proxies fail quality checks:

1. **Increase timeout**: Some proxies are slow
   ```python
   checker = QualityChecker(timeout=30)
   ```

2. **Check indicators**: Verify detection strings are current
   ```python
   from proxies.quality_checker import GOOGLE_CAPTCHA_INDICATORS, IMOT_BG_INDICATORS
   print(GOOGLE_CAPTCHA_INDICATORS)
   print(IMOT_BG_INDICATORS)
   ```

3. **Test manually**: Verify sites are accessible
   ```bash
   curl -x http://1.2.3.4:8080 https://www.google.com
   curl -x http://1.2.3.4:8080 https://www.imot.bg
   ```

### False Positives

If good proxies fail checks:

- **Google**: Google may be blocking all proxies temporarily
- **imot.bg**: Site may have changed HTML structure
- **Network**: Check your network allows proxy connections

### Slow Performance

For faster checks:

1. Reduce timeout for quick screening
2. Use batch processing with parallel execution
3. Cache recent check results
4. Filter proxies by basic liveness first

## Integration Examples

### With Celery Task

```python
from celery import Task
from proxies.quality_checker import enrich_proxy_with_quality

class QualityCheckTask(Task):
    def run(self, proxy):
        return enrich_proxy_with_quality(proxy, timeout=15)

@app.task(base=QualityCheckTask)
def check_proxy_quality_async(proxy):
    pass
```

### With Database Storage

```python
import sqlite3
from proxies.quality_checker import enrich_proxy_with_quality

def store_quality_results(proxy):
    enriched = enrich_proxy_with_quality(proxy)

    conn = sqlite3.connect("proxies.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE proxies
        SET google_passed = ?,
            target_passed = ?,
            quality_checked_at = ?
        WHERE host = ? AND port = ?
    """, (
        enriched["google_passed"],
        enriched["target_passed"],
        enriched["quality_checked_at"],
        enriched["host"],
        enriched["port"],
    ))

    conn.commit()
    conn.close()
```

## Changelog

### v1.0.0 (2025-12-23)
- Initial release
- Google captcha detection
- imot.bg validation
- Batch processing support
- Comprehensive test suite
