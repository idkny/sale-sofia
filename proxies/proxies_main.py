import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from celery import chain

import config
from paths import PROXIES_DIR
from proxies import proxy_to_url
from utils.utils import free_port

from .mubeng_manager import (
    start_mubeng_rotator_server,
    stop_mubeng_rotator_server as mm_stop_mubeng_rotator,
)
from .tasks import check_scraped_proxies_task, scrape_new_proxies_task

logger = logging.getLogger(__name__)

MIN_LIVE_PROXIES_DEFAULT = 1


def scrape_proxies():
    """Facade to trigger the proxy scraping Celery task."""
    logger.info("Triggering proxy scraping task via facade...")
    try:
        scrape_new_proxies_task.delay()
        print("[INFO] Proxy scraping task has been sent to the background worker.")
    except Exception as e:
        logger.error(f"Failed to trigger proxy scraping task: {e}", exc_info=True)
        print("[ERROR] Could not trigger proxy scraping task. Is the message broker running?")
        raise


def check_proxies():
    """Facade to trigger the proxy checking Celery task."""
    logger.info("Triggering proxy checking task via facade...")
    try:
        check_scraped_proxies_task.delay()
        print("[INFO] Proxy checking task has been sent to the background worker.")
    except Exception as e:
        logger.error(f"Failed to trigger proxy checking task: {e}", exc_info=True)
        print("[ERROR] Could not trigger proxy checking task. Is the message broker running?")
        raise


def get_and_filter_proxies(
    min_live_proxies: int = MIN_LIVE_PROXIES_DEFAULT,
) -> Optional[Path]:
    """
    Load proxies from live_proxies.json, filter out Transparent (exposes IP),
    and write to a temporary file for Mubeng.

    No protocol filtering - that happens at browser level.
    """
    logger.info(f"Loading proxies with min_live: {min_live_proxies}")
    live_proxies_file = PROXIES_DIR / "live_proxies.json"
    if not live_proxies_file.exists():
        print("[INFO] Live proxies file not found. Triggering a refresh...")
        scrape_new_proxies_task.delay()
        print("[INFO] Scraping task sent to background. Checking will follow. Please wait a moment and retry.")
        return None

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
        return None

    # Write to a temporary file for Mubeng
    try:
        temp_proxy_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", dir=PROXIES_DIR)
        with temp_proxy_file as f:
            for proxy in filtered_proxies:
                f.write(f"{proxy_to_url(proxy['host'], proxy['port'], proxy.get('protocol', 'http'))}\n")
        logger.info(f"Prepared temporary proxy file with {len(filtered_proxies)} proxies: {temp_proxy_file.name}")
        print(f"[SUCCESS] Created temporary proxy list for Mubeng with {len(filtered_proxies)} proxies.")
        return Path(temp_proxy_file.name)
    except Exception as e:
        logger.error(f"Failed to create temporary proxy file: {e}", exc_info=True)
        print("[ERROR] Failed to create temporary file for Mubeng. See logs for details.")
        return None


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

    if proxy_count < config.PROXY_VALID_THRESHOLD:
        logger.warning(
            f"Proxy count ({proxy_count}) is below threshold ({config.PROXY_VALID_THRESHOLD}). "
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
    min_live_proxies: int = MIN_LIVE_PROXIES_DEFAULT,
) -> Tuple[Optional[str], Optional[subprocess.Popen], Optional[Path]]:
    """
    Set up and start the Mubeng proxy rotator with ALL available proxies.

    No protocol filtering at this stage - that happens at browser level.
    Quality filtering happens via pre-flight check after mubeng starts.
    """
    logger.info("Setting up and starting Mubeng rotator...")

    _check_and_refresh_proxies()

    if not free_port(port):
        logger.critical(f"Port {port} is in use and could not be freed. Aborting.")
        return None, None, None

    # Load ALL proxies - no protocol/anonymity filtering at this stage
    filtered_proxies_file = get_and_filter_proxies(
        min_live_proxies=min_live_proxies,
    )

    if not filtered_proxies_file:
        logger.error("Failed to get a list of filtered proxies for Mubeng.")
        return None, None, None

    mubeng_process = start_mubeng_rotator_server(
        live_proxy_file=filtered_proxies_file,
        desired_port=port,
        country_codes=country_codes,
    )

    if not mubeng_process:
        logger.error("Failed to start Mubeng server process.")
        if filtered_proxies_file.exists():
            filtered_proxies_file.unlink(missing_ok=True)
        return None, None, None

    proxy_url = f"http://localhost:{port}"
    logger.info(f"Mubeng rotator started successfully at {proxy_url}")
    return proxy_url, mubeng_process, filtered_proxies_file


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
