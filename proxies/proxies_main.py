import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from celery import chain

from config.settings import MIN_PROXIES_TO_START, MIN_PROXIES_FOR_SCRAPING
from paths import PROXIES_DIR
from proxies import proxy_to_url
from utils.utils import free_port

from .mubeng_manager import (
    start_mubeng_rotator_server,
    stop_mubeng_rotator_server as mm_stop_mubeng_rotator,
)
from .tasks import check_scraped_proxies_task, scrape_new_proxies_task

logger = logging.getLogger(__name__)


def get_and_filter_proxies(
    min_live_proxies: int = MIN_PROXIES_TO_START,
) -> Tuple[Optional[Path], List[str]]:
    """
    Load proxies from live_proxies.json, filter out Transparent (exposes IP),
    and write to a temporary file for Mubeng.

    No protocol filtering - that happens at browser level.

    Returns:
        Tuple of (proxy_file_path, ordered_proxy_keys)
        - proxy_file_path: Path to temp file for mubeng, or None on failure
        - ordered_proxy_keys: List of "host:port" strings in file order (for X-Proxy-Offset)
    """
    logger.info(f"Loading proxies with min_live: {min_live_proxies}")
    live_proxies_file = PROXIES_DIR / "live_proxies.json"
    if not live_proxies_file.exists():
        print("[INFO] Live proxies file not found. Triggering a refresh...")
        scrape_new_proxies_task.delay()
        print("[INFO] Scraping task sent to background. Checking will follow. Please wait a moment and retry.")
        return None, []

    with open(live_proxies_file, "r") as f:
        all_proxies = json.load(f)
    print(f"[DEBUG] Loaded {len(all_proxies)} total proxies from {live_proxies_file.name}.")

    # Filter out Transparent proxies - they expose your real IP
    # Keep: Anonymous, Elite, or None/unknown (assume anonymous if not set)
    # Remove: Transparent or "1"
    filtered_proxies = [
        p for p in all_proxies
        if p.get("anonymity") not in ("Transparent", "1")
    ]
    filtered_count = len(all_proxies) - len(filtered_proxies)
    if filtered_count > 0:
        print(f"[DEBUG] Filtered out {filtered_count} Transparent proxies (expose IP).")
    print(f"[DEBUG] {len(filtered_proxies)} anonymous proxies remaining.")

    if len(filtered_proxies) < min_live_proxies:
        logger.warning(
            f"Found only {len(filtered_proxies)} live proxies after filtering, "
            f"which is less than the required {min_live_proxies}. Aborting."
        )
        print(
            f"[ERROR] Found only {len(filtered_proxies)} proxies matching your criteria. "
            f"Required at least {min_live_proxies}. Aborting."
        )
        return None, []

    # Build ordered proxy keys list (for X-Proxy-Offset mapping)
    ordered_proxy_keys = [f"{p['host']}:{p['port']}" for p in filtered_proxies]

    # Write to a temporary file for Mubeng
    try:
        temp_proxy_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", dir=PROXIES_DIR)
        with temp_proxy_file as f:
            for proxy in filtered_proxies:
                f.write(f"{proxy_to_url(proxy['host'], proxy['port'], proxy.get('protocol', 'http'))}\n")
        logger.info(f"Prepared temporary proxy file with {len(filtered_proxies)} proxies: {temp_proxy_file.name}")
        print(f"[SUCCESS] Created temporary proxy list for Mubeng with {len(filtered_proxies)} proxies.")
        return Path(temp_proxy_file.name), ordered_proxy_keys
    except Exception as e:
        logger.error(f"Failed to create temporary proxy file: {e}", exc_info=True)
        print("[ERROR] Failed to create temporary file for Mubeng. See logs for details.")
        return None, []


def _check_and_refresh_proxies():
    """Checks proxy health and triggers a background refresh if needed."""
    live_proxies_file = PROXIES_DIR / "live_proxies.json"
    proxy_count = 0
    if live_proxies_file.exists():
        with open(live_proxies_file, "r") as f:
            try:
                proxy_count = len(json.load(f))
            except json.JSONDecodeError:
                logger.warning("Could not parse live_proxies.json, assuming 0 proxies.")

    if proxy_count < MIN_PROXIES_FOR_SCRAPING:
        logger.warning(
            f"Proxy count ({proxy_count}) is below threshold ({MIN_PROXIES_FOR_SCRAPING}). "
            "Triggering a background refresh via Celery."
        )
        print("[WARNING] Proxy count is low. Starting a refresh in the background...")
        try:
            refresh_chain = chain(scrape_new_proxies_task.s(), check_scraped_proxies_task.s())
            refresh_chain.delay()
            print("[INFO] Background refresh and check tasks have been sent to the Celery worker.")
        except Exception as e:
            logger.error(f"Failed to start background refresh task: {e}", exc_info=True)
            print("[ERROR] Could not start background refresh task. Is Celery running?")


def setup_mubeng_rotator(
    port: int,
    country_codes: Optional[List[str]] = None,
    min_live_proxies: int = MIN_PROXIES_TO_START,
) -> Tuple[Optional[str], Optional[subprocess.Popen], Optional[Path], List[str]]:
    """
    Set up and start the Mubeng proxy rotator with ALL available proxies.

    No protocol filtering at this stage - that happens at browser level.
    Quality filtering happens via pre-flight check after mubeng starts.

    Returns:
        Tuple of (proxy_url, mubeng_process, proxy_file_path, ordered_proxy_keys)
        - proxy_url: Mubeng proxy URL (e.g., "http://localhost:8089")
        - mubeng_process: Popen object for the mubeng process
        - proxy_file_path: Path to the temp proxy file
        - ordered_proxy_keys: List of "host:port" strings for X-Proxy-Offset mapping
    """
    logger.info("Setting up and starting Mubeng rotator...")

    _check_and_refresh_proxies()

    if not free_port(port):
        logger.critical(f"Port {port} is in use and could not be freed. Aborting.")
        return None, None, None, []

    # Load ALL proxies - no protocol/anonymity filtering at this stage
    filtered_proxies_file, ordered_proxy_keys = get_and_filter_proxies(
        min_live_proxies=min_live_proxies,
    )

    if not filtered_proxies_file:
        logger.error("Failed to get a list of filtered proxies for Mubeng.")
        return None, None, None, []

    mubeng_process = start_mubeng_rotator_server(
        live_proxy_file=filtered_proxies_file,
        desired_port=port,
        country_codes=country_codes,
    )

    if not mubeng_process:
        logger.error("Failed to start Mubeng server process.")
        if filtered_proxies_file.exists():
            filtered_proxies_file.unlink(missing_ok=True)
        return None, None, None, []

    proxy_url = f"http://localhost:{port}"
    logger.info(f"Mubeng rotator started successfully at {proxy_url} with {len(ordered_proxy_keys)} proxies")
    return proxy_url, mubeng_process, filtered_proxies_file, ordered_proxy_keys


def stop_mubeng_rotator(process: Optional[subprocess.Popen], temp_file_path: Optional[Path]):
    """Facade to stop the mubeng rotator and clean up its temporary live proxy file."""
    if process:
        logger.info(f"Stopping mubeng rotator server (PID: {process.pid}) via facade.")
        mm_stop_mubeng_rotator(process)

    if temp_file_path and temp_file_path.exists():
        logger.info(f"Deleting temporary live proxy file: {temp_file_path} via facade.")
        try:
            temp_file_path.unlink(missing_ok=True)
        except OSError as e:
            logger.error(f"Error unlinking temp file {temp_file_path} in facade: {e}")


def validate_proxy(proxy: str | dict | None) -> dict | None:
    """Validates and formats the proxy argument for Playwright."""
    if not proxy:
        return None
    if isinstance(proxy, str):
        return {"server": proxy}
    if isinstance(proxy, dict) and "server" in proxy:
        return proxy
    logger.warning(f"Invalid proxy format: {proxy}. It will be ignored.")
    return None
