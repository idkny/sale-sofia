#!/usr/bin/env python3
"""
Sofia Real Estate Scraper - Automated apartment scraper for Bulgarian RE sites.

Usage:
    python main.py

Starts the full automated scraping pipeline:
1. Starts Redis & Celery
2. Waits for proxies (auto-refreshes if needed)
3. Starts proxy rotator
4. Crawls all configured start URLs from config/start_urls.yaml
"""

import asyncio
import time
from typing import Any, Optional

from dotenv import load_dotenv
from loguru import logger

from scrapling.fetchers import Fetcher, StealthyFetcher

from data import data_store_main
from paths import LOGS_DIR, PROXIES_DIR
from proxies.proxies_main import (
    setup_mubeng_rotator,
    stop_mubeng_rotator,
)
from proxies.proxy_scorer import ScoredProxyPool
from proxies.proxy_validator import preflight_check
from utils.log_config import setup_logging

# Default mubeng proxy endpoint - ALWAYS use proxy for scraping
MUBENG_PROXY = "http://localhost:8089"

# Maximum retries per URL when proxy fails
MAX_PROXY_RETRIES = 3

# Minimum proxies before triggering refresh
MIN_PROXIES = 5


async def _collect_listing_urls(
    scraper,
    start_url: str,
    limit: int,
    delay: float,
    proxy: str | None,
    proxy_pool: Optional[ScoredProxyPool]
) -> list[str]:
    """
    Phase 1: Collect listing URLs from search pages with pagination.

    Uses Fetcher (fast HTTP) for search pages - no JS needed.

    Returns:
        List of listing URLs found (up to limit).
    """
    current_url = start_url
    current_page = 1
    all_listing_urls = []

    while len(all_listing_urls) < limit:
        logger.info(f"[Page {current_page}] Loading: {current_url}")

        # Retry loop for proxy failures
        page_success = False
        html = None
        for attempt in range(MAX_PROXY_RETRIES):
            # Select specific proxy for this attempt (Solution F - X-Proxy-Offset)
            proxy_key = None
            headers = {}
            if proxy_pool:
                proxy_dict = proxy_pool.select_proxy()
                if proxy_dict:
                    proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"
                    index = proxy_pool.get_proxy_index(proxy_key)
                    if index is not None:
                        headers = {"X-Proxy-Offset": str(index)}

            try:
                # Use fast Fetcher for search pages (no JS needed)
                response = Fetcher.get(
                    url=current_url,
                    proxy=proxy or MUBENG_PROXY,
                    timeout=15,  # Fetcher.get uses seconds, not milliseconds
                    headers=headers
                )
                html = response.html_content
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=True)
                page_success = True
                break  # Exit retry loop on success

            except Exception as e:
                logger.warning(f"  -> Page attempt {attempt + 1}/{MAX_PROXY_RETRIES} failed: {e}")
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=False)
                # Continue to next attempt (try different proxy)

        if not page_success:
            logger.error(f"All {MAX_PROXY_RETRIES} attempts failed for page {current_page}")
            break  # Stop pagination on failure

        # Check if this is the last page
        if hasattr(scraper, "is_last_page") and scraper.is_last_page(html, current_page):
            logger.info(f"Last page detected at page {current_page}")
            listing_urls = await scraper.extract_search_results(html)
            if listing_urls:
                new_urls = [u for u in listing_urls if u not in all_listing_urls]
                all_listing_urls.extend(new_urls)
                logger.info(f"Found {len(new_urls)} new listings on last page (total: {len(all_listing_urls)})")
            break

        listing_urls = await scraper.extract_search_results(html)
        if not listing_urls:
            logger.info(f"No more listings found on page {current_page}")
            break

        new_urls = [u for u in listing_urls if u not in all_listing_urls]
        all_listing_urls.extend(new_urls)
        logger.info(f"Found {len(new_urls)} new listings (total: {len(all_listing_urls)})")

        if len(all_listing_urls) >= limit:
            break

        # Get next page URL
        if hasattr(scraper, "get_next_page_url"):
            current_url = scraper.get_next_page_url(current_url, current_page)
            current_page += 1
        else:
            break

        time.sleep(delay)

    return all_listing_urls[:limit]


async def _scrape_listings(
    scraper,
    urls: list[str],
    delay: float,
    proxy: str | None,
    proxy_pool: Optional[ScoredProxyPool]
) -> dict:
    """
    Phase 2: Scrape individual listings from collected URLs.

    Uses StealthyFetcher for listing pages - anti-bot protection.

    Returns:
        Dictionary with stats: {scraped: int, failed: int, total_attempts: int}
    """
    stats = {"scraped": 0, "failed": 0, "total_attempts": 0}

    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] {url}")
        stats["total_attempts"] += 1

        url_result = None  # None=pending, True=success, False=failed
        for attempt in range(MAX_PROXY_RETRIES):
            # Select specific proxy for this attempt (Solution F - X-Proxy-Offset)
            proxy_key = None
            extra_headers = {}
            if proxy_pool:
                proxy_dict = proxy_pool.select_proxy()
                if proxy_dict:
                    proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"
                    index = proxy_pool.get_proxy_index(proxy_key)
                    if index is not None:
                        extra_headers = {"X-Proxy-Offset": str(index)}

            try:
                # Use StealthyFetcher for listings (anti-bot bypass)
                response = StealthyFetcher.fetch(
                    url=url,
                    proxy=proxy or MUBENG_PROXY,
                    extra_headers=extra_headers,
                    humanize=True,
                    block_webrtc=True,
                    network_idle=True,
                    timeout=30000
                )
                html = response.html_content

                # If we get here, request succeeded
                listing = await scraper.extract_listing(html, url)
                if listing:
                    data_store_main.save_listing(listing)
                    stats["scraped"] += 1
                    logger.info(f"  -> Saved: {listing.price_eur} EUR, {listing.sqm_total} sqm")
                    if proxy_pool and proxy_key:
                        proxy_pool.record_result(proxy_key, success=True)
                    url_result = True
                    break  # Exit retry loop on success
                else:
                    # Extraction failed but request succeeded - don't retry
                    stats["failed"] += 1
                    logger.warning(f"  -> Failed to extract listing data")
                    if proxy_pool and proxy_key:
                        proxy_pool.record_result(proxy_key, success=False)
                    url_result = False
                    break  # Don't retry extraction failures

            except Exception as e:
                logger.warning(f"  -> Attempt {attempt + 1}/{MAX_PROXY_RETRIES} failed: {e}")
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=False)
                # Continue to next attempt (try different proxy)

        # All retries exhausted without success or explicit failure
        if url_result is None:
            stats["failed"] += 1
            logger.error(f"  -> All {MAX_PROXY_RETRIES} proxy attempts failed for {url}")

        time.sleep(delay)

    return stats


async def scrape_from_start_url(
    scraper,
    start_url: str,
    limit: int,
    delay: float = 6.0,
    proxy: str | None = None,
    proxy_pool: Optional[ScoredProxyPool] = None
) -> dict:
    """
    Scrape all listings from a starting URL with pagination support.

    Args:
        scraper: The site-specific scraper instance.
        start_url: Search results page URL to start from.
        limit: Maximum number of listings to scrape.
        delay: Seconds to wait between requests (default: 6.0).
        proxy: The proxy server URL (e.g., "http://localhost:8089"). Should always be set.
        proxy_pool: Optional ScoredProxyPool for tracking proxy performance.

    Returns:
        Dictionary with stats: {scraped: int, failed: int, total_attempts: int}
    """
    logger.info(f"Starting crawl from: {start_url}")
    logger.info(f"Rate limit: {60/delay:.1f} URLs/min ({delay} sec delay)")
    logger.info(f"Target: {limit} listings")
    effective_proxy = proxy or MUBENG_PROXY
    logger.info(f"Using proxy: {effective_proxy}")

    # Phase 1: Collect listing URLs from search pages
    urls = await _collect_listing_urls(scraper, start_url, limit, delay, proxy, proxy_pool)
    logger.info(f"Collected {len(urls)} listing URLs to scrape")

    # Phase 2: Scrape individual listings
    stats = await _scrape_listings(scraper, urls, delay, proxy, proxy_pool)
    logger.info(f"Scraping complete. Saved {stats['scraped']}/{len(urls)} listings.")

    return stats


def _print_banner() -> None:
    """Print startup banner."""
    print("=" * 60)
    print("SOFIA REAL ESTATE SCRAPER - AUTO MODE")
    print("=" * 60)
    print()


def _load_start_urls() -> dict | None:
    """Load and validate start URLs from config."""
    from config.loader import get_start_urls

    start_urls = get_start_urls()
    if not start_urls:
        print("[ERROR] No start URLs configured!")
        print("[HINT] Add URLs to config/start_urls.yaml")
        return None

    total_urls = sum(len(urls) for urls in start_urls.values())
    print(f"[INFO] Found {total_urls} start URLs across {len(start_urls)} sites")
    print()
    return start_urls


def _setup_infrastructure(orch) -> bool:
    """Start Redis and Celery, wait for proxies. Returns True if successful."""
    # 1. Start Redis
    if not orch.start_redis():
        print("[ERROR] Failed to start Redis. Aborting.")
        return False

    # 2. Start Celery
    if not orch.start_celery():
        print("[ERROR] Failed to start Celery. Aborting.")
        return False

    # 3. Wait for proxies
    print()
    print("[INFO] Checking proxy availability...")
    if not orch.wait_for_proxies(min_count=5, timeout=600):
        print("[ERROR] Could not get proxies. Aborting.")
        return False

    return True


def _initialize_proxy_pool() -> Optional[ScoredProxyPool]:
    """Initialize proxy scoring pool. Returns pool or None if failed."""
    print("[INFO] Initializing proxy scoring system...")
    try:
        proxy_pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")
        stats = proxy_pool.get_stats()
        print(f"[SUCCESS] Proxy pool initialized: {stats['total_proxies']} proxies, "
              f"avg score: {stats['average_score']:.2f}")
        return proxy_pool
    except Exception as e:
        logger.warning(f"Failed to initialize proxy pool: {e}")
        print(f"[WARNING] Proxy scoring disabled: {e}")
        return None


def _start_proxy_rotator() -> tuple[str, Any, Any, list[str]]:
    """Start mubeng proxy rotator. Returns (proxy_url, process, temp_file, ordered_proxy_keys)."""
    print()
    print("[INFO] Starting proxy rotator...")
    proxy_url, mubeng_process, temp_proxy_file, ordered_proxy_keys = setup_mubeng_rotator(
        port=8089,
        min_live_proxies=5,
    )

    if not mubeng_process:
        print("[ERROR] Failed to start proxy rotator. Aborting.")
        return proxy_url, mubeng_process, temp_proxy_file, ordered_proxy_keys

    print(f"[SUCCESS] Proxy rotator running at {proxy_url} with {len(ordered_proxy_keys)} proxies")
    return proxy_url, mubeng_process, temp_proxy_file, ordered_proxy_keys


def _run_preflight_level1(proxy_url: str, max_attempts: int = 6) -> bool:
    """
    Level 1 pre-flight: Try with mubeng auto-rotation.
    Mubeng rotates on error, so more attempts = more proxies tested.
    """
    print("[INFO] Running pre-flight proxy check...")
    for attempt in range(1, max_attempts + 1):
        if preflight_check(proxy_url, timeout=15):
            print(f"[SUCCESS] Pre-flight check passed (attempt {attempt})")
            return True
        else:
            print(f"[WARNING] Pre-flight check failed (attempt {attempt}/{max_attempts})")
            if attempt < max_attempts:
                time.sleep(1)  # Short delay, mubeng auto-rotates
    return False


def _run_preflight_level2(mubeng_process: Any) -> tuple[bool, Any, str, Any, list[str]]:
    """
    Level 2 pre-flight: Soft restart - reload mubeng with same proxy file.
    Returns (success, new_process, new_proxy_url, new_temp_file, ordered_proxy_keys).
    """
    print()
    print("[INFO] Soft restart: Reloading proxy rotator...")
    stop_mubeng_rotator(mubeng_process, None)  # Don't delete temp file

    proxy_url, new_process, new_temp_file, ordered_proxy_keys = setup_mubeng_rotator(
        port=8089,
        min_live_proxies=5,
    )
    if not new_process:
        return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys

    print(f"[SUCCESS] Proxy rotator restarted at {proxy_url}")
    for attempt in range(1, 4):
        if preflight_check(proxy_url, timeout=15):
            print(f"[SUCCESS] Pre-flight check passed after soft restart (attempt {attempt})")
            return True, new_process, proxy_url, new_temp_file, ordered_proxy_keys
        else:
            print(f"[WARNING] Pre-flight still failing (attempt {attempt}/3)")
            if attempt < 3:
                time.sleep(1)

    return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys


def _run_preflight_level3(orch, proxy_pool: Optional[ScoredProxyPool]) -> tuple[bool, Any, str, Any, list[str]]:
    """
    Level 3 pre-flight: Full refresh - scrape new proxies (5-10 min).
    Returns (success, new_process, new_proxy_url, new_temp_file, ordered_proxy_keys).
    """
    print()
    print("[INFO] Full refresh: Fetching new proxies (this takes 5-10 min)...")

    mtime_before, task_id = orch.trigger_proxy_refresh()
    if not orch.wait_for_refresh_completion(mtime_before, min_count=5, task_id=task_id):
        print("[ERROR] Proxy refresh timed out or failed. Aborting.", flush=True)
        return False, None, "", None, []

    print("[DEBUG] wait_for_refresh_completion returned True, continuing...", flush=True)

    # Reload proxy pool after refresh
    if proxy_pool:
        print("[INFO] Reloading proxy pool after refresh...", flush=True)
        proxy_pool.reload_proxies()
        stats = proxy_pool.get_stats()
        print(f"[SUCCESS] Proxy pool reloaded: {stats['total_proxies']} proxies")

    print("[INFO] Restarting proxy rotator with fresh proxies...")
    proxy_url, new_process, new_temp_file, ordered_proxy_keys = setup_mubeng_rotator(
        port=8089,
        min_live_proxies=5,
    )
    if not new_process:
        print("[ERROR] Failed to restart proxy rotator. Aborting.")
        return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys
    print(f"[SUCCESS] Proxy rotator restarted at {proxy_url}")

    # Final pre-flight check
    for attempt in range(1, 4):
        if preflight_check(proxy_url, timeout=15):
            print(f"[SUCCESS] Pre-flight check passed after refresh (attempt {attempt})")
            return True, new_process, proxy_url, new_temp_file, ordered_proxy_keys
        else:
            print(f"[WARNING] Pre-flight still failing (attempt {attempt}/3)")
            if attempt < 3:
                time.sleep(1)

    return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys


def _ensure_min_proxies(
    proxy_pool: Optional[ScoredProxyPool],
    orch,
    min_count: int = MIN_PROXIES
) -> bool:
    """
    Check proxy count and trigger refresh if below threshold.

    Returns True if we have enough proxies, False if refresh failed.
    """
    if not proxy_pool:
        return True  # No pool, skip check

    stats = proxy_pool.get_stats()
    current_count = stats['total_proxies']

    if current_count >= min_count:
        return True  # Enough proxies

    logger.warning(
        f"Proxy count low ({current_count} < {min_count}), triggering refresh..."
    )
    print(f"[WARNING] Proxy count low ({current_count} < {min_count}), refreshing...")

    mtime_before, task_id = orch.trigger_proxy_refresh()
    refresh_ok = orch.wait_for_refresh_completion(
        mtime_before, min_count=min_count, task_id=task_id
    )
    if not refresh_ok:
        logger.error("Proxy refresh failed during MIN_PROXIES check")
        return False

    # Reload proxy pool after refresh
    proxy_pool.reload_proxies()
    new_stats = proxy_pool.get_stats()
    logger.info(f"Proxy pool reloaded: {new_stats['total_proxies']} proxies")
    print(f"[SUCCESS] Proxy pool reloaded: {new_stats['total_proxies']} proxies")

    return True


def _crawl_all_sites(
    start_urls: dict,
    proxy_url: str,
    proxy_pool: Optional[ScoredProxyPool],
    orch
) -> dict:
    """Crawl all configured sites. Returns aggregated stats."""
    from config.loader import get_site_config
    from websites import get_scraper

    print()
    print("=" * 60)
    print("STARTING CRAWL")
    print("=" * 60)

    total_stats = {"scraped": 0, "failed": 0, "total_attempts": 0}

    # Check proxy count before starting
    if not _ensure_min_proxies(proxy_pool, orch):
        logger.error("Failed to ensure minimum proxies before crawl")
        return total_stats

    for site, urls in start_urls.items():
        scraper = get_scraper(site)
        if not scraper:
            print(f"[WARNING] Scraper for {site} not implemented, skipping")
            continue

        # Load per-site configuration
        site_config = get_site_config(site)
        print(f"\n[SITE] {site} ({len(urls)} start URLs)")
        print(f"[CONFIG] limit={site_config.limit}, delay={site_config.delay}s, timeout={site_config.timeout}s")

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] {url}")
            try:
                stats = asyncio.run(
                    scrape_from_start_url(
                        scraper,
                        url,
                        limit=site_config.limit,
                        delay=site_config.delay,
                        proxy=proxy_url,
                        proxy_pool=proxy_pool
                    )
                )
                # Aggregate stats
                total_stats["scraped"] += stats["scraped"]
                total_stats["failed"] += stats["failed"]
                total_stats["total_attempts"] += stats["total_attempts"]
                print(f"[STATS] Scraped: {stats['scraped']}, Failed: {stats['failed']}")
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                print(f"[ERROR] Failed to crawl {url}: {e}")
                continue

        # Check proxy count after each site
        if not _ensure_min_proxies(proxy_pool, orch):
            logger.error("Failed to ensure minimum proxies between sites")
            return total_stats

    return total_stats


def _print_summary(stats: dict, proxy_pool: Optional[ScoredProxyPool]) -> None:
    """Print final crawl summary and save proxy scores."""
    print()
    print("=" * 60)
    print("CRAWL COMPLETE")
    print("=" * 60)
    print(f"\n[SUMMARY] Total scraped: {stats['scraped']}, "
          f"Failed: {stats['failed']}, "
          f"Success rate: {stats['scraped'] / max(stats['total_attempts'], 1) * 100:.1f}%")

    # Save final proxy scores
    if proxy_pool:
        print("\n[INFO] Saving final proxy scores...")
        proxy_pool.save_scores()
        stats_pool = proxy_pool.get_stats()
        print(f"[SUCCESS] Final proxy stats: {stats_pool['total_proxies']} proxies, "
              f"avg score: {stats_pool['average_score']:.2f}")


def run_auto_mode() -> None:
    """
    Run automated scraping mode.

    Starts Redis, Celery, waits for proxies, and crawls all configured start URLs.
    Uses ScoredProxyPool to track proxy performance during scraping.
    """
    from orchestrator import Orchestrator

    _print_banner()

    start_urls = _load_start_urls()
    if not start_urls:
        return

    with Orchestrator() as orch:
        if not _setup_infrastructure(orch):
            return

        proxy_pool = _initialize_proxy_pool()
        proxy_url, mubeng_process, temp_proxy_file, ordered_proxy_keys = _start_proxy_rotator()
        if not mubeng_process:
            return

        # Set proxy order in pool for X-Proxy-Offset mapping (Solution F)
        if proxy_pool and ordered_proxy_keys:
            proxy_pool.set_proxy_order(ordered_proxy_keys)
            if temp_proxy_file:
                proxy_pool.set_mubeng_proxy_file(temp_proxy_file)

        # Pre-flight with 3-level recovery
        preflight_passed = _run_preflight_level1(proxy_url)

        if not preflight_passed:
            preflight_passed, mubeng_process, proxy_url, temp_proxy_file, ordered_proxy_keys = _run_preflight_level2(mubeng_process)
            if proxy_pool and ordered_proxy_keys:
                proxy_pool.set_proxy_order(ordered_proxy_keys)
                if temp_proxy_file:
                    proxy_pool.set_mubeng_proxy_file(temp_proxy_file)

        if not preflight_passed:
            result = _run_preflight_level3(orch, proxy_pool)
            preflight_passed, mubeng_process, proxy_url, temp_proxy_file, ordered_proxy_keys = result
            if proxy_pool and ordered_proxy_keys:
                proxy_pool.set_proxy_order(ordered_proxy_keys)
                if temp_proxy_file:
                    proxy_pool.set_mubeng_proxy_file(temp_proxy_file)

        if not preflight_passed:
            print("[ERROR] Pre-flight failed after all recovery attempts.")
            stop_mubeng_rotator(mubeng_process, temp_proxy_file)
            return

        try:
            stats = _crawl_all_sites(start_urls, proxy_url, proxy_pool, orch)
            _print_summary(stats, proxy_pool)
        finally:
            print()
            print("[INFO] Stopping proxy rotator...")
            stop_mubeng_rotator(mubeng_process, temp_proxy_file)

    print("[INFO] All processes stopped. Goodbye!")


def main() -> None:
    """Main entry point for Sofia Real Estate Scraper."""
    load_dotenv()
    setup_logging(LOGS_DIR)
    run_auto_mode()


if __name__ == "__main__":
    main()
