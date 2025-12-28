"""Celery tasks for parallel site scraping."""
import asyncio
import logging
import os
import time
import uuid
from typing import Any

import redis
from celery import chord, group

from celery_app import celery_app
from scraping.redis_keys import ScrapingKeys

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client = None
PROGRESS_KEY_TTL = 3600  # 1 hour


def get_redis_client():
    """Get shared Redis client for progress tracking."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_BROKER_DB", "0")),
            decode_responses=True,
        )
    return _redis_client


@celery_app.task(bind=True)
def dispatch_site_scraping(self, site_name: str, start_urls: list) -> dict:
    """
    Dispatcher: Collect listing URLs from start pages and dispatch chunk workers.

    Args:
        site_name: Site identifier (e.g., "imot.bg")
        start_urls: List of search/category page URLs to crawl

    Returns:
        {"job_id": str, "chord_id": str, "total_urls": int}
    """
    from config.scraping_config import load_scraping_config
    from scraping.async_fetcher import fetch_page
    from websites import get_scraper

    job_id = f"scrape_{site_name}_{uuid.uuid4().hex[:8]}"
    r = get_redis_client()

    logger.info(f"Starting site scraping dispatch for {site_name} (job_id: {job_id})")

    # Initialize job status
    r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "COLLECTING")
    r.setex(ScrapingKeys.started_at(job_id), PROGRESS_KEY_TTL, int(time.time()))

    scraper = get_scraper(site_name)
    if not scraper:
        r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "FAILED")
        return {"job_id": job_id, "error": f"No scraper for site: {site_name}"}

    config = load_scraping_config(site_name)

    # Phase 1: Collect listing URLs from all start pages
    all_listing_urls = []
    for start_url in start_urls:
        try:
            html = asyncio.run(fetch_page(start_url))
            urls = scraper.extract_search_results(html)
            all_listing_urls.extend(urls)
            logger.info(f"Collected {len(urls)} URLs from {start_url}")
        except Exception as e:
            logger.warning(f"Failed to collect from {start_url}: {e}")

    # Deduplicate
    all_listing_urls = list(set(all_listing_urls))

    if not all_listing_urls:
        r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "COMPLETE")
        r.setex(ScrapingKeys.result_count(job_id), PROGRESS_KEY_TTL, 0)
        return {"job_id": job_id, "total_urls": 0, "status": "NO_URLS"}

    # Phase 2: Split into chunks
    chunk_size = config.concurrency.max_per_domain * 10  # ~20 URLs per chunk
    if chunk_size < 10:
        chunk_size = 25  # fallback
    chunks = [
        all_listing_urls[i : i + chunk_size]
        for i in range(0, len(all_listing_urls), chunk_size)
    ]

    # Initialize Redis progress
    r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "DISPATCHED")
    r.setex(ScrapingKeys.total_chunks(job_id), PROGRESS_KEY_TTL, len(chunks))
    r.setex(ScrapingKeys.completed_chunks(job_id), PROGRESS_KEY_TTL, 0)
    r.setex(ScrapingKeys.total_urls(job_id), PROGRESS_KEY_TTL, len(all_listing_urls))

    # Phase 3: Create chord (workers | callback)
    workers = group(
        [scrape_chunk.s(chunk, job_id, site_name) for chunk in chunks]
    )
    callback = aggregate_results.s(job_id, site_name)

    workflow = chord(workers, callback)
    result = workflow.apply_async()

    logger.info(
        f"Dispatched {len(chunks)} chunks for {site_name} (chord_id: {result.id})"
    )
    return {
        "job_id": job_id,
        "chord_id": result.id,
        "total_urls": len(all_listing_urls),
        "total_chunks": len(chunks),
    }


@celery_app.task(
    bind=True,
    soft_time_limit=600,  # 10 min soft limit
    time_limit=720,  # 12 min hard limit
    max_retries=2,
    default_retry_delay=30,
)
def scrape_chunk(self, urls: list, job_id: str, site_name: str) -> list:
    """
    Worker: Scrape a chunk of listing URLs.

    Uses circuit breaker and rate limiter for resilience.
    Returns list of listing dicts (or error dicts).
    """
    from resilience import get_circuit_breaker
    from resilience.circuit_breaker import extract_domain
    from scraping.async_fetcher import fetch_page
    from websites import get_scraper

    scraper = get_scraper(site_name)
    if not scraper:
        return [{"url": url, "error": "no_scraper", "skipped": True} for url in urls]

    circuit_breaker = get_circuit_breaker()
    domain = extract_domain(urls[0]) if urls else site_name

    results = []
    for url in urls:
        try:
            # Check circuit breaker
            if not circuit_breaker.can_request(domain):
                results.append({"url": url, "error": "circuit_open", "skipped": True})
                continue

            # Fetch and extract (fetch_page handles rate limiting internally)
            html = asyncio.run(fetch_page(url))
            listing = scraper.extract_listing(html, url)

            if listing:
                circuit_breaker.record_success(domain)
                results.append(
                    listing.to_dict() if hasattr(listing, "to_dict") else listing
                )
            else:
                results.append({"url": url, "error": "extraction_failed"})

        except Exception as e:
            circuit_breaker.record_failure(domain, str(type(e).__name__))
            results.append({"url": url, "error": str(e)})

    # Update progress
    try:
        r = get_redis_client()
        r.incr(ScrapingKeys.completed_chunks(job_id))
        r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "PROCESSING")
    except Exception as e:
        logger.warning(f"Failed to update Redis progress: {e}")

    success_count = len([r for r in results if "error" not in r])
    logger.info(f"Chunk complete: {success_count}/{len(urls)} extracted")
    return results


@celery_app.task(bind=True)
def aggregate_results(
    self, chunk_results: list, job_id: str, site_name: str
) -> dict:
    """
    Callback: Aggregate results from all workers and save to database.

    Args:
        chunk_results: List of lists from each scrape_chunk worker
        job_id: Job identifier
        site_name: Site name for logging

    Returns:
        {"job_id": str, "saved": int, "errors": int}
    """
    from data.data_store_main import save_listing
    from websites import ListingData

    r = get_redis_client()
    r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "AGGREGATING")

    logger.info(f"Aggregating results for {site_name} (job_id: {job_id})")

    # Flatten results
    all_results = []
    for chunk in chunk_results:
        if chunk:  # Handle None from failed tasks
            all_results.extend(chunk)

    # Separate successes and errors
    listings = [r for r in all_results if isinstance(r, dict) and "error" not in r]
    errors = [r for r in all_results if isinstance(r, dict) and "error" in r]

    # Save to database
    saved_count = 0
    for listing_dict in listings:
        try:
            # Convert dict back to ListingData if needed
            if isinstance(listing_dict, dict):
                listing = ListingData(**listing_dict)
            else:
                listing = listing_dict
            save_listing(listing)
            saved_count += 1
        except Exception as e:
            errors.append({"url": listing_dict.get("url"), "error": f"db_save: {e}"})
            logger.warning(f"Failed to save listing: {e}")

    # Mark complete
    r.setex(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "COMPLETE")
    r.setex(ScrapingKeys.completed_at(job_id), PROGRESS_KEY_TTL, int(time.time()))
    r.setex(ScrapingKeys.result_count(job_id), PROGRESS_KEY_TTL, saved_count)
    r.setex(ScrapingKeys.error_count(job_id), PROGRESS_KEY_TTL, len(errors))

    logger.info(f"Job {job_id} complete: saved {saved_count}, errors {len(errors)}")
    return {
        "job_id": job_id,
        "site": site_name,
        "saved": saved_count,
        "errors": len(errors),
        "total_processed": len(all_results),
    }


@celery_app.task
def scrape_all_sites(sites_config: dict) -> dict:
    """
    Dispatch scraping for all sites in parallel.

    Args:
        sites_config: {"imot.bg": ["url1", "url2"], "bazar.bg": ["url3"]}

    Returns:
        {"group_id": str, "sites": list}
    """
    tasks = group(
        [
            dispatch_site_scraping.s(site, urls)
            for site, urls in sites_config.items()
        ]
    )

    result = tasks.apply_async()

    logger.info(
        f"Dispatched scraping for {len(sites_config)} sites (group_id: {result.id})"
    )
    return {
        "group_id": result.id,
        "sites": list(sites_config.keys()),
    }
