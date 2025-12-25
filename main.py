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

from browsers.browsers_main import create_instance
from data import data_store_main
from paths import LOGS_DIR, PROXIES_DIR
from proxies.proxies_main import (
    setup_mubeng_rotator,
    stop_mubeng_rotator,
)
from proxies.proxy_scorer import ScoredProxyPool
from proxies.proxy_validator import preflight_check
from utils.log_config import setup_logging


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
    if proxy:
        logger.info(f"Using proxy: {proxy}")

    stats = {"scraped": 0, "failed": 0, "total_attempts": 0}

    browser_handle = await create_instance(browser_type="chromiumstealth", proxy=proxy)
    if not browser_handle:
        logger.error("Failed to initialize browser")
        return stats

    try:
        page = await browser_handle.new_tab()
        current_url = start_url
        current_page = 1
        all_listing_urls = []

        # Phase 1: Collect listing URLs from search pages (with pagination)
        while len(all_listing_urls) < limit:
            logger.info(f"[Page {current_page}] Loading: {current_url}")

            try:
                await page.goto(current_url, wait_until="domcontentloaded")
                html = await page.content()

                # Check if this is the last page using scraper's detection method
                if hasattr(scraper, "is_last_page") and scraper.is_last_page(html, current_page):
                    logger.info(f"Last page detected at page {current_page}")
                    # Still extract listings from this page before stopping
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

            except Exception as e:
                logger.error(f"Error loading search page {current_page}: {e}")
                # Record failure for mubeng rotator (it will auto-rotate)
                if proxy_pool and proxy:
                    proxy_pool.record_result(proxy, success=False)
                break

            if len(all_listing_urls) >= limit:
                break

            # Get next page URL
            if hasattr(scraper, "get_next_page_url"):
                current_url = scraper.get_next_page_url(current_url, current_page)
                current_page += 1
            else:
                break  # No pagination support

            # Rate limit between page loads
            await asyncio.sleep(delay)

        # Trim to limit
        urls_to_scrape = all_listing_urls[:limit]
        logger.info(f"Collected {len(urls_to_scrape)} listing URLs to scrape")

        # Phase 2: Scrape each listing
        for i, url in enumerate(urls_to_scrape, 1):
            logger.info(f"[{i}/{len(urls_to_scrape)}] {url}")
            stats["total_attempts"] += 1

            try:
                await page.goto(url, wait_until="domcontentloaded")
                html = await page.content()

                listing = await scraper.extract_listing(html, url)
                if listing:
                    data_store_main.save_listing(listing)
                    stats["scraped"] += 1
                    logger.info(f"  -> Saved: {listing.price_eur} EUR, {listing.sqm_total} sqm")

                    # Record success for mubeng rotator
                    if proxy_pool and proxy:
                        proxy_pool.record_result(proxy, success=True)
                else:
                    stats["failed"] += 1
                    logger.warning(f"  -> Failed to extract listing data")

                    # Record failure for mubeng rotator
                    if proxy_pool and proxy:
                        proxy_pool.record_result(proxy, success=False)

            except Exception as e:
                stats["failed"] += 1
                logger.error(f"Error scraping {url}: {e}")

                # Record failure for mubeng rotator (it will auto-rotate)
                if proxy_pool and proxy:
                    proxy_pool.record_result(proxy, success=False)

                continue

            # Rate limit between listing scrapes
            await asyncio.sleep(delay)

        logger.info(f"Scraping complete. Saved {stats['scraped']}/{len(urls_to_scrape)} listings.")

    finally:
        await browser_handle._browser.close()

    return stats


async def cleanup_browser(browser_instance: Optional[Any], browser_type: str) -> None:
    """Clean up browser resources."""
    if browser_instance:
        logger.info(f"Cleaning up browser connection for '{browser_type}'.")
        try:
            if browser_type == "my_browser_gui":
                await browser_instance.disconnect()
            else:
                await browser_instance.close()
        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")


def run_auto_mode() -> None:
    """
    Run automated scraping mode.

    Starts Redis, Celery, waits for proxies, and crawls all configured start URLs.
    Uses ScoredProxyPool to track proxy performance during scraping.
    """
    from config.loader import get_site_config, get_start_urls
    from orchestrator import Orchestrator
    from websites import get_scraper

    print("=" * 60)
    print("SOFIA REAL ESTATE SCRAPER - AUTO MODE")
    print("=" * 60)
    print()

    # Load start URLs first to validate config
    start_urls = get_start_urls()
    if not start_urls:
        print("[ERROR] No start URLs configured!")
        print("[HINT] Add URLs to config/start_urls.yaml")
        return

    total_urls = sum(len(urls) for urls in start_urls.values())
    print(f"[INFO] Found {total_urls} start URLs across {len(start_urls)} sites")
    print()

    # Initialize proxy pool for scoring (will be loaded after proxies are available)
    proxy_pool: Optional[ScoredProxyPool] = None

    with Orchestrator() as orch:
        # 1. Start Redis
        if not orch.start_redis():
            print("[ERROR] Failed to start Redis. Aborting.")
            return

        # 2. Start Celery
        if not orch.start_celery():
            print("[ERROR] Failed to start Celery. Aborting.")
            return

        # 3. Wait for proxies
        print()
        print("[INFO] Checking proxy availability...")
        if not orch.wait_for_proxies(min_count=5, timeout=600):
            print("[ERROR] Could not get proxies. Aborting.")
            return

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

        # 4. Set up proxy rotator
        print()
        print("[INFO] Starting proxy rotator...")
        proxy_url, mubeng_process, temp_proxy_file = setup_mubeng_rotator(
            port=8089,
            min_live_proxies=5,
        )

        if not mubeng_process:
            print("[ERROR] Failed to start proxy rotator. Aborting.")
            return

        print(f"[SUCCESS] Proxy rotator running at {proxy_url}")

        # Pre-flight check with tiered recovery:
        # Level 1: Let mubeng auto-rotate (more attempts)
        # Level 2: Soft restart mubeng (reload same proxy file)
        # Level 3: Full proxy refresh (scrape + check, 5-10 min)
        preflight_passed = False

        # Level 1: Try pre-flight with mubeng auto-rotation (up to 6 attempts)
        # Mubeng rotates on error, so more attempts = more proxies tested
        print("[INFO] Running pre-flight proxy check...")
        for attempt in range(1, 7):
            if preflight_check(proxy_url, timeout=15):
                print(f"[SUCCESS] Pre-flight check passed (attempt {attempt})")
                preflight_passed = True
                break
            else:
                print(f"[WARNING] Pre-flight check failed (attempt {attempt}/6)")
                if attempt < 6:
                    time.sleep(1)  # Short delay, mubeng auto-rotates

        # Level 2: Soft restart - reload mubeng with same proxy file
        if not preflight_passed:
            print()
            print("[INFO] Soft restart: Reloading proxy rotator...")
            stop_mubeng_rotator(mubeng_process, None)  # Don't delete temp file

            proxy_url, mubeng_process, _ = setup_mubeng_rotator(
                port=8089,
                min_live_proxies=5,
            )
            if mubeng_process:
                print(f"[SUCCESS] Proxy rotator restarted at {proxy_url}")
                for attempt in range(1, 4):
                    if preflight_check(proxy_url, timeout=15):
                        print(f"[SUCCESS] Pre-flight check passed after soft restart (attempt {attempt})")
                        preflight_passed = True
                        break
                    else:
                        print(f"[WARNING] Pre-flight still failing (attempt {attempt}/3)")
                        if attempt < 3:
                            time.sleep(1)

        # Level 3: Full refresh - scrape new proxies (5-10 min)
        if not preflight_passed:
            print()
            print("[INFO] Full refresh: Fetching new proxies (this takes 5-10 min)...")
            stop_mubeng_rotator(mubeng_process, temp_proxy_file)

            mtime_before, task_id = orch.trigger_proxy_refresh()
            if not orch.wait_for_refresh_completion(mtime_before, min_count=5, task_id=task_id):
                print("[ERROR] Proxy refresh timed out or failed. Aborting.")
                return

            # Reload proxy pool after refresh
            if proxy_pool:
                print("[INFO] Reloading proxy pool after refresh...")
                proxy_pool.reload_proxies()
                stats = proxy_pool.get_stats()
                print(f"[SUCCESS] Proxy pool reloaded: {stats['total_proxies']} proxies")

            print("[INFO] Restarting proxy rotator with fresh proxies...")
            proxy_url, mubeng_process, temp_proxy_file = setup_mubeng_rotator(
                port=8089,
                min_live_proxies=5,
            )
            if not mubeng_process:
                print("[ERROR] Failed to restart proxy rotator. Aborting.")
                return
            print(f"[SUCCESS] Proxy rotator restarted at {proxy_url}")

            # Final pre-flight check
            for attempt in range(1, 4):
                if preflight_check(proxy_url, timeout=15):
                    print(f"[SUCCESS] Pre-flight check passed after refresh (attempt {attempt})")
                    preflight_passed = True
                    break
                else:
                    print(f"[WARNING] Pre-flight still failing (attempt {attempt}/3)")
                    if attempt < 3:
                        time.sleep(1)

        if not preflight_passed:
            print("[ERROR] Pre-flight check failed after all recovery attempts. Proxies may be blocked.")
            stop_mubeng_rotator(mubeng_process, temp_proxy_file)
            return

        try:
            # 5. Crawl each site's URLs
            print()
            print("=" * 60)
            print("STARTING CRAWL")
            print("=" * 60)

            total_stats = {"scraped": 0, "failed": 0, "total_attempts": 0}

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

            print()
            print("=" * 60)
            print("CRAWL COMPLETE")
            print("=" * 60)
            print(f"\n[SUMMARY] Total scraped: {total_stats['scraped']}, "
                  f"Failed: {total_stats['failed']}, "
                  f"Success rate: {total_stats['scraped'] / max(total_stats['total_attempts'], 1) * 100:.1f}%")

            # Save final proxy scores
            if proxy_pool:
                print("\n[INFO] Saving final proxy scores...")
                proxy_pool.save_scores()
                stats = proxy_pool.get_stats()
                print(f"[SUCCESS] Final proxy stats: {stats['total_proxies']} proxies, "
                      f"avg score: {stats['average_score']:.2f}")

        finally:
            # Clean up proxy rotator
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
