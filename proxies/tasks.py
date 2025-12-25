import json
import logging
import re
import shlex
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from celery import group

from celery_app import celery_app
from paths import MUBENG_EXECUTABLE_PATH, PROXIES_DIR, PROXY_CHECKER_DIR, PSC_EXECUTABLE_PATH
from proxies.anonymity_checker import enrich_proxy_with_anonymity, get_real_ip
from proxies.quality_checker import enrich_proxy_with_quality

logger = logging.getLogger(__name__)


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


@celery_app.task
def check_scraped_proxies_task(_previous_result=None):
    """
    Dispatcher task that splits the scraped proxy list into chunks
    and sends them to worker tasks to be checked in parallel.
    """
    logger.info("Starting parallel proxy check dispatcher...")
    psc_output_file = PROXY_CHECKER_DIR / "out" / "proxies_pretty.json"
    if not psc_output_file.exists() or psc_output_file.stat().st_size == 0:
        raise FileNotFoundError("Scraped proxy file not found or is empty.")

    with open(psc_output_file, "r") as f:
        all_proxies = json.load(f)

    chunk_size = 100  # Process 100 proxies per task
    proxy_chunks = [all_proxies[i : i + chunk_size] for i in range(0, len(all_proxies), chunk_size)]
    logger.info(f"Split {len(all_proxies)} proxies into {len(proxy_chunks)} chunks of {chunk_size}.")

    # Create a group of parallel tasks
    parallel_tasks = group(check_proxy_chunk_task.s(chunk) for chunk in proxy_chunks)

    # Execute the group and define a callback task to process the results
    callback = process_check_results_task.s()
    # This creates a chain: group runs in parallel, then callback runs with results
    (parallel_tasks | callback).delay()

    logger.info("Dispatched all proxy check chunks to workers.")
    return f"Dispatched {len(proxy_chunks)} chunks for processing."


@celery_app.task
def check_proxy_chunk_task(proxy_chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Worker task that checks a small chunk of proxies for liveness and returns the live ones.
    Uses mubeng binary for fast parallel liveness checking.
    """
    live_proxies_in_chunk = []
    chunk_size = len(proxy_chunk)

    # Create temp input file with proxy URLs
    # IMPORTANT: Must close file before mubeng reads it (flush alone is not enough)
    temp_input_path = Path(tempfile.mktemp(suffix=".txt"))
    with open(temp_input_path, "w") as temp_input_file:
        for proxy in proxy_chunk:
            protocol = proxy.get("protocol", "http")
            temp_input_file.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")
    # File is now closed and flushed

    # Create temp output file path
    temp_output_path = Path(tempfile.mktemp(suffix=".txt"))

    try:
        # Mubeng command with explicit timeout (critical for reliability)
        mubeng_cmd = [
            str(MUBENG_EXECUTABLE_PATH),
            "--check",
            "-f", str(temp_input_path),
            "-o", str(temp_output_path),
            "-t", "10s",  # 10 second timeout per proxy (default is 30s)
        ]
        # Wrap with `script` to provide PTY - mubeng hangs without terminal
        cmd = ["script", "-q", "/dev/null", "-c", shlex.join(mubeng_cmd)]
        # Use check=False to handle errors manually (mubeng returns non-zero for various reasons)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)

        if result.returncode != 0 and result.stderr:
            logger.warning(f"Mubeng returned non-zero ({result.returncode}): {result.stderr[:200]}")

        # Read results AFTER mubeng completes
        if temp_output_path.exists():
            with open(temp_output_path, "r") as f:
                live_proxy_urls = [line.strip() for line in f if line.strip()]
        else:
            live_proxy_urls = []

        # Enrich the live proxies found in this chunk
        proxy_data_map = {f"{p['host']}:{p['port']}": p for p in proxy_chunk}
        for proxy_url in live_proxy_urls:
            match = re.search(r"://(.*?:\d+)", proxy_url)
            if match and (host_port := match.group(1)) in proxy_data_map:
                live_proxies_in_chunk.append(proxy_data_map[host_port])

        logger.info(f"Chunk liveness check: {len(live_proxies_in_chunk)}/{chunk_size} proxies alive")

        # Check anonymity level for each live proxy
        if live_proxies_in_chunk:
            logger.info(f"Checking anonymity for {len(live_proxies_in_chunk)} live proxies...")
            for proxy in live_proxies_in_chunk:
                enrich_proxy_with_anonymity(proxy, timeout=10)

            # Count anonymity levels
            anon_counts = {}
            for p in live_proxies_in_chunk:
                level = p.get("anonymity", "Unknown")
                anon_counts[level] = anon_counts.get(level, 0) + 1
            logger.info(f"Anonymity check complete: {anon_counts}")

            # Filter out proxies where exit_ip is in same /24 subnet as our real IP
            # (proxy not actually working, just routing through local connection)
            real_ip = get_real_ip()
            if real_ip:
                # Extract /24 subnet (first 3 octets)
                real_ip_prefix = ".".join(real_ip.split(".")[:3])
                before_filter = len(live_proxies_in_chunk)
                live_proxies_in_chunk = [
                    p for p in live_proxies_in_chunk
                    if p.get("exit_ip") and not p.get("exit_ip", "").startswith(real_ip_prefix + ".")
                ]
                filtered = before_filter - len(live_proxies_in_chunk)
                if filtered > 0:
                    logger.info(f"Filtered {filtered} proxies with exit_ip in same /24 as real IP {real_ip_prefix}.x (not actually proxying)")

        # Quality check stage: Only check non-transparent proxies
        quality_candidates = [
            p for p in live_proxies_in_chunk
            if p.get("anonymity") not in ("Transparent", "1")
        ]

        if quality_candidates:
            logger.info(f"Checking quality for {len(quality_candidates)} non-transparent proxies...")
            for proxy in quality_candidates:
                enrich_proxy_with_quality(proxy, timeout=60)

            # Count quality results
            ip_passed = sum(1 for p in quality_candidates if p.get("ip_check_passed"))
            target_passed = sum(1 for p in quality_candidates if p.get("target_passed"))
            both_passed = sum(
                1 for p in quality_candidates
                if p.get("ip_check_passed") and p.get("target_passed")
            )
            logger.info(
                f"Quality check complete: {both_passed}/{len(quality_candidates)} passed both checks "
                f"(IP: {ip_passed}, Target: {target_passed})"
            )

    except subprocess.TimeoutExpired:
        logger.error(f"Mubeng check timed out after 120s for chunk of {chunk_size} proxies")
    except Exception as e:
        logger.error(f"Mubeng check failed for a chunk: {e}")
    finally:
        temp_input_path.unlink(missing_ok=True)
        temp_output_path.unlink(missing_ok=True)

    return live_proxies_in_chunk


@celery_app.task
def process_check_results_task(results: List[List[Dict[str, Any]]]):
    """
    Callback task that collects results from all chunk tasks,
    combines them, and saves the final master list.

    Logs quality check statistics but does not filter by quality.
    Users can filter the live_proxies.json file based on ip_check_passed/target_passed fields.
    """
    logger.info("Processing results from all proxy check workers...")
    all_live_proxies = [proxy for chunk_result in results for proxy in chunk_result if proxy]

    # Filter out Transparent proxies (anonymity level 1) - they don't hide your IP
    before_filter = len(all_live_proxies)
    all_live_proxies = [
        p for p in all_live_proxies
        if p.get("anonymity") not in ("Transparent", "1")
    ]
    filtered_count = before_filter - len(all_live_proxies)
    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} Transparent proxies (don't hide IP).")

    if not all_live_proxies:
        logger.warning("No live proxies were found across all chunks.")
        return "Completed: No live proxies found."

    # Log quality check statistics (if quality checks were performed)
    quality_checked = [p for p in all_live_proxies if "quality_checked_at" in p]
    if quality_checked:
        ip_passed = sum(1 for p in quality_checked if p.get("ip_check_passed"))
        target_passed = sum(1 for p in quality_checked if p.get("target_passed"))
        both_passed = sum(
            1 for p in quality_checked
            if p.get("ip_check_passed") and p.get("target_passed")
        )
        logger.info(
            f"Quality statistics: {len(quality_checked)} proxies checked. "
            f"Passed both checks: {both_passed}, "
            f"IP check: {ip_passed}, "
            f"Target only: {target_passed}"
        )
    else:
        logger.info("No quality checks were performed on proxies.")

    # Sort by timeout (speed)
    all_live_proxies.sort(key=lambda p: p.get("timeout", 999))

    json_output = PROXIES_DIR / "live_proxies.json"
    txt_output = PROXIES_DIR / "live_proxies.txt"

    # Overwrite the master files with the new, complete list
    with open(json_output, "w") as f:
        json.dump(all_live_proxies, f, indent=2)
    with open(txt_output, "w") as f:
        for proxy in all_live_proxies:
            protocol = proxy.get("protocol", "http")
            f.write(f"{protocol}://{proxy['host']}:{proxy['port']}\n")

    logger.info(f"Successfully saved {len(all_live_proxies)} live proxies from all workers.")
    return f"Completed: Saved {len(all_live_proxies)} live proxies."


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
