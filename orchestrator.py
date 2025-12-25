"""
Process orchestrator for Redis, Celery, and proxy management.

Handles starting/stopping all required services for automated scraping.
Used as a context manager to ensure clean shutdown.

Usage:
    with Orchestrator() as orch:
        orch.start_redis()
        orch.start_celery()
        orch.wait_for_proxies()
        # ... do scraping ...
    # Redis and Celery automatically stopped on exit
"""

import atexit
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from paths import LOGS_DIR, PROXIES_DIR, ROOT_DIR

# Celery log file for debugging
CELERY_LOG_FILE = LOGS_DIR / "celery_worker.log"


class Orchestrator:
    """Manages lifecycle of Redis, Celery, and proxy availability."""

    def __init__(self):
        self.redis_process: Optional[subprocess.Popen] = None
        self.celery_process: Optional[subprocess.Popen] = None
        self.celery_log_handle = None
        self._shutdown_registered = False

    def __enter__(self):
        """Context manager entry."""
        self._register_shutdown_handlers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops all processes."""
        self.stop_all()
        return False  # Don't suppress exceptions

    def _register_shutdown_handlers(self):
        """Register signal handlers for clean shutdown."""
        if self._shutdown_registered:
            return

        def shutdown_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop_all()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)
        atexit.register(self.stop_all)
        self._shutdown_registered = True

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    def _is_redis_running(self) -> bool:
        """Check if Redis is running on default port."""
        return self._is_port_in_use(6379)

    def start_redis(self) -> bool:
        """
        Start Redis if not running.

        Returns:
            True if Redis is available, False otherwise.
        """
        if self._is_redis_running():
            logger.info("Redis is already running")
            print("[INFO] Redis is already running")
            return True

        logger.info("Starting Redis server...")
        print("[INFO] Starting Redis server...")

        try:
            # Start Redis in background
            self.redis_process = subprocess.Popen(
                ["redis-server", "--daemonize", "no"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )

            # Wait for Redis to start
            for _ in range(10):
                time.sleep(0.5)
                if self._is_redis_running():
                    logger.info("Redis started successfully")
                    print("[SUCCESS] Redis started")
                    return True

            # Check if process failed
            if self.redis_process.poll() is not None:
                stderr = self.redis_process.stderr.read().decode() if self.redis_process.stderr else ""
                logger.error(f"Redis failed to start: {stderr}")
                print(f"[ERROR] Redis failed to start: {stderr}")
                return False

            logger.error("Redis did not start in time")
            print("[ERROR] Redis did not start in time")
            return False

        except FileNotFoundError:
            logger.error("redis-server not found. Install Redis first.")
            print("[ERROR] redis-server not found. Install with: sudo apt install redis-server")
            return False
        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            print(f"[ERROR] Failed to start Redis: {e}")
            return False

    def _is_celery_running_systemwide(self) -> bool:
        """Check if any Celery worker is already running on the system."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "celery -A celery_app.*worker"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def start_celery(self) -> bool:
        """
        Start Celery worker with beat scheduler.

        Logs output to data/logs/celery_worker.log for debugging.
        If a worker is already running system-wide, reuses it.

        Returns:
            True if Celery started/running, False otherwise.
        """
        # Check if a worker is already running system-wide
        if self._is_celery_running_systemwide():
            logger.info("Celery worker already running - reusing existing worker")
            print("[INFO] Celery worker already running - reusing existing worker")
            return True

        logger.info("Starting Celery worker with beat scheduler...")
        print("[INFO] Starting Celery worker...")

        try:
            # Open log file for Celery output
            CELERY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.celery_log_handle = open(CELERY_LOG_FILE, "w")

            # Start Celery worker + beat in one process
            # IMPORTANT: Must specify -Q sale_sofia to consume from the correct queue
            # Beat schedule sends tasks to 'sale_sofia' queue
            # Using start_new_session=True to detach from parent terminal
            # This prevents Celery from stopping when main.py is interrupted
            self.celery_process = subprocess.Popen(
                [
                    "celery",
                    "-A", "celery_app",
                    "worker",
                    "--beat",
                    "-Q", "celery,sale_sofia",  # Consume from both queues
                    "--loglevel=info",  # More verbose for debugging
                    "--concurrency=8",
                ],
                cwd=ROOT_DIR,
                stdin=subprocess.DEVNULL,  # Detach from terminal input
                stdout=self.celery_log_handle,
                stderr=subprocess.STDOUT,  # Merge stderr to stdout (log file)
                env={**os.environ, "PYTHONPATH": str(ROOT_DIR)},
                start_new_session=True,  # Detach from parent process group
            )

            # Give Celery time to start (check every 0.5s for 5s)
            for i in range(10):
                time.sleep(0.5)
                if self.celery_process.poll() is not None:
                    # Process died - read log for error
                    self.celery_log_handle.flush()
                    with open(CELERY_LOG_FILE, "r") as f:
                        log_content = f.read()
                    logger.error(f"Celery exited early. Log:\n{log_content[-2000:]}")
                    print(f"[ERROR] Celery failed. Check: {CELERY_LOG_FILE}")
                    return False

            logger.info(f"Celery worker started (PID: {self.celery_process.pid})")
            print(f"[SUCCESS] Celery worker started (log: {CELERY_LOG_FILE})")
            return True

        except FileNotFoundError:
            logger.error("celery not found. Install with: pip install celery")
            print("[ERROR] celery not found. Is it installed?")
            return False
        except Exception as e:
            logger.error(f"Failed to start Celery: {e}")
            print(f"[ERROR] Failed to start Celery: {e}")
            return False

    def is_celery_alive(self) -> bool:
        """Check if Celery worker process is still running."""
        # First check our own process
        if self.celery_process and self.celery_process.poll() is None:
            return True
        # Fall back to system-wide check (in case we're reusing external worker)
        return self._is_celery_running_systemwide()

    def restart_celery_if_dead(self) -> bool:
        """Restart Celery if it died. Returns True if running after check."""
        if self.is_celery_alive():
            return True

        logger.warning("Celery worker died! Restarting...")
        print("[WARNING] Celery worker died! Restarting...")

        # Close old log handle
        if self.celery_log_handle:
            self.celery_log_handle.close()
            self.celery_log_handle = None

        return self.start_celery()

    def get_proxy_count(self) -> int:
        """Get the current number of live proxies."""
        live_proxies_file = PROXIES_DIR / "live_proxies.json"
        if not live_proxies_file.exists():
            return 0

        try:
            with open(live_proxies_file, "r") as f:
                proxies = json.load(f)
                return len(proxies) if proxies else 0
        except (json.JSONDecodeError, IOError):
            return 0

    def get_usable_proxy_count(self) -> int:
        """
        Get count of usable proxies (non-Transparent).

        Filters out Transparent proxies that expose your real IP.
        No protocol filtering - that happens at browser level.
        """
        live_proxies_file = PROXIES_DIR / "live_proxies.json"
        if not live_proxies_file.exists():
            return 0

        try:
            with open(live_proxies_file, "r") as f:
                proxies = json.load(f)

            if not proxies:
                return 0

            # Filter out Transparent proxies (expose your IP)
            # Keep: Anonymous, Elite, or None/unknown (assume anonymous if not set)
            filtered = [
                p for p in proxies
                if p.get("anonymity") not in ("Transparent", "1")
            ]

            return len(filtered)
        except (json.JSONDecodeError, IOError):
            return 0

    def get_proxy_file_mtime(self) -> float:
        """Get the modification time of live_proxies.json."""
        live_proxies_file = PROXIES_DIR / "live_proxies.json"
        if live_proxies_file.exists():
            return live_proxies_file.stat().st_mtime
        return 0.0

    def get_task_state(self, task_id: str) -> tuple[str, Optional[str]]:
        """
        Get the state of a Celery task.

        Args:
            task_id: The Celery task ID to check.

        Returns:
            Tuple of (state, result):
            - state: PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
            - result: Task result if SUCCESS, error message if FAILURE, else None
        """
        try:
            from celery.result import AsyncResult
            from celery_app import celery_app

            result = AsyncResult(task_id, app=celery_app)
            state = result.state

            if state == "SUCCESS":
                return state, str(result.result)
            elif state == "FAILURE":
                return state, str(result.result) if result.result else "Unknown error"
            else:
                return state, None
        except Exception as e:
            logger.warning(f"Failed to get task state for {task_id}: {e}")
            return "UNKNOWN", str(e)

    def trigger_proxy_refresh(self) -> tuple[float, Optional[str]]:
        """
        Trigger a proxy refresh via Celery task (scrape + check).

        Returns:
            Tuple of (mtime_before, task_id):
            - mtime_before: File mtime BEFORE refresh started
            - task_id: The Celery chain task ID for tracking (or None on error)
        """
        mtime_before = self.get_proxy_file_mtime()
        task_id = None

        try:
            from celery import chain
            from proxies.tasks import check_scraped_proxies_task, scrape_new_proxies_task

            # Chain: scrape new proxies -> check them
            refresh_chain = chain(scrape_new_proxies_task.s(), check_scraped_proxies_task.s())
            result = refresh_chain.delay()
            task_id = result.id
            logger.info(f"Proxy refresh chain triggered (task_id: {task_id})")
            print(f"[INFO] Proxy refresh task sent to Celery (task_id: {task_id})")
        except Exception as e:
            logger.error(f"Failed to trigger proxy refresh: {e}")
            print(f"[ERROR] Failed to trigger proxy refresh: {e}")

        return mtime_before, task_id

    def wait_for_proxies(self, min_count: int = 5, timeout: int = 2400) -> bool:
        """
        Wait for USABLE proxies to be available.

        Checks filtered proxy count (http/https + Anonymous/Elite).
        Triggers a refresh if count is below threshold.

        Args:
            min_count: Minimum number of usable proxies required.
            timeout: Maximum seconds to wait (default 40 minutes).

        Returns:
            True if usable proxies available, False if timeout.
        """
        total_count = self.get_proxy_count()
        usable_count = self.get_usable_proxy_count()

        logger.info(f"Proxy counts - Total: {total_count}, Usable: {usable_count}")
        print(f"[INFO] Proxy counts - Total: {total_count}, Usable (non-transparent): {usable_count}")

        if usable_count >= min_count:
            print(f"[SUCCESS] {usable_count} usable proxies available")
            return True

        # Trigger refresh
        print(f"[INFO] Need at least {min_count} usable proxies, triggering refresh...")
        print("[INFO] This may take 2-5 minutes (scraping + checking proxies)...")
        mtime_before, task_id = self.trigger_proxy_refresh()

        # Wait loop
        start_time = time.time()
        check_interval = 15  # seconds

        while time.time() - start_time < timeout:
            # Check if Celery is still alive (restart if died)
            if not self.restart_celery_if_dead():
                logger.error("Celery failed to restart")
                print("[ERROR] Celery worker cannot be restarted")
                return False

            usable_count = self.get_usable_proxy_count()
            elapsed = int(time.time() - start_time)

            if usable_count >= min_count:
                print(f"[SUCCESS] {usable_count} usable proxies available after {elapsed}s")
                return True

            # Show progress every check
            total = self.get_proxy_count()
            celery_status = "alive" if self.is_celery_alive() else "DEAD"
            print(f"[WAIT] {usable_count}/{total} usable proxies... ({elapsed}s, celery: {celery_status})")
            time.sleep(check_interval)

        logger.error(f"Timeout waiting for proxies after {timeout}s")
        print(f"[ERROR] Timeout waiting for proxies after {timeout}s")
        return False

    def wait_for_refresh_completion(
        self,
        mtime_before: float,
        min_count: int = 5,
        timeout: int = 0,  # 0 = no timeout, wait forever
        task_id: Optional[str] = None,
    ) -> bool:
        """
        Wait for a proxy refresh to complete by monitoring task state and file modification time.

        This is used after pre-flight check failure when we KNOW current proxies are bad
        and need to wait for actually NEW proxies, not just check the count.

        Args:
            mtime_before: The file mtime before refresh was triggered.
            min_count: Minimum number of usable proxies required.
            timeout: Maximum seconds to wait (0 = wait forever until task completes).
            task_id: Optional Celery task ID to track state (more reliable than mtime).

        Returns:
            True if new proxies available, False if failure.
        """
        start_time = time.time()
        check_interval = 15  # seconds
        pending_warn_threshold = 120  # Warn if PENDING for > 2 min (queue issue)

        print("[INFO] Waiting for proxy refresh to complete...")
        print("[INFO] proxy-scraper-checker typically takes 5-15 minutes. Will wait until done.")

        while True:
            # Check if Celery is still alive (restart if died)
            if not self.restart_celery_if_dead():
                logger.error("Celery failed to restart")
                print("[ERROR] Celery worker cannot be restarted")
                return False

            elapsed = int(time.time() - start_time)

            # Check task state if we have a task_id
            task_state = None
            if task_id:
                task_state, task_result = self.get_task_state(task_id)
                if task_state == "FAILURE":
                    logger.error(f"Refresh task failed: {task_result}")
                    print(f"[ERROR] Refresh task failed: {task_result}")
                    return False
                elif task_state == "SUCCESS":
                    logger.info(f"Refresh task completed: {task_result}")
                    # Task done - check proxy count
                    usable_count = self.get_usable_proxy_count()
                    if usable_count >= min_count:
                        print(f"[SUCCESS] Refresh complete! {usable_count} usable proxies after {elapsed}s")
                        return True
                    else:
                        print(f"[WARNING] Task completed but only {usable_count} usable proxies (need {min_count})")
                        # Don't return False - maybe more proxies are coming from chunk tasks
                        # Wait a bit more for process_check_results_task to finish
                        time.sleep(30)
                        usable_count = self.get_usable_proxy_count()
                        if usable_count >= min_count:
                            print(f"[SUCCESS] Refresh complete! {usable_count} usable proxies after waiting")
                            return True
                        return False
                elif task_state == "PENDING" and elapsed > pending_warn_threshold:
                    # Task stuck in PENDING - likely queue issue
                    print(f"[WARNING] Task still PENDING after {elapsed}s - possible queue issue")
                    print("[INFO] Check: celery worker might not be consuming from correct queue")

            # Fallback: Check if file has been updated (for when task_id not available)
            current_mtime = self.get_proxy_file_mtime()
            if current_mtime > mtime_before:
                # File was updated - check if we have enough proxies
                usable_count = self.get_usable_proxy_count()
                if usable_count >= min_count:
                    print(f"[SUCCESS] Refresh complete! {usable_count} new usable proxies after {elapsed}s")
                    return True
                else:
                    print(f"[INFO] File updated but only {usable_count} usable proxies so far (need {min_count})")
                    # Continue waiting - chunk tasks may still be running
                    mtime_before = current_mtime

            # Show progress with task state
            celery_status = "alive" if self.is_celery_alive() else "DEAD"
            task_info = f", task: {task_state}" if task_state else ""
            mins = elapsed // 60
            secs = elapsed % 60
            print(f"[WAIT] Refresh in progress... ({mins}m {secs}s elapsed, celery: {celery_status}{task_info})")
            time.sleep(check_interval)

            # Optional timeout (if set > 0)
            if timeout > 0 and elapsed >= timeout:
                logger.error(f"Timeout waiting for proxy refresh after {timeout}s")
                print(f"[ERROR] Timeout waiting for proxy refresh after {timeout}s")
                return False

    def stop_all(self):
        """Stop all managed processes."""
        logger.info("Stopping all orchestrated processes...")

        # Stop Celery first (it depends on Redis)
        if self.celery_process and self.celery_process.poll() is None:
            logger.info("Stopping Celery worker...")
            print("[INFO] Stopping Celery worker...")
            self.celery_process.terminate()
            try:
                self.celery_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.celery_process.kill()
            self.celery_process = None

        # Close Celery log handle
        if self.celery_log_handle:
            self.celery_log_handle.close()
            self.celery_log_handle = None

        # Stop Redis
        if self.redis_process and self.redis_process.poll() is None:
            logger.info("Stopping Redis server...")
            print("[INFO] Stopping Redis server...")
            self.redis_process.terminate()
            try:
                self.redis_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.redis_process.kill()
            self.redis_process = None

        print("[INFO] All processes stopped")
