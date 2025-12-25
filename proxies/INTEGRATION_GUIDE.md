# Proxy Scorer Integration Guide

## Quick Start

The proxy scorer is ready to use. Here's how to integrate it into your scraping workflow.

## Files Created

1. `/home/wow/Projects/sale-sofia/proxies/proxy_scorer.py` - Main implementation
2. `/home/wow/Projects/sale-sofia/tests/test_proxy_scorer.py` - Comprehensive unit tests
3. `/home/wow/Projects/sale-sofia/proxies/proxy_scorer_example.py` - Usage examples
4. `/home/wow/Projects/sale-sofia/proxies/PROXY_SCORER_README.md` - Full documentation
5. `/home/wow/Projects/sale-sofia/run_proxy_scorer_tests.sh` - Test runner script

## Integration Options

### Option 1: Replace Mubeng Completely (Recommended for Testing)

Replace the random rotation with weighted scoring:

```python
# In main.py or your scraper
from proxies.proxy_scorer import ScoredProxyPool
from paths import PROXIES_DIR

# Initialize pool
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

# For each page to scrape
for url in urls:
    proxy_url = pool.get_proxy_url()

    try:
        # Use proxy with browser
        browser = await create_instance(proxy=proxy_url)
        await browser.goto(url)
        # ... scraping logic ...

        # Record success
        pool.record_result(proxy_url, success=True)

    except Exception as e:
        # Record failure
        pool.record_result(proxy_url, success=False)

        # Optionally retry with different proxy
        proxy_url = pool.get_proxy_url()
        # ... retry logic ...
```

### Option 2: Hybrid - Feed Top Proxies to Mubeng (Recommended for Production)

Use scorer to filter best proxies, then let mubeng rotate:

```python
# In proxies/proxies_main.py
from proxies.proxy_scorer import ScoredProxyPool
from paths import PROXIES_DIR
import tempfile

def setup_mubeng_with_scoring(port: int = 8089) -> tuple:
    """Setup mubeng with top-scored proxies."""

    # Load scorer
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

    # Get top 30 proxies by score
    proxies_with_scores = [
        (p, pool.scores.get(pool._get_proxy_key(p), {}).get("score", 0))
        for p in pool.proxies
    ]
    top_proxies = sorted(proxies_with_scores, key=lambda x: x[1], reverse=True)[:30]

    logger.info(f"Selected top {len(top_proxies)} proxies for mubeng")
    for proxy, score in top_proxies[:5]:
        logger.info(f"  {proxy['host']}:{proxy['port']} - score: {score:.3f}")

    # Write to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    for proxy, _ in top_proxies:
        line = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}\n"
        temp_file.write(line)
    temp_file.close()

    # Start mubeng with top proxies
    cmd = ["mubeng", "-a", f"localhost:{port}", "-f", temp_file.name, "--rotate", "1"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return process, temp_file.name, pool
```

### Option 3: Monitoring Only (Safest)

Keep existing setup, just track performance:

```python
# In your existing scraper
from proxies.proxy_scorer import ScoredProxyPool
from paths import PROXIES_DIR

# Initialize once at startup
pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

# Keep your existing mubeng setup unchanged
# ...existing code...

# After scraping, record results for monitoring
# (This requires tracking which proxy was actually used)
def record_scraping_result(proxy_used: str, success: bool):
    """Optional: track proxy performance for future optimization."""
    pool.record_result(proxy_used, success=success)

# Periodically check stats
if scrape_count % 100 == 0:
    stats = pool.get_stats()
    logger.info(f"Proxy pool stats: {stats}")
```

## Integration with Orchestrator

Add scorer to the orchestrator lifecycle:

```python
# In orchestrator.py
from proxies.proxy_scorer import ScoredProxyPool

class Orchestrator:
    def __init__(self):
        # ... existing code ...
        self.proxy_pool = None

    def setup_proxy_scorer(self):
        """Initialize the proxy scorer."""
        self.proxy_pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")
        logger.info(f"Proxy scorer initialized with {len(self.proxy_pool.proxies)} proxies")
        return self.proxy_pool

    def reload_proxy_scores(self):
        """Reload proxies after Celery refresh."""
        if self.proxy_pool:
            self.proxy_pool.reload_proxies()
            logger.info(f"Reloaded proxy pool: {len(self.proxy_pool.proxies)} proxies")
```

## Testing

Run the unit tests to verify everything works:

```bash
# Make script executable
chmod +x /home/wow/Projects/sale-sofia/run_proxy_scorer_tests.sh

# Run tests
./run_proxy_scorer_tests.sh

# Or directly with pytest
python -m pytest tests/test_proxy_scorer.py -v
```

Expected output:
```
test_proxy_scorer.py::TestProxyPoolInitialization::test_load_proxies PASSED
test_proxy_scorer.py::TestProxyPoolInitialization::test_initialize_scores PASSED
test_proxy_scorer.py::TestProxySelection::test_select_proxy PASSED
test_proxy_scorer.py::TestProxySelection::test_select_proxy_weighted PASSED
test_proxy_scorer.py::TestScoreUpdates::test_record_success PASSED
test_proxy_scorer.py::TestScoreUpdates::test_record_failure PASSED
test_proxy_scorer.py::TestAutoPruning::test_auto_prune_on_max_failures PASSED
... (32 tests total)
```

## Example: Quick Test

Try it out with the example script:

```bash
cd /home/wow/Projects/sale-sofia
python proxies/proxy_scorer_example.py
```

This will:
1. Load proxies from live_proxies.json
2. Show pool statistics
3. Demonstrate selection and scoring
4. Show how to reload proxies

## Monitoring Dashboard Integration

Add proxy scorer stats to your Streamlit dashboard:

```python
# In app/streamlit_app.py or app/pages/dashboard.py
from proxies.proxy_scorer import ScoredProxyPool
from paths import PROXIES_DIR

def show_proxy_stats():
    """Display proxy scorer statistics."""
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")
    stats = pool.get_stats()

    st.subheader("Proxy Pool Statistics")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Proxies", stats['total_proxies'])

    with col2:
        st.metric("Average Score", f"{stats['average_score']:.2f}")

    with col3:
        st.metric("Failing Proxies", stats['proxies_with_failures'])

    # Show top proxies
    if st.checkbox("Show Top Proxies"):
        proxies_with_scores = [
            {
                "proxy": pool._get_proxy_key(p),
                "score": pool.scores.get(pool._get_proxy_key(p), {}).get("score", 0),
                "failures": pool.scores.get(pool._get_proxy_key(p), {}).get("failures", 0),
            }
            for p in pool.proxies
        ]
        df = pd.DataFrame(proxies_with_scores)
        df = df.sort_values("score", ascending=False).head(10)
        st.dataframe(df)
```

## Recommended Next Steps

1. **Test in isolation**: Run `python proxies/proxy_scorer_example.py`
2. **Run unit tests**: `./run_proxy_scorer_tests.sh`
3. **Add to one scraper**: Try Option 1 with a single website scraper
4. **Monitor results**: Check `proxies/proxy_scores.json` after scraping
5. **Scale up**: If successful, integrate with orchestrator (Option 2)
6. **Add dashboard**: Show proxy stats in Streamlit

## Troubleshooting

### Import Error

If you get `ModuleNotFoundError`, make sure you're in the project directory:

```bash
cd /home/wow/Projects/sale-sofia
python -c "from proxies.proxy_scorer import ScoredProxyPool; print('OK')"
```

### No Proxies Available

If `pool.get_proxy_url()` returns `None`:

```python
# Check if file exists
print(pool.proxies_file.exists())  # Should be True

# Check proxy count
print(len(pool.proxies))  # Should be > 0

# Reload from file
pool.reload_proxies()
```

### Scores Not Persisting

Check file permissions:

```bash
ls -la /home/wow/Projects/sale-sofia/proxies/proxy_scores.json
```

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

The scorer is lightweight:

- **Selection**: O(n) where n = number of proxies (typically < 100)
- **Update**: O(1) with file I/O
- **Memory**: ~1KB per proxy (negligible)
- **Thread-safe**: Uses locks but minimal contention

Safe to use in production without performance concerns.

## Migration Path

If you want to migrate from current mubeng-only setup:

1. **Week 1**: Add scorer in monitoring mode (Option 3)
   - Track proxy performance without changing behavior
   - Analyze scores to identify bad proxies

2. **Week 2**: Test hybrid mode (Option 2)
   - Feed top-scored proxies to mubeng
   - Compare performance vs. random selection

3. **Week 3**: Decide on long-term approach
   - If hybrid works well, keep it
   - If scores show clear winners, consider Option 1

## Questions?

See full documentation in:
- `/home/wow/Projects/sale-sofia/proxies/PROXY_SCORER_README.md` - Complete guide
- `/home/wow/Projects/sale-sofia/docs/PROXY_SYSTEM_SPECS.md` - Design specs (section 10.7)
- `/home/wow/Projects/sale-sofia/proxies/proxy_scorer_example.py` - Code examples
