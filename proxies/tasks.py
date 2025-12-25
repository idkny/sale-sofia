import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis
from celery import group

from celery_app import celery_app
from paths import MUBENG_EXECUTABLE_PATH, PROXIES_DIR, PROXY_CHECKER_DIR, PSC_EXECUTABLE_PATH
from proxies.anonymity_checker import enrich_proxy_with_anonymity, get_real_ip
from proxies.quality_checker import enrich_proxy_with_quality

logger = logging.getLogger(__name__)

# Redis client singleton for progress tracking
_redis_client: Optional[redis.Redis] = None
PROGRESS_KEY_TTL = 3600  # 1 hour TTL for progress keys


def get_redis_client() -> redis.Redis:
    """Get shared Redis client instance for progress tracking."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_BROKER_DB", "0")),
            decode_responses=True,
        )
    return _redis_client


@celery_app.task
def scrape_new_proxies_task(_previous_result=None):
    """
    Celery task to scrape a new list of potential proxies.

    Args:
        _previous_result: Ignored. Allows this task to be used in chains.

    Note:
        This task does NOT auto-trigger check. Use chains instead:
        - Orchestrator: chain(scrape.s(), check.s())
        - Beat: Uses scrape_and_check_chain_task
    """
    logger.info("Starting proxy scraping task...")
    try:
        if not PSC_EXECUTABLE_PATH.exists():
            raise FileNotFoundError(f"proxy-scraper-checker executable not found at {PSC_EXECUTABLE_PATH}")

        psc_output_file = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
        psc_output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [str(PSC_EXECUTABLE_PATH), "-o", str(psc_output_file)]
        subprocess.run(
            cmd,
            cwd=str(PROXY_CHECKER_DIR),
            check=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout for scraping
        )
        with open(psc_output_file, "r") as f:
            proxies_found = len(json.load(f))
        logger.info(f"Scraping task completed. Found {proxies_found} potential proxies.")

        return f"Scraped {proxies_found} potential proxies."
    except subprocess.TimeoutExpired:
        logger.error("Proxy scraping task timed out after 5 minutes")
        raise
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Proxy scraping task failed: {e}", exc_info=True)
        raise


@celery_app.task(bind=True)
def check_scraped_proxies_task(self, _previous_result=None):
    """
    Dispatcher task that splits the scraped proxy list into chunks
    and sends them to worker tasks to be checked in parallel.

    Uses Redis for progress tracking (see spec 107).
    """
    job_id = self.request.id
    logger.info(f"Starting parallel proxy check dispatcher (job_id: {job_id})...")

    psc_output_file = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
    if not psc_output_file.exists() or psc_output_file.stat().st_size == 0:
        raise FileNotFoundError("Scraped proxy file not found or is empty.")

    with open(psc_output_file, "r") as f:
        all_proxies = json.load(f)

    chunk_size = 100  # Process 100 proxies per task
    proxy_chunks = [all_proxies[i : i + chunk_size] for i in range(0, len(all_proxies), chunk_size)]
    total_chunks = len(proxy_chunks)
    logger.info(f"Split {len(all_proxies)} proxies into {total_chunks} chunks of {chunk_size}.")

    # Set up Redis progress tracking
    try:
        r = get_redis_client()
        r.setex(f"proxy_refresh:{job_id}:total_chunks", PROGRESS_KEY_TTL, total_chunks)
        r.setex(f"proxy_refresh:{job_id}:completed_chunks", PROGRESS_KEY_TTL, 0)
        r.setex(f"proxy_refresh:{job_id}:status", PROGRESS_KEY_TTL, "DISPATCHED")
        r.setex(f"proxy_refresh:{job_id}:started_at", PROGRESS_KEY_TTL, int(time.time()))
        logger.info(f"Redis progress tracking initialized for job {job_id}")
    except Exception as e:
        logger.warning(f"Failed to set up Redis progress tracking: {e}")

    # Create a group of parallel tasks - pass job_id for progress tracking
    parallel_tasks = group(check_proxy_chunk_task.s(chunk, job_id) for chunk in proxy_chunks)

    # Execute the group and define a callback task to process the results
    callback = process_check_results_task.s(job_id)
    # This creates a chord: group runs in parallel, then callback runs with results
    # Use apply_async() to get chord result for event-based completion tracking
    chord_result = (parallel_tasks | callback).apply_async()

    logger.info(f"Dispatched all proxy check chunks to workers. chord_id: {chord_result.id}")
    return {"job_id": job_id, "chord_id": chord_result.id, "total_chunks": total_chunks, "status": "DISPATCHED"}


def _run_mubeng_liveness_check(proxy_chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run mubeng binary to check which proxies are alive.

    Returns:
        List of live proxy dicts from the chunk.
    """
    chunk_size = len(proxy_chunk)
    live_proxies = []

    temp_input_path = Path(tempfile.mktemp(suffix=".txt"))
    temp_output_path = Path(tempfile.mktemp(suffix=".txt"))

    try:
        # Write proxy URLs to temp input file
        with open(temp_input_path, "w") as f:
            for proxy in proxy_chunk:
                protocol = proxy.get("protocol", "http")
                f.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")

        # Run mubeng with PTY wrapper (mubeng hangs without terminal)
        mubeng_cmd = [
            str(MUBENG_EXECUTABLE_PATH), "--check",
            "-f", str(temp_input_path),
            "-o", str(temp_output_path),
            "-t", "10s",
        ]
        cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)

        if result.returncode != 0 and result.stderr:
            logger.warning(f"Mubeng returned non-zero ({result.returncode}): {result.stderr[:200]}")

        # Parse output: map live proxy URLs back to original dicts
        live_proxy_urls = []
        if temp_output_path.exists():
            with open(temp_output_path, "r") as f:
                live_proxy_urls = [line.strip() for line in f if line.strip()]

        proxy_data_map = {f"{p['host']}:{p['port']}": p for p in proxy_chunk}
        for proxy_url in live_proxy_urls:
            match = re.search(r"://(.*?:\d+)", proxy_url)
            if match and (host_port := match.group(1)) in proxy_data_map:
                live_proxies.append(proxy_data_map[host_port])

        logger.info(f"Chunk liveness check: {len(live_proxies)}/{chunk_size} proxies alive")

    except subprocess.TimeoutExpired:
        logger.error(f"Mubeng check timed out after 120s for chunk of {chunk_size} proxies")
    except Exception as e:
        logger.error(f"Mubeng check failed for a chunk: {e}")
    finally:
        temp_input_path.unlink(missing_ok=True)
        temp_output_path.unlink(missing_ok=True)

    return live_proxies


def _enrich_with_anonymity(live_proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check anonymity level for each live proxy and log results.
    Modifies proxies in-place and returns the same list.
    """
    if not live_proxies:
        return live_proxies

    logger.info(f"Checking anonymity for {len(live_proxies)} live proxies...")
    for proxy in live_proxies:
        enrich_proxy_with_anonymity(proxy, timeout=10)

    anon_counts = {}
    for p in live_proxies:
        level = p.get("anonymity", "Unknown")
        anon_counts[level] = anon_counts.get(level, 0) + 1
    logger.info(f"Anonymity check complete: {anon_counts}")

    return live_proxies


def _filter_by_real_ip_subnet(proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out proxies where exit_ip is in same /24 subnet as our real IP.
    These proxies are not actually working (routing through local connection).
    """
    real_ip = get_real_ip()
    if not real_ip:
        return proxies

    real_ip_prefix = ".".join(real_ip.split(".")[:3])
    before_count = len(proxies)

    filtered = [
        p for p in proxies
        if p.get("exit_ip") and not p.get("exit_ip", "").startswith(real_ip_prefix + ".")
    ]

    removed = before_count - len(filtered)
    if removed > 0:
        logger.info(f"Filtered {removed} proxies with exit_ip in same /24 as real IP {real_ip_prefix}.x")

    return filtered


def _check_quality_for_non_transparent(proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run quality checks for non-transparent proxies. Modifies in-place.
    """
    candidates = [p for p in proxies if p.get("anonymity") not in ("Transparent", "1")]

    if not candidates:
        return proxies

    logger.info(f"Checking quality for {len(candidates)} non-transparent proxies...")
    for proxy in candidates:
        enrich_proxy_with_quality(proxy, timeout=60)

    ip_passed = sum(1 for p in candidates if p.get("ip_check_passed"))
    target_passed = sum(1 for p in candidates if p.get("target_passed"))
    both_passed = sum(1 for p in candidates if p.get("ip_check_passed") and p.get("target_passed"))
    logger.info(
        f"Quality check complete: {both_passed}/{len(candidates)} passed both checks "
        f"(IP: {ip_passed}, Target: {target_passed})"
    )

    return proxies


def _update_redis_progress(job_id: str) -> None:
    """Increment completed chunks counter in Redis for progress tracking."""
    if not job_id:
        return
    try:
        r = get_redis_client()
        completed = r.incr(f"proxy_refresh:{job_id}:completed_chunks")
        r.setex(f"proxy_refresh:{job_id}:status", PROGRESS_KEY_TTL, "PROCESSING")
        logger.debug(f"Job {job_id}: chunk completed ({completed} total)")
    except Exception as e:
        logger.warning(f"Failed to update Redis progress: {e}")


@celery_app.task
def check_proxy_chunk_task(proxy_chunk: List[Dict[str, Any]], job_id: str = "") -> List[Dict[str, Any]]:
    """
    Worker task that checks a small chunk of proxies for liveness and returns the live ones.
    Uses mubeng binary for fast parallel liveness checking.

    Args:
        proxy_chunk: List of proxy dicts to check
        job_id: Job ID for Redis progress tracking (from dispatcher)
    """
    live_proxies = _run_mubeng_liveness_check(proxy_chunk)
    live_proxies = _enrich_with_anonymity(live_proxies)
    live_proxies = _filter_by_real_ip_subnet(live_proxies)
    live_proxies = _check_quality_for_non_transparent(live_proxies)
    _update_redis_progress(job_id)
    return live_proxies


def _flatten_and_filter_results(results: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Flatten chunk results and filter out transparent proxies.

    Returns:
        List of non-transparent proxies from all chunks.
    """
    all_proxies = [proxy for chunk_result in results for proxy in chunk_result if proxy]

    before_count = len(all_proxies)
    filtered = [p for p in all_proxies if p.get("anonymity") not in ("Transparent", "1")]

    removed = before_count - len(filtered)
    if removed > 0:
        logger.info(f"Filtered out {removed} Transparent proxies (don't hide IP).")

    return filtered


def _log_quality_statistics(proxies: List[Dict[str, Any]]) -> None:
    """Log quality check statistics for proxies that were quality-checked."""
    quality_checked = [p for p in proxies if "quality_checked_at" in p]

    if not quality_checked:
        logger.info("No quality checks were performed on proxies.")
        return

    ip_passed = sum(1 for p in quality_checked if p.get("ip_check_passed"))
    target_passed = sum(1 for p in quality_checked if p.get("target_passed"))
    both_passed = sum(1 for p in quality_checked if p.get("ip_check_passed") and p.get("target_passed"))

    logger.info(
        f"Quality statistics: {len(quality_checked)} proxies checked. "
        f"Passed both checks: {both_passed}, IP check: {ip_passed}, Target only: {target_passed}"
    )


def _save_proxy_files(proxies: List[Dict[str, Any]]) -> None:
    """Save proxies to JSON and TXT files."""
    json_output = PROXIES_DIR / "live_proxies.json"
    txt_output = PROXIES_DIR / "live_proxies.txt"

    with open(json_output, "w") as f:
        json.dump(proxies, f, indent=2)

    with open(txt_output, "w") as f:
        for proxy in proxies:
            protocol = proxy.get("protocol", "http")
            f.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")

    logger.info(f"Successfully saved {len(proxies)} live proxies from all workers.")


def _mark_job_complete(job_id: str, result_count: int) -> None:
    """Mark job as complete in Redis with result count."""
    if not job_id:
        return

    try:
        r = get_redis_client()
        r.setex(f"proxy_refresh:{job_id}:status", PROGRESS_KEY_TTL, "COMPLETE")
        r.setex(f"proxy_refresh:{job_id}:completed_at", PROGRESS_KEY_TTL, int(time.time()))
        r.setex(f"proxy_refresh:{job_id}:result_count", PROGRESS_KEY_TTL, result_count)
        logger.info(f"Job {job_id} marked as COMPLETE with {result_count} proxies")
    except Exception as e:
        logger.warning(f"Failed to update Redis completion status: {e}")


@celery_app.task
def process_check_results_task(results: List[List[Dict[str, Any]]], job_id: str = ""):
    """
    Callback task that collects results from all chunk tasks,
    combines them, and saves the final master list.

    Args:
        results: List of results from all chunk tasks
        job_id: Job ID for Redis progress tracking (from dispatcher)
    """
    logger.info(f"Processing results from all proxy check workers (job_id: {job_id})...")

    all_proxies = _flatten_and_filter_results(results)

    if not all_proxies:
        logger.warning("No live proxies were found across all chunks.")
        _mark_job_complete(job_id, 0)
        return "Completed: No live proxies found."

    _log_quality_statistics(all_proxies)
    sorted_proxies = sorted(all_proxies, key=lambda p: p.get("timeout", 999))
    _save_proxy_files(sorted_proxies)
    _mark_job_complete(job_id, len(sorted_proxies))

    return f"Completed: Saved {len(sorted_proxies)} live proxies."


@celery_app.task
def scrape_and_check_chain_task():
    """
    Meta-task that triggers the full scrape+check chain.

    Used by Celery beat to ensure scrape and check always run together.
    This avoids the fire-and-forget problem of separate beat tasks.
    """
    from celery import chain

    logger.info("Starting scrape+check chain...")
    refresh_chain = chain(scrape_new_proxies_task.s(), check_scraped_proxies_task.s())
    result = refresh_chain.delay()
    logger.info(f"Scrape+check chain dispatched (task_id: {result.id})")
    return f"Chain dispatched: {result.id}"
