# Anonymity Checker Enhancements

## Summary

Enhanced `/home/wow/Projects/sale-sofia/proxies/anonymity_checker.py` with improved reliability, better error handling, and additional privacy checks.

## Changes Made

### 1. Full Header Inspection (Enhanced Privacy Headers)

Added missing privacy-revealing headers to `PRIVACY_HEADERS`:

```python
PRIVACY_HEADERS = [
    "VIA",
    "X-FORWARDED-FOR",
    "X-FORWARDED",
    "FORWARDED-FOR",
    "FORWARDED-FOR-IP",
    "FORWARDED",
    "X-REAL-IP",
    "CLIENT-IP",
    "X-CLIENT-IP",           # NEW
    "PROXY-CONNECTION",
    "X-PROXY-ID",
    "X-BLUECOAT-VIA",        # NEW
    "X-ORIGINATING-IP",
]
```

**Impact:** More comprehensive detection of anonymous proxies that leak privacy headers.

### 2. Multiple Judge URLs with Fallback

Expanded `JUDGE_URLS` from 2 to 5 URLs:

```python
JUDGE_URLS = [
    "https://httpbin.org/headers",    # Primary
    "http://httpbin.org/headers",     # Primary (fallback to HTTP)
    "https://httpbin.io/headers",     # Fallback
    "http://httpbin.io/headers",      # Fallback (HTTP)
    "https://ifconfig.me/all.json",   # Fallback
]
```

**Impact:** Increased reliability - if one judge service is down, others will be tried automatically.

### 3. Cached Real IP with Force Refresh

Enhanced `get_real_ip()` function:

```python
def get_real_ip(timeout: int = DEFAULT_TIMEOUT, force_refresh: bool = False) -> Optional[str]:
    """
    Get your real IP address (without using proxy).

    Args:
        timeout: Request timeout in seconds
        force_refresh: If True, bypass cache and fetch fresh IP

    Returns:
        Real IP address as string, or None if detection failed
    """
```

**New Features:**
- `force_refresh` parameter to bypass cache when needed
- Better logging of failures with exception details
- Maintains module-level cache `_real_ip_cache`

**Impact:**
- Avoids repeated network requests for real IP detection
- Option to refresh when IP might have changed (e.g., VPN switch)

### 4. Timestamp on Anonymity Verification

Added timestamp field to `enrich_proxy_with_anonymity()`:

```python
def enrich_proxy_with_anonymity(proxy: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Returns:
        Same proxy dict with 'anonymity' and 'anonymity_verified_at' fields added
    """
    # ... check logic ...

    proxy["anonymity"] = anonymity
    proxy["anonymity_verified_at"] = datetime.now(timezone.utc).isoformat()

    return proxy
```

**Output Example:**
```python
{
    "protocol": "http",
    "host": "1.2.3.4",
    "port": 8080,
    "anonymity": "Elite",
    "anonymity_verified_at": "2025-12-23T10:30:45.123456+00:00"  # ISO format with timezone
}
```

**Impact:** Track when anonymity was verified - useful for cache invalidation and debugging.

### 5. Improved Error Handling

Enhanced `check_proxy_anonymity()` with granular exception handling:

```python
try:
    response = requests.get(judge_url, proxies={...}, timeout=timeout)
    # ... process response ...

except requests.exceptions.Timeout:
    logger.debug(f"Judge {judge_url} timed out for {proxy_url}")
    continue
except requests.exceptions.ProxyError as e:
    logger.debug(f"Proxy error with {judge_url} for {proxy_url}: {e}")
    continue
except requests.exceptions.ConnectionError as e:
    logger.debug(f"Connection error with {judge_url} for {proxy_url}: {e}")
    continue
except requests.exceptions.RequestException as e:
    logger.debug(f"Judge {judge_url} failed for {proxy_url}: {e}")
    continue
```

**Impact:**
- Better logging for debugging proxy issues
- Graceful fallback to next judge URL on specific error types
- More informative error messages

### 6. Enhanced Logging

Improved debug logging throughout:

```python
# get_real_ip() now logs failures
logger.debug(f"Failed to get real IP from {url}: {e}")

# check_proxy_anonymity() now logs which judge succeeded
logger.debug(f"Proxy {proxy_url} anonymity: {anonymity} (via {judge_url})")
```

**Impact:** Easier debugging and monitoring of anonymity checks.

## New Test Suite

Created comprehensive test suite in `/home/wow/Projects/sale-sofia/tests/test_anonymity_checker.py`:

### Test Coverage

1. **TestGetRealIP** (7 tests)
   - Successful IP detection
   - Cache behavior
   - Force refresh
   - Fallback between URLs
   - All URLs failing
   - Invalid IP format rejection

2. **TestParseAnonymity** (8 tests)
   - Transparent proxy detection
   - Anonymous proxy detection (various headers)
   - Elite proxy detection
   - Case-insensitive header matching

3. **TestCheckProxyAnonymity** (9 tests)
   - Elite proxy check
   - Transparent proxy check
   - Real IP provided vs fetched
   - No real IP available
   - Timeout handling
   - Proxy error handling
   - Connection error handling
   - All judges failing

4. **TestEnrichProxyWithAnonymity** (7 tests)
   - Successful enrichment
   - Missing host/port
   - Fallback to exit_ip
   - Timestamp format validation

5. **TestCheckProxyAnonymityBatch** (3 tests)
   - Batch processing
   - Missing data handling
   - Partial failures

6. **TestPrivacyHeaders** (2 tests)
   - All required headers present
   - All headers uppercase

7. **TestJudgeUrls** (2 tests)
   - Multiple URLs configured
   - Primary and fallback judges present

**Total: 38 unit tests**

### Running Tests

```bash
# Run all tests
python -m pytest tests/test_anonymity_checker.py -v

# Run specific test class
python -m pytest tests/test_anonymity_checker.py::TestGetRealIP -v

# Run with coverage
python -m pytest tests/test_anonymity_checker.py --cov=proxies.anonymity_checker --cov-report=html
```

## Verification Script

Created `/home/wow/Projects/sale-sofia/verify_anonymity_enhancements.py` to verify all enhancements:

```bash
python verify_anonymity_enhancements.py
```

**Checks:**
1. Privacy headers configuration
2. Judge URLs configuration
3. Real IP caching with force_refresh
4. Timestamp format
5. Error handling implementation

## Backward Compatibility

All changes are **fully backward compatible**:

- Existing function signatures unchanged (only added optional parameters)
- New fields added to proxy dicts (existing fields preserved)
- Fallback behavior maintains original logic
- Default timeout and behavior unchanged

## Migration Guide

No migration needed! The enhancements are drop-in replacements:

```python
from proxies import anonymity_checker

# Old usage still works
proxy = {"protocol": "http", "host": "1.2.3.4", "port": 8080}
enriched = anonymity_checker.enrich_proxy_with_anonymity(proxy)

# New features available
print(enriched["anonymity"])                  # "Elite", "Anonymous", or "Transparent"
print(enriched["anonymity_verified_at"])      # "2025-12-23T10:30:45.123456+00:00"

# Force refresh real IP if needed
real_ip = anonymity_checker.get_real_ip(force_refresh=True)
```

## Performance Considerations

1. **Real IP Caching**: Reduces network requests from N to 1 per session
2. **Judge Fallback**: Adds latency only on failure (1-5 attempts max)
3. **Error Handling**: No performance impact, only better logging
4. **Timestamp**: Negligible overhead (~microseconds)

## Files Modified

1. `/home/wow/Projects/sale-sofia/proxies/anonymity_checker.py` - Core implementation
2. `/home/wow/Projects/sale-sofia/tests/test_anonymity_checker.py` - New test suite
3. `/home/wow/Projects/sale-sofia/verify_anonymity_enhancements.py` - Verification script

## Next Steps

1. Run the verification script to confirm all enhancements
2. Run the test suite to ensure everything works
3. Use the enhanced anonymity checker in proxy validation workflows
4. Monitor logs for better debugging of proxy issues

## Example Usage

```python
from proxies import anonymity_checker

# Check anonymity of a single proxy
proxy = {
    "protocol": "http",
    "host": "1.2.3.4",
    "port": 8080,
}

enriched = anonymity_checker.enrich_proxy_with_anonymity(proxy, timeout=10)

print(f"Anonymity: {enriched['anonymity']}")
print(f"Verified at: {enriched['anonymity_verified_at']}")

# Check a batch of proxies
proxies = [
    {"protocol": "http", "host": "1.1.1.1", "port": 8080},
    {"protocol": "http", "host": "2.2.2.2", "port": 8080},
    {"protocol": "socks5", "host": "3.3.3.3", "port": 1080},
]

enriched_batch = anonymity_checker.check_proxy_anonymity_batch(proxies, timeout=10)

for p in enriched_batch:
    print(f"{p['host']}:{p['port']} - {p['anonymity']}")
```

## References

- [HTTP Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers)
- [Proxy Anonymity Levels](https://www.proxynova.com/proxy-articles/proxy-anonymity-levels)
- [httpbin.org](https://httpbin.org/) - HTTP request & response service
- [ifconfig.me](https://ifconfig.me/) - IP address lookup service
