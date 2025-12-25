# Proxy Scorer - Runtime Scoring System

## Overview

The `ScoredProxyPool` class provides runtime proxy scoring based on the Competitor-Intel pattern (see `docs/PROXY_SYSTEM_SPECS.md` section 10.7). Proxies are scored dynamically based on success/failure rates, with automatic removal of consistently failing proxies.

## Features

1. **Weighted Random Selection**: Proxies with higher scores are more likely to be selected
2. **Dynamic Scoring**: Scores update based on real-world performance
3. **Auto-Pruning**: Bad proxies are automatically removed
4. **Thread-Safe**: Safe for concurrent access from multiple threads
5. **Persistent Scores**: Scores are saved to disk and survive restarts
6. **Smart Initialization**: Initial scores based on response times from validation

## Files

- `/home/wow/Projects/sale-sofia/proxies/proxy_scorer.py` - Main implementation
- `/home/wow/Projects/sale-sofia/tests/test_proxy_scorer.py` - Unit tests
- `/home/wow/Projects/sale-sofia/proxies/proxy_scorer_example.py` - Usage examples
- `/home/wow/Projects/sale-sofia/proxies/proxy_scores.json` - Persisted scores (auto-created)

## Usage

### Basic Usage

```python
from proxies.proxy_scorer import ScoredProxyPool
from paths import PROXIES_DIR

# Initialize pool from live_proxies.json
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

# Get a proxy (weighted random selection)
proxy_url = pool.get_proxy_url()
# Returns: "http://1.2.3.4:8080"

# Use the proxy...
try:
    # ... your scraping code ...
    pool.record_result(proxy_url, success=True)
except Exception:
    pool.record_result(proxy_url, success=False)
```

### Advanced Usage

```python
# Get proxy dict instead of URL
proxy = pool.select_proxy()
# Returns: {"protocol": "http", "host": "1.2.3.4", "port": 8080, ...}

# Get pool statistics
stats = pool.get_stats()
# Returns: {"total_proxies": 10, "average_score": 1.5, ...}

# Manually remove a bad proxy
pool.remove_proxy("1.2.3.4:8080")

# Reload proxies after Celery refresh
pool.reload_proxies()
```

## How It Works

### 1. Initialization

When the pool is created:

1. Loads proxies from `live_proxies.json`
2. Loads existing scores from `proxy_scores.json` (if exists)
3. Initializes scores for new proxies:
   - `score = 1.0 / response_time` (from validation)
   - Faster proxies get higher initial scores

### 2. Selection

When you call `select_proxy()`:

1. Calculates weights based on scores
2. Performs weighted random selection (higher score = higher probability)
3. Updates `last_used` timestamp
4. Returns the selected proxy

### 3. Score Updates

When you call `record_result()`:

**On Success:**
- `score *= 1.1` (+10% reward)
- `failures = 0` (reset counter)

**On Failure:**
- `score *= 0.5` (-50% penalty)
- `failures += 1`

**Auto-Pruning:**
Proxy is removed if:
- `failures >= 3` (consecutive failures)
- OR `score < 0.01` (too low)

### 4. Persistence

Scores are automatically saved to `proxy_scores.json` after each update:

```json
{
  "1.2.3.4:8080": {
    "score": 1.5,
    "failures": 0,
    "last_used": 1703361600
  }
}
```

## Integration Patterns

### Pattern 1: Direct Usage (Replace Mubeng)

Use the scorer to select proxies directly:

```python
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

for url in urls_to_scrape:
    proxy_url = pool.get_proxy_url()
    browser = await create_instance(proxy=proxy_url)

    try:
        await browser.goto(url)
        # ... scraping ...
        pool.record_result(proxy_url, success=True)
    except Exception:
        pool.record_result(proxy_url, success=False)
```

### Pattern 2: Hybrid with Mubeng

Use scorer to select top proxies, then feed to mubeng:

```python
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

# Get top 20 proxies by score
top_proxies = sorted(
    pool.proxies,
    key=lambda p: pool.scores.get(pool._get_proxy_key(p), {}).get("score", 0),
    reverse=True
)[:20]

# Write to temp file for mubeng
with open("top_proxies.txt", "w") as f:
    for proxy in top_proxies:
        f.write(f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}\n")

# Start mubeng with top proxies only
subprocess.Popen(["mubeng", "-a", "localhost:8089", "-f", "top_proxies.txt"])
```

### Pattern 3: Monitoring Mode

Track proxy performance alongside existing setup:

```python
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

# Your existing browser setup with mubeng rotator
browser = await create_instance(proxy="http://localhost:8089")

# After each request, check which proxy was actually used
# (would need to query mubeng or inspect response headers)
proxy_used = get_actual_proxy_used()  # Custom logic

# Record result for tracking
pool.record_result(proxy_used, success=True)

# Periodically check stats
if request_count % 100 == 0:
    stats = pool.get_stats()
    logger.info(f"Pool stats: {stats}")
```

## Configuration

Settings from `proxy_scorer.py`:

```python
SCORE_SUCCESS_MULTIPLIER = 1.1  # +10% on success
SCORE_FAILURE_MULTIPLIER = 0.5  # -50% on failure
MAX_FAILURES = 3                # Auto-remove after 3 failures
MIN_SCORE = 0.01                # Auto-remove if score < 0.01
```

Adjust these values based on your needs:
- **More aggressive pruning**: Lower `MAX_FAILURES` to 2
- **More forgiving**: Increase `SCORE_FAILURE_MULTIPLIER` to 0.7
- **Faster score growth**: Increase `SCORE_SUCCESS_MULTIPLIER` to 1.2

## Thread Safety

All methods are thread-safe:

```python
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

# Safe to call from multiple threads
def worker():
    for _ in range(100):
        proxy = pool.select_proxy()
        # ... use proxy ...
        pool.record_result(proxy_url, success=True)

threads = [Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

Uses `threading.Lock` internally to protect:
- Proxy selection
- Score updates
- Proxy removal
- File I/O

## Testing

Run unit tests:

```bash
cd /home/wow/Projects/sale-sofia
chmod +x run_proxy_scorer_tests.sh
./run_proxy_scorer_tests.sh
```

Or directly:

```bash
python -m pytest tests/test_proxy_scorer.py -v
```

Test coverage includes:
- Proxy loading and initialization
- Score calculation
- Weighted selection
- Success/failure recording
- Auto-pruning
- Thread safety
- Persistence
- Edge cases

## Monitoring

Get pool statistics:

```python
stats = pool.get_stats()
print(f"Total proxies: {stats['total_proxies']}")
print(f"Average score: {stats['average_score']:.3f}")
print(f"Proxies with failures: {stats['proxies_with_failures']}")
```

## Troubleshooting

### No proxies available

```python
if pool.get_proxy_url() is None:
    # Reload from file (in case Celery refreshed)
    pool.reload_proxies()

    if pool.get_proxy_url() is None:
        # Trigger proxy refresh
        from orchestrator import Orchestrator
        orch = Orchestrator()
        orch.trigger_proxy_refresh()
```

### All proxies removed

If all proxies are auto-pruned, reload from file:

```python
pool.reload_proxies()
```

The reload will reinitialize scores from response times.

### Scores not updating

Check that `proxy_scores.json` is writable:

```bash
ls -la /home/wow/Projects/sale-sofia/proxies/proxy_scores.json
```

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Design Decisions

### Why not integrate with existing ProxyValidator?

`ProxyValidator` is designed for pre-flight checks of the mubeng rotator endpoint (`localhost:8089`), not individual proxy scoring. The `ScoredProxyPool` is designed for runtime scoring of individual proxies from the pool.

### Why separate from mubeng?

Mubeng handles rotation but doesn't track proxy performance. The scorer provides:
- Historical performance tracking
- Weighted selection (not just random)
- Auto-removal of bad proxies
- Persistent scores across restarts

### Why not use Redis?

JSON file persistence is simpler and sufficient for our use case:
- Small data size (~100 proxies)
- Infrequent writes (only on score updates)
- No need for shared state across machines
- Easy to inspect/debug

Could be upgraded to Redis later if needed.

## Future Enhancements

Potential improvements (not implemented):

1. **Time-based decay**: Reduce scores over time if not used
2. **Success rate tracking**: Track overall success percentage
3. **Response time tracking**: Factor average response time into scores
4. **Geo-based selection**: Prefer proxies from specific countries
5. **Redis backend**: Use Redis instead of JSON for multi-worker setups
6. **Web dashboard**: Visualize proxy scores and performance

## References

- Design spec: `/home/wow/Projects/sale-sofia/docs/PROXY_SYSTEM_SPECS.md` section 10.7
- Competitor-Intel pattern: `RobustProxyTransport` class (lines 149-171)
- Integration example: `/home/wow/Projects/sale-sofia/proxies/proxy_scorer_example.py`
