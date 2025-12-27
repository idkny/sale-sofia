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
import signal
import sys
import time
from datetime import datetime
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from loguru import logger

from scrapling.fetchers import Fetcher, StealthyFetcher

from resilience.circuit_breaker import get_circuit_breaker
from resilience.exceptions import BlockedException, CircuitOpenException
from resilience.rate_limiter import get_rate_limiter
from resilience.response_validator import detect_soft_block
from resilience.retry import retry_with_backoff
from resilience.checkpoint import CheckpointManager
from data import data_store_main
from data.change_detector import compute_hash, has_changed, track_price_change
from paths import LOGS_DIR, PROXIES_DIR
from proxies.proxies_main import (
    setup_mubeng_rotator,
    stop_mubeng_rotator,
)
from proxies.proxy_scorer import ScoredProxyPool
from proxies.proxy_validator import preflight_check
from utils.log_config import setup_logging
from config.settings import (
    MUBENG_PROXY,
    MAX_PROXY_RETRIES,
    MIN_PROXIES_FOR_SCRAPING,
    PROXY_TIMEOUT_SECONDS,
    PROXY_TIMEOUT_MS,
    PREFLIGHT_MAX_ATTEMPTS_L1,
    PREFLIGHT_MAX_ATTEMPTS_L2,
    PREFLIGHT_MAX_ATTEMPTS_L3,
    PREFLIGHT_RETRY_DELAY,
    PROXY_WAIT_TIMEOUT,
    DEFAULT_SCRAPE_DELAY,
)


# Global state for checkpoint signal handler
_checkpoint_manager: Optional[CheckpointManager] = None
_scraped_urls: set[str] = set()
_pending_urls: list[str] = []


def _signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT gracefully."""
    logger.warning(f"Received signal {signum}, saving checkpoint...")
    if _checkpoint_manager:
        _checkpoint_manager.save(_scraped_urls, _pending_urls, force=True)
    logger.info("Checkpoint saved, exiting...")
    sys.exit(0)


def _setup_signal_handlers():
    """Set up graceful shutdown handlers."""
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)


def _extract_domain(url: str) -> str:
    """Extract domain from URL for circuit breaker tracking."""
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split('/')[0]


def _check_and_save_listing(listing) -> dict:
    """
    Check if listing changed and save if needed.

    Implements change detection to skip unchanged listings and track price changes.

    Args:
        listing: ListingData object from scraper

    Returns:
        dict with keys:
            - saved (bool): True if listing was saved (new or changed)
            - price_changed (bool): True if price changed
            - price_diff (float|None): Price difference if changed
            - old_price (float|None): Previous price if changed
            - new_price (float|None): Current price if changed
    """
    # Check for existing listing
    stored = data_store_main.get_listing_by_url(listing.url)
    new_hash = compute_hash(listing)

    # Check if content changed
    stored_hash = stored["content_hash"] if stored else None
    if stored and not has_changed(new_hash, stored_hash):
        # No change - just update counter
        data_store_main.increment_unchanged_counter(listing.url)
        return {"saved": False, "price_changed": False, "price_diff": None}

    # Content changed or new listing - track price change
    stored_price = stored["price_eur"] if stored else None
    stored_history = stored["price_history"] if stored else None

    price_changed, new_history, price_diff = track_price_change(
        listing.price_eur, stored_price, stored_history
    )

    # Save with change metadata
    data_store_main.save_listing(
        listing, content_hash=new_hash, price_history=new_history
    )

    return {
        "saved": True,
        "price_changed": price_changed,
        "price_diff": price_diff,
        "old_price": stored_price,
        "new_price": listing.price_eur,
    }


def _fetch_search_page(
    url: str,
    proxy: str | None,
    proxy_pool: Optional[ScoredProxyPool]
) -> tuple[str, str | None]:
    """
    Fetch search page with retry logic, circuit breaker, and rate limiting.

    Uses retry_with_backoff decorator for exponential backoff.
    Selects a new proxy on each retry attempt.

    Args:
        url: The URL to fetch
        proxy: Base proxy URL (mubeng rotator)
        proxy_pool: Optional ScoredProxyPool for proxy selection and scoring

    Returns:
        (html_content, proxy_key) - proxy_key is the successful proxy or None

    Raises:
        CircuitOpenException if circuit breaker is open for domain
        Exception if all retries fail (after MAX_PROXY_RETRIES attempts)
    """
    circuit_breaker = get_circuit_breaker()
    rate_limiter = get_rate_limiter()
    domain = _extract_domain(url)

    # Check circuit breaker FIRST
    if not circuit_breaker.can_request(domain):
        raise CircuitOpenException(f"Circuit open for {domain}")

    # Acquire rate limiter token (blocks if needed)
    rate_limiter.acquire(domain)

    # Track proxy across retries for scoring
    proxy_state = {"key": None}

    def on_retry(attempt: int, exc: Exception):
        # Score the failed proxy before retry
        if proxy_pool and proxy_state["key"]:
            proxy_pool.record_result(proxy_state["key"], success=False)
        # Record failure with circuit breaker
        circuit_breaker.record_failure(domain)

    @retry_with_backoff(max_attempts=MAX_PROXY_RETRIES, on_retry=on_retry)
    def fetch():
        # Select proxy for this attempt (Solution F - X-Proxy-Offset)
        headers = {}
        if proxy_pool:
            proxy_dict = proxy_pool.select_proxy()
            if proxy_dict:
                proxy_state["key"] = f"{proxy_dict['host']}:{proxy_dict['port']}"
                index = proxy_pool.get_proxy_index(proxy_state["key"])
                if index is not None:
                    headers = {"X-Proxy-Offset": str(index)}

        response = Fetcher.get(
            url=url,
            proxy=proxy or MUBENG_PROXY,
            timeout=PROXY_TIMEOUT_SECONDS,
            headers=headers
        )
        return response.html_content

    html = fetch()  # May raise after all retries exhausted

    # Check for soft blocks before recording success
    is_blocked, block_reason = detect_soft_block(html)
    if is_blocked:
        circuit_breaker.record_failure(domain)
        if proxy_pool and proxy_state["key"]:
            proxy_pool.record_result(proxy_state["key"], success=False)
        raise BlockedException(f"Soft block detected: {block_reason}")

    # Record success with circuit breaker
    circuit_breaker.record_success(domain)

    return html, proxy_state["key"]


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

        try:
            html, proxy_key = _fetch_search_page(current_url, proxy, proxy_pool)
            # Score successful proxy
            if proxy_pool and proxy_key:
                proxy_pool.record_result(proxy_key, success=True)
        except Exception as e:
            logger.error(f"All {MAX_PROXY_RETRIES} attempts failed for page {current_page}: {e}")
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


def _fetch_listing_page(
    url: str,
    proxy: str | None,
    proxy_pool: Optional[ScoredProxyPool]
) -> tuple[str, str | None]:
    """
    Fetch listing page with retry logic, circuit breaker, and rate limiting.

    Uses StealthyFetcher with retry_with_backoff decorator.
    Selects a new proxy on each retry attempt.

    Args:
        url: The listing URL to fetch
        proxy: Base proxy URL (mubeng rotator)
        proxy_pool: Optional ScoredProxyPool for proxy selection and scoring

    Returns:
        (html_content, proxy_key) - proxy_key is the successful proxy or None

    Raises:
        CircuitOpenException if circuit breaker is open for domain
        Exception if all retries fail (after MAX_PROXY_RETRIES attempts)
    """
    circuit_breaker = get_circuit_breaker()
    rate_limiter = get_rate_limiter()
    domain = _extract_domain(url)

    # Check circuit breaker FIRST
    if not circuit_breaker.can_request(domain):
        raise CircuitOpenException(f"Circuit open for {domain}")

    # Acquire rate limiter token (blocks if needed)
    rate_limiter.acquire(domain)

    # Track proxy across retries for scoring
    proxy_state = {"key": None}

    def on_retry(attempt: int, exc: Exception):
        # Score the failed proxy before retry
        if proxy_pool and proxy_state["key"]:
            proxy_pool.record_result(proxy_state["key"], success=False)
        # Record failure with circuit breaker
        circuit_breaker.record_failure(domain)

    @retry_with_backoff(max_attempts=MAX_PROXY_RETRIES, on_retry=on_retry)
    def fetch():
        # Select proxy for this attempt (Solution F - X-Proxy-Offset)
        extra_headers = {}
        if proxy_pool:
            proxy_dict = proxy_pool.select_proxy()
            if proxy_dict:
                proxy_state["key"] = f"{proxy_dict['host']}:{proxy_dict['port']}"
                index = proxy_pool.get_proxy_index(proxy_state["key"])
                if index is not None:
                    extra_headers = {"X-Proxy-Offset": str(index)}

        response = StealthyFetcher.fetch(
            url=url,
            proxy=proxy or MUBENG_PROXY,
            extra_headers=extra_headers,
            humanize=True,
            block_webrtc=True,
            network_idle=True,
            timeout=PROXY_TIMEOUT_MS
        )
        return response.html_content

    html = fetch()  # May raise after all retries exhausted

    # Check for soft blocks before recording success
    is_blocked, block_reason = detect_soft_block(html)
    if is_blocked:
        circuit_breaker.record_failure(domain)
        if proxy_pool and proxy_state["key"]:
            proxy_pool.record_result(proxy_state["key"], success=False)
        raise BlockedException(f"Soft block detected: {block_reason}")

    # Record success with circuit breaker
    circuit_breaker.record_success(domain)

    return html, proxy_state["key"]


async def _scrape_listings(
    scraper,
    urls: list[str],
    delay: float,
    proxy: str | None,
    proxy_pool: Optional[ScoredProxyPool],
    checkpoint: Optional[CheckpointManager] = None
) -> dict:
    """
    Phase 2: Scrape individual listings from collected URLs.

    Uses StealthyFetcher for listing pages - anti-bot protection.

    Returns:
        Dictionary with stats: {scraped: int, failed: int, total_attempts: int, unchanged: int}
    """
    global _scraped_urls, _pending_urls

    stats = {"scraped": 0, "failed": 0, "total_attempts": 0, "unchanged": 0}
    _pending_urls = list(urls)

    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] {url}")
        stats["total_attempts"] += 1

        try:
            html, proxy_key = _fetch_listing_page(url, proxy, proxy_pool)

            # Request succeeded - extract listing data
            listing = await scraper.extract_listing(html, url)
            if listing:
                result = _check_and_save_listing(listing)
                if result["saved"]:
                    stats["scraped"] += 1
                    logger.info(f"  -> Saved: {listing.price_eur} EUR, {listing.sqm_total} sqm")
                    if result["price_changed"]:
                        direction = "dropped" if result["price_diff"] < 0 else "increased"
                        logger.info(
                            f"  -> Price {direction}: "
                            f"{result['old_price']} -> {result['new_price']} EUR"
                        )
                else:
                    stats["unchanged"] += 1
                    logger.debug("  -> Unchanged (skipped)")
                # Score successful proxy
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=True)
            else:
                # Extraction failed but request succeeded
                stats["failed"] += 1
                logger.warning("  -> Failed to extract listing data")
                # Score as failure (page content was unusable)
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=False)

        except Exception as e:
            # All retries exhausted
            stats["failed"] += 1
            logger.error(f"  -> All {MAX_PROXY_RETRIES} attempts failed for {url}: {e}")

        # Update checkpoint state
        _scraped_urls.add(url)
        if url in _pending_urls:
            _pending_urls.remove(url)
        if checkpoint:
            checkpoint.save(_scraped_urls, _pending_urls)

        time.sleep(delay)

    return stats


async def scrape_from_start_url(
    scraper,
    start_url: str,
    limit: int,
    delay: float = DEFAULT_SCRAPE_DELAY,
    proxy: str | None = None,
    proxy_pool: Optional[ScoredProxyPool] = None,
    checkpoint: Optional[CheckpointManager] = None
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
        checkpoint: Optional CheckpointManager for crash recovery.

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
    stats = await _scrape_listings(scraper, urls, delay, proxy, proxy_pool, checkpoint)
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
    if not orch.wait_for_proxies(min_count=MIN_PROXIES_FOR_SCRAPING, timeout=PROXY_WAIT_TIMEOUT):
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
        min_live_proxies=MIN_PROXIES_FOR_SCRAPING,
    )

    if not mubeng_process:
        print("[ERROR] Failed to start proxy rotator. Aborting.")
        return proxy_url, mubeng_process, temp_proxy_file, ordered_proxy_keys

    print(f"[SUCCESS] Proxy rotator running at {proxy_url} with {len(ordered_proxy_keys)} proxies")
    return proxy_url, mubeng_process, temp_proxy_file, ordered_proxy_keys


def _run_preflight_level1(proxy_url: str, max_attempts: int = PREFLIGHT_MAX_ATTEMPTS_L1) -> bool:
    """
    Level 1 pre-flight: Try with mubeng auto-rotation.
    Mubeng rotates on error, so more attempts = more proxies tested.
    """
    print("[INFO] Running pre-flight proxy check...")
    for attempt in range(1, max_attempts + 1):
        if preflight_check(proxy_url, timeout=PROXY_TIMEOUT_SECONDS):
            print(f"[SUCCESS] Pre-flight check passed (attempt {attempt})")
            return True
        else:
            print(f"[WARNING] Pre-flight check failed (attempt {attempt}/{max_attempts})")
            if attempt < max_attempts:
                time.sleep(PREFLIGHT_RETRY_DELAY)  # Short delay, mubeng auto-rotates
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
        min_live_proxies=MIN_PROXIES_FOR_SCRAPING,
    )
    if not new_process:
        return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys

    print(f"[SUCCESS] Proxy rotator restarted at {proxy_url}")
    for attempt in range(1, PREFLIGHT_MAX_ATTEMPTS_L2 + 1):
        if preflight_check(proxy_url, timeout=PROXY_TIMEOUT_SECONDS):
            print(f"[SUCCESS] Pre-flight check passed after soft restart (attempt {attempt})")
            return True, new_process, proxy_url, new_temp_file, ordered_proxy_keys
        else:
            print(f"[WARNING] Pre-flight still failing (attempt {attempt}/{PREFLIGHT_MAX_ATTEMPTS_L2})")
            if attempt < PREFLIGHT_MAX_ATTEMPTS_L2:
                time.sleep(PREFLIGHT_RETRY_DELAY)

    return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys


def _run_preflight_level3(orch, proxy_pool: Optional[ScoredProxyPool]) -> tuple[bool, Any, str, Any, list[str]]:
    """
    Level 3 pre-flight: Full refresh - scrape new proxies (5-10 min).
    Returns (success, new_process, new_proxy_url, new_temp_file, ordered_proxy_keys).
    """
    print()
    print("[INFO] Full refresh: Fetching new proxies (this takes 5-10 min)...")

    mtime_before, task_id = orch.trigger_proxy_refresh()
    if not orch.wait_for_refresh_completion(mtime_before, min_count=MIN_PROXIES_FOR_SCRAPING, task_id=task_id):
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
        min_live_proxies=MIN_PROXIES_FOR_SCRAPING,
    )
    if not new_process:
        print("[ERROR] Failed to restart proxy rotator. Aborting.")
        return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys
    print(f"[SUCCESS] Proxy rotator restarted at {proxy_url}")

    # Final pre-flight check
    for attempt in range(1, PREFLIGHT_MAX_ATTEMPTS_L3 + 1):
        if preflight_check(proxy_url, timeout=PROXY_TIMEOUT_SECONDS):
            print(f"[SUCCESS] Pre-flight check passed after refresh (attempt {attempt})")
            return True, new_process, proxy_url, new_temp_file, ordered_proxy_keys
        else:
            print(f"[WARNING] Pre-flight still failing (attempt {attempt}/{PREFLIGHT_MAX_ATTEMPTS_L3})")
            if attempt < PREFLIGHT_MAX_ATTEMPTS_L3:
                time.sleep(PREFLIGHT_RETRY_DELAY)

    return False, new_process, proxy_url, new_temp_file, ordered_proxy_keys


def _ensure_min_proxies(
    proxy_pool: Optional[ScoredProxyPool],
    orch,
    min_count: int = MIN_PROXIES_FOR_SCRAPING
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
    global _checkpoint_manager, _scraped_urls, _pending_urls

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

        # Create checkpoint for this site
        checkpoint_name = f"{site}_{datetime.now().strftime('%Y-%m-%d')}"
        checkpoint = CheckpointManager(checkpoint_name)
        _checkpoint_manager = checkpoint

        # Load existing checkpoint
        state = checkpoint.load()
        already_scraped = set(state["scraped"]) if state else set()
        if already_scraped:
            logger.info(f"Resuming from checkpoint: {len(already_scraped)} URLs already scraped")
            _scraped_urls = already_scraped

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
                        proxy_pool=proxy_pool,
                        checkpoint=checkpoint
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

        # Clear checkpoint after successful completion of this site
        checkpoint.clear()
        _checkpoint_manager = None
        _scraped_urls = set()
        _pending_urls = []

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
    print(f"\n[SUMMARY] Scraped: {stats['scraped']}, "
          f"Unchanged: {stats.get('unchanged', 0)}, "
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
    global _checkpoint_manager, _scraped_urls, _pending_urls

    from orchestrator import Orchestrator

    _print_banner()

    start_urls = _load_start_urls()
    if not start_urls:
        return

    with Orchestrator() as orch:
        # Set up signal handlers for graceful shutdown
        _setup_signal_handlers()

        # Reset global checkpoint state
        _checkpoint_manager = None
        _scraped_urls = set()
        _pending_urls = []

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
