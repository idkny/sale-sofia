"""
Example usage of ScoredProxyPool for runtime proxy scoring.

This demonstrates how to integrate the scorer into your scraping workflow.
"""

import logging
from pathlib import Path

from proxies.proxy_scorer import ScoredProxyPool
from paths import PROXIES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Example workflow using scored proxy pool."""

    # Initialize the pool
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

    logger.info(f"Initialized pool with {len(pool.proxies)} proxies")
    logger.info(f"Pool stats: {pool.get_stats()}")

    # Example 1: Simple selection and usage
    print("\n--- Example 1: Basic Usage ---")
    proxy_url = pool.get_proxy_url()
    if proxy_url:
        print(f"Selected proxy: {proxy_url}")

        # Simulate using the proxy
        try:
            # ... your scraping code here ...
            # If successful:
            pool.record_result(proxy_url, success=True)
            print("Recorded success")
        except Exception as e:
            # If failed:
            pool.record_result(proxy_url, success=False)
            print(f"Recorded failure: {e}")

    # Example 2: Multiple requests with scoring
    print("\n--- Example 2: Multiple Requests ---")
    for i in range(5):
        proxy = pool.select_proxy()
        if not proxy:
            print("No proxies available")
            break

        proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
        print(f"Request {i+1}: Using {proxy_url}")

        # Simulate success/failure (50/50 for demo)
        success = i % 2 == 0
        pool.record_result(proxy_url, success=success)
        print(f"  -> {'Success' if success else 'Failure'}")

    # Example 3: Check statistics
    print("\n--- Example 3: Pool Statistics ---")
    stats = pool.get_stats()
    print(f"Total proxies: {stats['total_proxies']}")
    print(f"Average score: {stats['average_score']:.3f}")
    print(f"Proxies with failures: {stats['proxies_with_failures']}")

    # Example 4: Reload proxies after Celery refresh
    print("\n--- Example 4: Reloading Proxies ---")
    print("(Simulating after Celery task refreshed live_proxies.json)")
    pool.reload_proxies()
    print(f"Pool now has {len(pool.proxies)} proxies")


def integration_with_browser():
    """
    Example integration with browser automation.

    This shows how to use the scorer in a real scraping scenario.
    """
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

    # Get a proxy for the browser
    proxy = pool.select_proxy()
    if not proxy:
        logger.error("No proxies available")
        return

    proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"

    try:
        # Initialize browser with proxy
        # browser = await create_instance(proxy=proxy_url)

        # Perform scraping
        # await browser.goto("https://example.com")
        # ... scraping logic ...

        # Record success
        pool.record_result(proxy_url, success=True)
        logger.info(f"Successfully used proxy {proxy_url}")

    except Exception as e:
        # Record failure
        pool.record_result(proxy_url, success=False)
        logger.error(f"Proxy {proxy_url} failed: {e}")

        # Try with a different proxy
        proxy = pool.select_proxy()
        if proxy:
            logger.info(f"Retrying with {proxy['host']}:{proxy['port']}")
            # ... retry logic ...


def integration_with_mubeng_rotator():
    """
    Example integration alongside mubeng rotator.

    The scorer tracks individual proxy performance while mubeng
    handles rotation at runtime.
    """
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

    # Option 1: Use top-scored proxies with mubeng
    # Select top 10 proxies by score and create a temp file for mubeng
    proxies_with_scores = [
        (pool._get_proxy_key(p), pool.scores.get(pool._get_proxy_key(p), {}).get("score", 0))
        for p in pool.proxies
    ]
    top_proxies = sorted(proxies_with_scores, key=lambda x: x[1], reverse=True)[:10]

    print("Top 10 proxies by score:")
    for proxy_key, score in top_proxies:
        print(f"  {proxy_key}: {score:.3f}")

    # Write to temp file for mubeng
    # with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
    #     for proxy in pool.proxies:
    #         key = pool._get_proxy_key(proxy)
    #         if key in [p[0] for p in top_proxies]:
    #             f.write(f"{proxy['protocol']}://{key}\n")
    #     temp_file = f.name
    #
    # # Start mubeng with top proxies
    # subprocess.Popen(["mubeng", "-a", "localhost:8089", "-f", temp_file])


if __name__ == "__main__":
    main()
