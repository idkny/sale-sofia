# ScoredProxyPool Integration with main.py

## Overview

The `ScoredProxyPool` has been integrated into `main.py` to track proxy performance during scraping sessions. Due to the architecture using mubeng as a rotating proxy server, the scoring tracks the overall success/failure rate of scraping attempts rather than individual proxies.

## Architecture Considerations

### Mubeng Rotator
- Mubeng (`http://localhost:8089`) acts as a proxy rotator that internally manages multiple proxies
- It automatically rotates proxies on errors (configured with `--rotate-on-error`)
- The scraper only sees the mubeng endpoint, not which individual proxy was used

### Scoring Strategy
Since mubeng hides which proxy is actually used for each request, we track:
- **Session-level success/failure**: Each listing scrape is recorded as success or failure
- **Mubeng endpoint tracking**: The scoring tracks `http://localhost:8089` as a "meta-proxy"
- **Pool-level metrics**: Overall proxy pool health and performance statistics

This approach provides:
1. Performance monitoring across scraping sessions
2. Historical data about proxy pool effectiveness
3. Metrics for triggering proxy refresh decisions

## Changes Made to main.py

### 1. Imports Added
```python
from paths import LOGS_DIR, PROXIES_DIR
from proxies.proxy_scorer import ScoredProxyPool
```

### 2. Function Signature Updated
`scrape_from_start_url()` now accepts an optional `proxy_pool` parameter:

```python
async def scrape_from_start_url(
    scraper,
    start_url: str,
    limit: int,
    proxy: str | None = None,
    proxy_pool: Optional[ScoredProxyPool] = None
) -> dict:
```

Returns statistics: `{scraped: int, failed: int, total_attempts: int}`

### 3. Success/Failure Tracking
The scraping function now records results after each attempt:

```python
# On success
if listing:
    data_store_main.save_listing(listing)
    stats["scraped"] += 1
    if proxy_pool and proxy:
        proxy_pool.record_result(proxy, success=True)

# On failure
else:
    stats["failed"] += 1
    if proxy_pool and proxy:
        proxy_pool.record_result(proxy, success=False)
```

### 4. Proxy Pool Initialization
In `run_auto_mode()`, after proxies are confirmed available:

```python
# Initialize proxy scoring pool
print("[INFO] Initializing proxy scoring system...")
try:
    proxy_pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")
    stats = proxy_pool.get_stats()
    print(f"[SUCCESS] Proxy pool initialized: {stats['total_proxies']} proxies, "
          f"avg score: {stats['average_score']:.2f}")
except Exception as e:
    logger.warning(f"Failed to initialize proxy pool: {e}")
    print(f"[WARNING] Proxy scoring disabled: {e}")
    proxy_pool = None
```

### 5. Proxy Refresh Integration
When proxies are refreshed (Level 3 recovery), the pool is reloaded:

```python
# After proxy refresh completes
if proxy_pool:
    print("[INFO] Reloading proxy pool after refresh...")
    proxy_pool.reload_proxies()
    stats = proxy_pool.get_stats()
    print(f"[SUCCESS] Proxy pool reloaded: {stats['total_proxies']} proxies")
```

### 6. Final Statistics
At the end of crawling, scores are saved and stats displayed:

```python
# Save final proxy scores
if proxy_pool:
    print("\n[INFO] Saving final proxy scores...")
    proxy_pool.save_scores()
    stats = proxy_pool.get_stats()
    print(f"[SUCCESS] Final proxy stats: {stats['total_proxies']} proxies, "
          f"avg score: {stats['average_score']:.2f}")
```

## What Gets Tracked

### Per-Listing Tracking
For each listing scrape attempt:
- Success: Listing extracted and saved → `record_result(proxy, success=True)`
- Failure: Exception or failed extraction → `record_result(proxy, success=False)`

### Search Page Tracking
For search page loads (pagination):
- Success: Page loaded and listings extracted (implicit - no recording)
- Failure: Exception during page load → `record_result(proxy, success=False)`

### Aggregated Statistics
The scraper now prints:
```
[SUMMARY] Total scraped: X, Failed: Y, Success rate: Z%
[SUCCESS] Final proxy stats: N proxies, avg score: S
```

## Files Modified

1. **main.py**
   - Added `ScoredProxyPool` integration
   - Modified `scrape_from_start_url()` to track success/failure
   - Modified `run_auto_mode()` to initialize and use proxy pool
   - Added statistics collection and reporting

## Files Created

1. **test_integration.py**
   - Test script to verify integration
   - Checks imports, initialization, and function signatures
   - Can be run without live proxies

2. **PROXY_SCORER_INTEGRATION.md** (this file)
   - Integration documentation

## Data Files

The integration creates/updates:

1. **proxies/proxy_scores.json**
   - Persisted proxy scores
   - Format: `{"host:port": {"score": 1.0, "failures": 0, "last_used": timestamp}}`
   - Note: When using mubeng, this tracks `localhost:8089` instead of individual proxies

## Limitations and Future Improvements

### Current Limitations

1. **No Individual Proxy Tracking**
   - Mubeng hides which proxy is used, so we can't score individual proxies during runtime
   - Scoring tracks the mubeng endpoint as a whole

2. **Limited Actionable Insights**
   - Since mubeng already auto-rotates on errors, scoring doesn't influence proxy selection
   - Scoring is primarily for monitoring, not optimization

### Future Improvements

**Option 1: Direct Proxy Selection (No Mubeng)**
- Replace mubeng with direct proxy selection using `ScoredProxyPool.select_proxy()`
- Each scrape attempt uses `pool.select_proxy()` to get the best proxy
- Failures trigger immediate rotation to next best proxy
- Benefits: True weighted selection, adaptive proxy ranking

**Option 2: Hybrid Approach**
- Use `ScoredProxyPool` to select top N proxies
- Feed only top-scored proxies to mubeng
- Periodically refresh mubeng's proxy list based on scores
- Benefits: Combines scoring intelligence with mubeng's rotation

**Option 3: Enhanced Monitoring**
- Add dashboard visualization of proxy performance over time
- Track success rates per website/domain
- Implement automatic proxy refresh triggers based on score thresholds

## Testing

Run the integration test:

```bash
cd /home/wow/Projects/sale-sofia
python test_integration.py
```

Expected output:
```
[TEST 1] Testing imports...
  ✓ All imports successful
[TEST 2] Testing ScoredProxyPool initialization...
  ✓ Proxy pool initialized successfully
[TEST 3] Testing record_result with mubeng URL...
  ✓ record_result handles mubeng URL correctly
[TEST 4] Testing function signature...
  ✓ Function signature is correct
```

## Syntax Verification

The code has been verified with:
```bash
python -m py_compile main.py
```

No syntax errors found.

## Usage

The integration is automatic - just run main.py as normal:

```bash
python main.py
```

You'll see additional output:
```
[INFO] Initializing proxy scoring system...
[SUCCESS] Proxy pool initialized: 50 proxies, avg score: 1.24
...
[STATS] Scraped: 45, Failed: 5
...
[SUMMARY] Total scraped: 180, Failed: 20, Success rate: 90.0%
[SUCCESS] Final proxy stats: 50 proxies, avg score: 1.18
```

## Monitoring Proxy Performance

Check the scores file after scraping:

```bash
cat proxies/proxy_scores.json
```

This shows which proxies (or the mubeng endpoint) have been performing well or poorly.

## Conclusion

The integration is complete and functional. While the current implementation has limitations due to mubeng's architecture, it provides valuable monitoring capabilities and lays the groundwork for future enhancements like direct proxy selection or hybrid approaches.
