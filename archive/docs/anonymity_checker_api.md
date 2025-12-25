# Anonymity Checker API Reference

Quick reference for using the enhanced anonymity checker module.

## Core Functions

### `get_real_ip(timeout=15, force_refresh=False)`

Get your real IP address (without proxy).

**Parameters:**
- `timeout` (int): Request timeout in seconds (default: 15)
- `force_refresh` (bool): Bypass cache and fetch fresh IP (default: False)

**Returns:**
- `str`: Real IP address (e.g., "1.2.3.4")
- `None`: If detection failed

**Example:**
```python
from proxies import anonymity_checker

# Get real IP (cached after first call)
real_ip = anonymity_checker.get_real_ip()
print(f"Your IP: {real_ip}")

# Force refresh (e.g., after VPN change)
new_ip = anonymity_checker.get_real_ip(force_refresh=True)
```

---

### `parse_anonymity(response_text, real_ip)`

Parse anonymity level from HTTP response.

**Parameters:**
- `response_text` (str): Full HTTP response with headers
- `real_ip` (str): Your real IP address

**Returns:**
- `str`: One of "Transparent", "Anonymous", or "Elite"

**Example:**
```python
response = '{"headers": {"X-Forwarded-For": "5.6.7.8"}}'
level = anonymity_checker.parse_anonymity(response, "1.2.3.4")
print(level)  # "Anonymous"
```

---

### `check_proxy_anonymity(proxy_url, real_ip=None, timeout=15)`

Check the anonymity level of a proxy.

**Parameters:**
- `proxy_url` (str): Full proxy URL (e.g., "http://1.2.3.4:8080")
- `real_ip` (str, optional): Your real IP (auto-fetched if not provided)
- `timeout` (int): Request timeout in seconds (default: 15)

**Returns:**
- `str`: One of "Transparent", "Anonymous", or "Elite"
- `None`: If check failed (proxy dead or judges unreachable)

**Example:**
```python
# Basic usage
level = anonymity_checker.check_proxy_anonymity("http://1.2.3.4:8080")
print(f"Anonymity: {level}")

# With pre-fetched real IP (more efficient)
real_ip = anonymity_checker.get_real_ip()
level = anonymity_checker.check_proxy_anonymity(
    "http://1.2.3.4:8080",
    real_ip=real_ip
)

# SOCKS5 proxy
level = anonymity_checker.check_proxy_anonymity("socks5://1.2.3.4:1080")
```

---

### `enrich_proxy_with_anonymity(proxy, timeout=15)`

Add anonymity level to a single proxy dict.

**Parameters:**
- `proxy` (dict): Proxy dict with 'protocol', 'host', 'port' keys
- `timeout` (int): Request timeout in seconds (default: 15)

**Returns:**
- `dict`: Same proxy with 'anonymity' and 'anonymity_verified_at' fields added

**Example:**
```python
proxy = {
    "protocol": "http",
    "host": "1.2.3.4",
    "port": 8080,
}

enriched = anonymity_checker.enrich_proxy_with_anonymity(proxy, timeout=10)

print(enriched)
# {
#     "protocol": "http",
#     "host": "1.2.3.4",
#     "port": 8080,
#     "anonymity": "Elite",
#     "anonymity_verified_at": "2025-12-23T10:30:45.123456+00:00"
# }
```

---

### `check_proxy_anonymity_batch(proxies, timeout=15)`

Check anonymity for a batch of proxies.

**Parameters:**
- `proxies` (list[dict]): List of proxy dicts with 'protocol', 'host', 'port' keys
- `timeout` (int): Request timeout per proxy (default: 15)

**Returns:**
- `list[dict]`: Same list with 'anonymity' field added to each proxy

**Example:**
```python
proxies = [
    {"protocol": "http", "host": "1.1.1.1", "port": 8080},
    {"protocol": "http", "host": "2.2.2.2", "port": 8080},
    {"protocol": "socks5", "host": "3.3.3.3", "port": 1080},
]

enriched = anonymity_checker.check_proxy_anonymity_batch(proxies, timeout=10)

for proxy in enriched:
    print(f"{proxy['host']}:{proxy['port']} - {proxy['anonymity']}")
```

---

## Constants

### `PRIVACY_HEADERS`

List of HTTP headers that reveal proxy usage:

```python
[
    "VIA",
    "X-FORWARDED-FOR",
    "X-FORWARDED",
    "FORWARDED-FOR",
    "FORWARDED-FOR-IP",
    "FORWARDED",
    "X-REAL-IP",
    "CLIENT-IP",
    "X-CLIENT-IP",
    "PROXY-CONNECTION",
    "X-PROXY-ID",
    "X-BLUECOAT-VIA",
    "X-ORIGINATING-IP",
]
```

---

### `JUDGE_URLS`

URLs used to check proxy anonymity (with automatic fallback):

```python
[
    "https://httpbin.org/headers",
    "http://httpbin.org/headers",
    "https://httpbin.io/headers",
    "http://httpbin.io/headers",
    "https://ifconfig.me/all.json",
]
```

---

### `REAL_IP_URLS`

URLs used to detect your real IP:

```python
[
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
]
```

---

### `DEFAULT_TIMEOUT`

Default timeout for requests (15 seconds).

---

## Anonymity Levels

### Transparent
- **Description**: Real IP appears in the response
- **Privacy**: None (worst)
- **Use case**: Not recommended for privacy-sensitive tasks

### Anonymous
- **Description**: IP hidden but privacy headers present
- **Privacy**: Medium
- **Use case**: Basic scraping, non-sensitive data collection

### Elite
- **Description**: IP hidden AND no privacy headers
- **Privacy**: High (best)
- **Use case**: Privacy-sensitive tasks, production scraping

---

## Error Handling

Functions handle errors gracefully:

```python
# Returns None if check fails
level = anonymity_checker.check_proxy_anonymity("http://dead-proxy:8080")
if level is None:
    print("Proxy check failed")
else:
    print(f"Anonymity: {level}")

# Fallback logic for enrichment
proxy = {"protocol": "http", "host": "1.2.3.4", "port": 8080}
enriched = anonymity_checker.enrich_proxy_with_anonymity(proxy)

if enriched["anonymity"] is None:
    print("Could not determine anonymity")
else:
    print(f"Anonymity: {enriched['anonymity']}")
```

---

## Best Practices

### 1. Cache Real IP

```python
# Fetch once per session
real_ip = anonymity_checker.get_real_ip()

# Reuse for multiple checks
for proxy_url in proxy_urls:
    level = anonymity_checker.check_proxy_anonymity(proxy_url, real_ip=real_ip)
```

### 2. Use Batch Processing

```python
# More efficient than individual checks
proxies = [...]
enriched = anonymity_checker.check_proxy_anonymity_batch(proxies)
```

### 3. Check Timestamp Staleness

```python
from datetime import datetime, timezone, timedelta

def is_stale(proxy, max_age_hours=24):
    """Check if anonymity check is too old"""
    if not proxy.get("anonymity_verified_at"):
        return True

    verified_at = datetime.fromisoformat(proxy["anonymity_verified_at"])
    age = datetime.now(timezone.utc) - verified_at

    return age > timedelta(hours=max_age_hours)

# Re-check if stale
if is_stale(proxy):
    proxy = anonymity_checker.enrich_proxy_with_anonymity(proxy)
```

### 4. Filter by Anonymity Level

```python
# Keep only Elite proxies
elite_proxies = [
    p for p in enriched_proxies
    if p.get("anonymity") == "Elite"
]

# Keep Elite or Anonymous
safe_proxies = [
    p for p in enriched_proxies
    if p.get("anonymity") in ["Elite", "Anonymous"]
]
```

### 5. Handle Network Failures

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Logs will show which judges failed and why
level = anonymity_checker.check_proxy_anonymity("http://1.2.3.4:8080")
```

---

## Common Issues

### Issue: All judge URLs failing

**Possible causes:**
- Network connectivity issues
- Judge services are down
- Firewall blocking requests

**Solution:**
```python
# Check with verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

level = anonymity_checker.check_proxy_anonymity("http://1.2.3.4:8080")
# Check logs for specific errors
```

### Issue: Cannot detect real IP

**Possible causes:**
- Network offline
- IP detection services blocked
- VPN/proxy already active

**Solution:**
```python
# Provide real IP manually if known
level = anonymity_checker.check_proxy_anonymity(
    "http://1.2.3.4:8080",
    real_ip="YOUR_REAL_IP"
)
```

### Issue: Slow checks

**Possible causes:**
- High timeout values
- Dead proxies
- Slow judge services

**Solution:**
```python
# Reduce timeout for faster failures
level = anonymity_checker.check_proxy_anonymity(
    "http://1.2.3.4:8080",
    timeout=5  # Fail faster
)
```

---

## Integration Examples

### With Proxy Validation Pipeline

```python
from proxies import anonymity_checker, validator

def validate_and_check_anonymity(proxies, min_level="Anonymous"):
    """Validate proxies and filter by anonymity level"""
    # First validate they work
    valid_proxies = validator.validate_proxies(proxies)

    # Then check anonymity
    enriched = anonymity_checker.check_proxy_anonymity_batch(valid_proxies)

    # Filter by minimum anonymity level
    levels = ["Transparent", "Anonymous", "Elite"]
    min_index = levels.index(min_level)

    filtered = [
        p for p in enriched
        if p.get("anonymity") and levels.index(p["anonymity"]) >= min_index
    ]

    return filtered
```

### With Database Storage

```python
import sqlite3
from datetime import datetime

def store_proxy_with_anonymity(db_path, proxy):
    """Store proxy with anonymity info in database"""
    enriched = anonymity_checker.enrich_proxy_with_anonymity(proxy)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO proxies (host, port, protocol, anonymity, verified_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        enriched["host"],
        enriched["port"],
        enriched["protocol"],
        enriched.get("anonymity"),
        enriched.get("anonymity_verified_at"),
    ))

    conn.commit()
    conn.close()
```

### With Scheduled Re-checks

```python
from datetime import datetime, timezone, timedelta
import time

def recheck_stale_proxies(proxies, max_age_hours=24):
    """Re-check proxies with stale anonymity data"""
    now = datetime.now(timezone.utc)
    stale_proxies = []

    for proxy in proxies:
        verified_at = proxy.get("anonymity_verified_at")

        if not verified_at:
            stale_proxies.append(proxy)
            continue

        dt = datetime.fromisoformat(verified_at)
        age = now - dt

        if age > timedelta(hours=max_age_hours):
            stale_proxies.append(proxy)

    if stale_proxies:
        print(f"Re-checking {len(stale_proxies)} stale proxies...")
        anonymity_checker.check_proxy_anonymity_batch(stale_proxies)

    return proxies
```

---

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/test_anonymity_checker.py -v

# Specific test
python -m pytest tests/test_anonymity_checker.py::TestGetRealIP::test_get_real_ip_success -v

# With coverage
python -m pytest tests/test_anonymity_checker.py --cov=proxies.anonymity_checker
```

Run verification script:

```bash
python verify_anonymity_enhancements.py
```

---

## Performance

### Typical Timings

- `get_real_ip()`: 0.2-1.0s (first call), 0.0s (cached)
- `check_proxy_anonymity()`: 0.5-2.0s per proxy (depends on proxy speed)
- `check_proxy_anonymity_batch()`: 0.5-2.0s per proxy (sequential)

### Optimization Tips

1. **Cache real IP**: Saves 0.5-1.0s per check
2. **Lower timeout**: Fail faster on dead proxies
3. **Batch processing**: Fetches real IP once for all proxies
4. **Parallel processing**: Use threading for batch checks (not implemented yet)

---

## Changelog

### v2.0.0 (2025-12-23)

**New Features:**
- Added `force_refresh` parameter to `get_real_ip()`
- Added `anonymity_verified_at` timestamp field
- Added 3 new privacy headers (X-CLIENT-IP, X-BLUECOAT-VIA)
- Added 3 new judge URLs for fallback

**Improvements:**
- Enhanced error handling with specific exception types
- Better logging for debugging
- Improved judge fallback mechanism

**Testing:**
- Added 38 unit tests
- Created verification script

**Documentation:**
- API reference guide
- Enhancement summary document
