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

import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx

from dotenv import load_dotenv
from loguru import logger

from scrapling.fetchers import Fetcher, StealthyFetcher

from resilience.circuit_breaker import extract_domain, get_circuit_breaker
from resilience.exceptions import BlockedException, CircuitOpenException
from resilience.rate_limiter import get_rate_limiter
from resilience.response_validator import detect_soft_block
from resilience.retry import retry_with_backoff
from resilience.checkpoint import CheckpointManager
from data import data_store_main
from data.change_detector import compute_hash, has_changed, track_price_change
from paths import LOGS_DIR, PROXIES_DIR
from proxies.proxy_scorer import ScoredProxyPool
from utils.log_config import setup_logging
from config.settings import (
    MAX_URL_RETRIES,
    MIN_PROXIES_FOR_SCRAPING,
    PROXY_TIMEOUT_SECONDS,
    PROXY_TIMEOUT_MS,
    SCRAPER_REPORTS_DIR,
    PARALLEL_SCRAPING_ENABLED,
)
from scraping.metrics import MetricsCollector, RequestStatus
from scraping.session_report import SessionReportGenerator


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


def quick_liveness_check(proxy_url: str) -> bool:
    """
    Quick check if proxy is alive using httpx.

    Tests against imot.bg (actual target) rather than httpbin.
    Uses PROXY_TIMEOUT_SECONDS (45s) - same as scraping timeout.

    Args:
        proxy_url: Full proxy URL (e.g., "http://1.2.3.4:8080")

    Returns:
        True if proxy responds, False otherwise
    """
    try:
        with httpx.Client(proxy=proxy_url, timeout=PROXY_TIMEOUT_SECONDS) as client:
            response = client.get("https://www.imot.bg")
            return response.status_code == 200
    except Exception:
        return False


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
    Fetch search page with liveness check, circuit breaker, and rate limiting.

    Flow:
    1. Pick proxy from pool
    2. Quick liveness check - if dead, remove and pick next
    3. If alive, pass to Fetcher
    4. On fetch failure, record and retry with new proxy

    Args:
        url: The URL to fetch
        proxy: Fallback proxy URL (if no pool)
        proxy_pool: ScoredProxyPool for proxy selection and scoring

    Returns:
        (html_content, proxy_key) - proxy_key is the successful proxy or None

    Raises:
        CircuitOpenException if circuit breaker is open for domain
        Exception if all retries fail (after MAX_URL_RETRIES attempts)
    """
    circuit_breaker = get_circuit_breaker()
    rate_limiter = get_rate_limiter()
    domain = extract_domain(url)

    # Check circuit breaker FIRST
    if not circuit_breaker.can_request(domain):
        raise CircuitOpenException(f"Circuit open for {domain}")

    # Acquire rate limiter token (blocks if needed)
    rate_limiter.acquire(domain)

    # Track successful proxy
    successful_proxy_key = None

    for attempt in range(1, MAX_URL_RETRIES + 1):
        # Select proxy with liveness check
        effective_proxy = proxy  # fallback
        proxy_key = None

        if proxy_pool:
            # Find a live proxy (check up to pool size times)
            max_checks = min(proxy_pool.get_stats()['total_proxies'], 10)
            for _ in range(max_checks):
                proxy_dict = proxy_pool.select_proxy()
                if not proxy_dict:
                    break

                proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"
                protocol = proxy_dict.get('protocol', 'http')
                effective_proxy = f"{protocol}://{proxy_dict['host']}:{proxy_dict['port']}"

                # Quick liveness check
                if quick_liveness_check(effective_proxy):
                    logger.debug(f"Proxy {proxy_key} is alive")
                    break
                else:
                    # Dead proxy - remove immediately
                    logger.warning(f"Proxy {proxy_key} dead, removing from pool")
                    proxy_pool.remove_proxy(proxy_key)
                    proxy_key = None
                    effective_proxy = proxy

            if not proxy_key and not effective_proxy:
                raise Exception("No working proxies available")

        # Try to fetch with the live proxy
        try:
            response = Fetcher.get(
                url=url,
                proxy=effective_proxy,
                timeout=PROXY_TIMEOUT_SECONDS
            )
            html = response.html_content

            # Check for soft blocks
            is_blocked, block_reason = detect_soft_block(html)
            if is_blocked:
                circuit_breaker.record_failure(domain)
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=False)
                raise BlockedException(f"Soft block detected: {block_reason}")

            # Success!
            circuit_breaker.record_success(domain)
            if proxy_pool and proxy_key:
                proxy_pool.record_result(proxy_key, success=True)
            successful_proxy_key = proxy_key
            return html, successful_proxy_key

        except Exception as e:
            logger.warning(f"Fetch attempt {attempt}/{MAX_URL_RETRIES} failed: {e}")
            circuit_breaker.record_failure(domain)
            if proxy_pool and proxy_key:
                proxy_pool.record_result(proxy_key, success=False)

            if attempt == MAX_URL_RETRIES:
                raise

            # Brief delay before retry
            time.sleep(1)

    raise Exception(f"All {MAX_URL_RETRIES} fetch attempts failed")


def _collect_listing_urls(
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
            logger.error(f"All {MAX_URL_RETRIES} attempts failed for page {current_page}: {e}")
            break  # Stop pagination on failure

        # Check if this is the last page
        if hasattr(scraper, "is_last_page") and scraper.is_last_page(html, current_page):
            logger.info(f"Last page detected at page {current_page}")
            listing_urls = scraper.extract_search_results(html)
            if listing_urls:
                new_urls = [u for u in listing_urls if u not in all_listing_urls]
                all_listing_urls.extend(new_urls)
                logger.info(f"Found {len(new_urls)} new listings on last page (total: {len(all_listing_urls)})")
            break

        listing_urls = scraper.extract_search_results(html)
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
    Fetch listing page with liveness check, circuit breaker, and rate limiting.

    Uses StealthyFetcher (browser) for JS-rendered pages.
    Flow:
    1. Pick proxy from pool
    2. Quick liveness check - if dead, remove and pick next
    3. If alive, pass to StealthyFetcher
    4. On fetch failure, record and retry with new proxy

    Args:
        url: The listing URL to fetch
        proxy: Fallback proxy URL (if no pool)
        proxy_pool: ScoredProxyPool for proxy selection and scoring

    Returns:
        (html_content, proxy_key) - proxy_key is the successful proxy or None

    Raises:
        CircuitOpenException if circuit breaker is open for domain
        Exception if all retries fail (after MAX_URL_RETRIES attempts)
    """
    circuit_breaker = get_circuit_breaker()
    rate_limiter = get_rate_limiter()
    domain = extract_domain(url)

    # Check circuit breaker FIRST
    if not circuit_breaker.can_request(domain):
        raise CircuitOpenException(f"Circuit open for {domain}")

    # Acquire rate limiter token (blocks if needed)
    rate_limiter.acquire(domain)

    # Track successful proxy
    successful_proxy_key = None

    for attempt in range(1, MAX_URL_RETRIES + 1):
        # Select proxy with liveness check
        effective_proxy = proxy  # fallback
        proxy_key = None

        if proxy_pool:
            # Find a live proxy (check up to pool size times)
            max_checks = min(proxy_pool.get_stats()['total_proxies'], 10)
            for _ in range(max_checks):
                proxy_dict = proxy_pool.select_proxy()
                if not proxy_dict:
                    break

                proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"
                protocol = proxy_dict.get('protocol', 'http')
                effective_proxy = f"{protocol}://{proxy_dict['host']}:{proxy_dict['port']}"

                # Quick liveness check
                if quick_liveness_check(effective_proxy):
                    logger.debug(f"Proxy {proxy_key} is alive")
                    break
                else:
                    # Dead proxy - remove immediately
                    logger.warning(f"Proxy {proxy_key} dead, removing from pool")
                    proxy_pool.remove_proxy(proxy_key)
                    proxy_key = None
                    effective_proxy = proxy

            if not proxy_key and not effective_proxy:
                raise Exception("No working proxies available")

        # Try to fetch with the live proxy
        try:
            response = StealthyFetcher.fetch(
                url=url,
                proxy=effective_proxy,
                humanize=True,
                block_webrtc=True,
                network_idle=True,
                timeout=PROXY_TIMEOUT_MS
            )
            html = response.html_content

            # Check for soft blocks
            is_blocked, block_reason = detect_soft_block(html)
            if is_blocked:
                circuit_breaker.record_failure(domain)
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=False)
                raise BlockedException(f"Soft block detected: {block_reason}")

            # Success!
            circuit_breaker.record_success(domain)
            if proxy_pool and proxy_key:
                proxy_pool.record_result(proxy_key, success=True)
            successful_proxy_key = proxy_key
            return html, successful_proxy_key

        except Exception as e:
            logger.warning(f"Fetch attempt {attempt}/{MAX_URL_RETRIES} failed: {e}")
            circuit_breaker.record_failure(domain)
            if proxy_pool and proxy_key:
                proxy_pool.record_result(proxy_key, success=False)

            if attempt == MAX_URL_RETRIES:
                raise

            # Brief delay before retry
            time.sleep(1)

    raise Exception(f"All {MAX_URL_RETRIES} fetch attempts failed")


def _scrape_listings(
    scraper,
    urls: list[str],
    delay: float,
    proxy: str | None,
    proxy_pool: Optional[ScoredProxyPool],
    checkpoint: Optional[CheckpointManager] = None,
    metrics: Optional[MetricsCollector] = None
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

        # Track request for metrics
        domain = extract_domain(url)
        if metrics:
            metrics.record_request(url, domain)
        start_time = time.time()

        try:
            html, proxy_key = _fetch_listing_page(url, proxy, proxy_pool)
            response_time_ms = (time.time() - start_time) * 1000

            # Request succeeded - extract listing data
            listing = scraper.extract_listing(html, url)
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
                    if metrics:
                        metrics.record_response(
                            url, RequestStatus.SUCCESS, response_time_ms=response_time_ms
                        )
                        metrics.record_listing_saved(url, listing.url)
                else:
                    stats["unchanged"] += 1
                    logger.debug("  -> Unchanged (skipped)")
                    if metrics:
                        metrics.record_response(
                            url, RequestStatus.SKIPPED, response_time_ms=response_time_ms
                        )
                        metrics.record_listing_skipped(url, "unchanged")
                # Score successful proxy
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=True)
            else:
                # Extraction failed but request succeeded
                stats["failed"] += 1
                logger.warning("  -> Failed to extract listing data")
                if metrics:
                    metrics.record_response(
                        url, RequestStatus.PARSE_ERROR,
                        response_time_ms=response_time_ms,
                        error_type="extraction_failed"
                    )
                # Score as failure (page content was unusable)
                if proxy_pool and proxy_key:
                    proxy_pool.record_result(proxy_key, success=False)

        except BlockedException as e:
            response_time_ms = (time.time() - start_time) * 1000
            stats["failed"] += 1
            logger.error(f"  -> Blocked: {e}")
            if metrics:
                metrics.record_response(
                    url, RequestStatus.BLOCKED,
                    response_time_ms=response_time_ms,
                    error_type="blocked",
                    error_message=str(e)
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            # All retries exhausted
            stats["failed"] += 1
            error_msg = str(e).lower()
            if "timeout" in error_msg:
                logger.error(f"  -> Timeout: {e}")
                if metrics:
                    metrics.record_response(
                        url, RequestStatus.TIMEOUT,
                        response_time_ms=response_time_ms,
                        error_type="timeout",
                        error_message=str(e)
                    )
            else:
                logger.error(f"  -> All {MAX_URL_RETRIES} attempts failed for {url}: {e}")
                if metrics:
                    metrics.record_response(
                        url, RequestStatus.FAILED,
                        response_time_ms=response_time_ms,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )

        # Update checkpoint state
        _scraped_urls.add(url)
        if url in _pending_urls:
            _pending_urls.remove(url)
        if checkpoint:
            checkpoint.save(_scraped_urls, _pending_urls)

        time.sleep(delay)

    return stats


def scrape_from_start_url(
    scraper,
    start_url: str,
    limit: int,
    delay: float,
    proxy: str | None = None,
    proxy_pool: Optional[ScoredProxyPool] = None,
    checkpoint: Optional[CheckpointManager] = None,
    metrics: Optional[MetricsCollector] = None
) -> dict:
    """
    Scrape all listings from a starting URL with pagination support.

    Args:
        scraper: The site-specific scraper instance.
        start_url: Search results page URL to start from.
        limit: Maximum number of listings to scrape.
        delay: Seconds to wait between requests (from site config).
        proxy: The proxy server URL (e.g., "http://localhost:8089"). Should always be set.
        proxy_pool: Optional ScoredProxyPool for tracking proxy performance.
        checkpoint: Optional CheckpointManager for crash recovery.
        metrics: Optional MetricsCollector for scraper monitoring.

    Returns:
        Dictionary with stats: {scraped: int, failed: int, total_attempts: int}
    """
    logger.info(f"Starting crawl from: {start_url}")
    logger.info(f"Rate limit: {60/delay:.1f} URLs/min ({delay} sec delay)")
    logger.info(f"Target: {limit} listings")
    if proxy_pool:
        stats = proxy_pool.get_stats()
        logger.info(f"Using proxy pool: {stats['total_proxies']} proxies available")
    elif proxy:
        logger.info(f"Using proxy: {proxy}")

    # Phase 1: Collect listing URLs from search pages
    urls = _collect_listing_urls(scraper, start_url, limit, delay, proxy, proxy_pool)
    logger.info(f"Collected {len(urls)} listing URLs to scrape")

    # Phase 2: Scrape individual listings
    stats = _scrape_listings(
        scraper, urls, delay, proxy, proxy_pool, checkpoint, metrics
    )
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
    if not orch.wait_for_proxies(min_count=MIN_PROXIES_FOR_SCRAPING):
        print("[ERROR] Could not get proxies. Aborting.")
        return False

    return True


def _initialize_proxy_pool() -> Optional[ScoredProxyPool]:
    """Initialize proxy scoring pool. Returns pool or None if failed."""
    print("[INFO] Initializing proxy scoring system...")
    try:
        proxy_pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")
        stats = proxy_pool.get_stats()
        print(f"[SUCCESS] Proxy pool initialized: {stats['total_proxies']} proxies")
        return proxy_pool
    except Exception as e:
        logger.warning(f"Failed to initialize proxy pool: {e}")
        print(f"[WARNING] Proxy scoring disabled: {e}")
        return None


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
    from config.scraping_config import load_scraping_config
    from websites import get_scraper

    print()
    print("=" * 60)
    print("STARTING CRAWL")
    print("=" * 60)

    total_stats = {"scraped": 0, "failed": 0, "total_attempts": 0}

    # Initialize metrics collector for this crawl session
    metrics = MetricsCollector()

    # Check proxy count before starting
    if not _ensure_min_proxies(proxy_pool, orch):
        logger.error("Failed to ensure minimum proxies before crawl")
        return total_stats

    for site, urls in start_urls.items():
        scraper = get_scraper(site)
        if not scraper:
            print(f"[WARNING] Scraper for {site} not implemented, skipping")
            continue

        # Load per-site configuration (new system)
        scraping_config = load_scraping_config(site)
        # Get limit from start_urls.yaml (legacy, per-crawl setting)
        site_config = get_site_config(site)
        print(f"\n[SITE] {site} ({len(urls)} start URLs)")
        print(f"[CONFIG] limit={site_config.limit}, delay={scraping_config.timing.delay_seconds}s, timeout={scraping_config.timeouts.page_load_seconds}s")

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
                stats = scrape_from_start_url(
                    scraper,
                    url,
                    limit=site_config.limit,
                    delay=scraping_config.timing.delay_seconds,
                    proxy=proxy_url,
                    proxy_pool=proxy_pool,
                    checkpoint=checkpoint,
                    metrics=metrics
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
            break

    # Generate and save session report
    run_metrics = metrics.end_run()
    report_gen = SessionReportGenerator(Path(SCRAPER_REPORTS_DIR))
    report = report_gen.generate(
        metrics=run_metrics,
        proxy_stats=proxy_pool.get_stats() if proxy_pool else None,
        circuit_states=get_circuit_breaker().get_all_states()
    )
    report_path = report_gen.save(report)
    logger.info(f"Session report saved: {report_path}")
    print(f"[INFO] Session report saved: {report_path}")

    return total_stats


def _wait_for_parallel_scraping(orch, group_id: str, poll_interval: float = 5.0) -> dict:
    """
    Wait for parallel scraping to complete, showing progress.

    Args:
        orch: Orchestrator instance
        group_id: Celery group ID from start_all_sites_scraping()
        poll_interval: Seconds between progress checks

    Returns:
        Aggregated stats dict
    """
    print("[INFO] Waiting for parallel scraping to complete...")

    while True:
        time.sleep(poll_interval)

        # Check Celery task status
        from celery.result import GroupResult
        result = GroupResult.restore(group_id)

        if result is None:
            print("[WARNING] Could not restore group result")
            break

        if result.ready():
            print("[SUCCESS] All parallel scraping tasks complete")
            break

        completed = sum(1 for r in result.results if r.ready())
        total = len(result.results)
        print(f"[PROGRESS] {completed}/{total} site tasks complete")

    return {"scraped": 0, "failed": 0, "total_attempts": 0}  # TODO: aggregate from results


def _print_summary(stats: dict, proxy_pool: Optional[ScoredProxyPool]) -> None:
    """Print final crawl summary."""
    print()
    print("=" * 60)
    print("CRAWL COMPLETE")
    print("=" * 60)
    print(f"\n[SUMMARY] Scraped: {stats['scraped']}, "
          f"Unchanged: {stats.get('unchanged', 0)}, "
          f"Failed: {stats['failed']}, "
          f"Success rate: {stats['scraped'] / max(stats['total_attempts'], 1) * 100:.1f}%")

    # Show final proxy stats
    if proxy_pool:
        stats_pool = proxy_pool.get_stats()
        print(f"\n[INFO] Final proxy stats: {stats_pool['total_proxies']} proxies, "
              f"{stats_pool['proxies_with_failures']} with failures")


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
        if not proxy_pool:
            print("[ERROR] Failed to initialize proxy pool. Aborting.")
            return

        # Check we have enough proxies before starting
        stats = proxy_pool.get_stats()
        if stats['total_proxies'] < MIN_PROXIES_FOR_SCRAPING:
            print(f"[WARNING] Only {stats['total_proxies']} proxies available, need {MIN_PROXIES_FOR_SCRAPING}")
            print("[INFO] Triggering proxy refresh...")
            mtime_before, task_id = orch.trigger_proxy_refresh()
            if not orch.wait_for_refresh_completion(mtime_before, min_count=MIN_PROXIES_FOR_SCRAPING, task_id=task_id):
                print("[ERROR] Proxy refresh failed. Aborting.")
                return
            proxy_pool.reload_proxies()
            stats = proxy_pool.get_stats()
            print(f"[SUCCESS] Proxy pool reloaded: {stats['total_proxies']} proxies")

        print(f"[INFO] Using direct proxy connections ({stats['total_proxies']} proxies available)")

        if PARALLEL_SCRAPING_ENABLED:
            # Parallel scraping via Celery
            print()
            print("[INFO] PARALLEL_SCRAPING mode enabled")
            print("[INFO] Dispatching all sites to Celery workers...")

            # Convert start_urls dict format for Celery task
            # start_urls is {site: [url1, url2, ...]}
            result = orch.start_all_sites_scraping(start_urls)
            print(f"[SUCCESS] Dispatched group: {result['group_id']}")

            stats = _wait_for_parallel_scraping(orch, result['group_id'])
        else:
            # Sequential scraping - proxies selected directly from pool
            stats = _crawl_all_sites(start_urls, None, proxy_pool, orch)

        _print_summary(stats, proxy_pool)

    print("[INFO] All processes stopped.")

    # Auto-launch dashboard
    print()
    print("=" * 60)
    print("LAUNCHING DASHBOARD")
    print("=" * 60)
    print("[INFO] Starting Streamlit dashboard at http://localhost:8501")
    subprocess.run(["streamlit", "run", "app/streamlit_app.py"])


def main() -> None:
    """Main entry point for Sofia Real Estate Scraper."""
    load_dotenv()
    setup_logging(LOGS_DIR)

    # Initialize database before any operations (Phase 4.3.0.2)
    # Must happen before Celery workers spawn to prevent race conditions
    data_store_main.initialize_database()

    run_auto_mode()


if __name__ == "__main__":
    main()
