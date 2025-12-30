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
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import psutil
import redis
from loguru import logger

from paths import LOGS_DIR, PROXIES_DIR, ROOT_DIR
from config.settings import MIN_PROXIES_FOR_SCRAPING
from proxies.redis_keys import (
    job_completed_chunks_key,
    job_result_count_key,
    job_status_key,
    job_total_chunks_key,
)

# Celery log file for debugging
CELERY_LOG_FILE = LOGS_DIR / "celery_worker.log"


@dataclass
class DispatchResult:
    """Result from waiting for chain dispatch to complete."""

    job_id: Optional[str] = None
    chord_id: Optional[str] = None
    total_chunks: int = 0
    success: bool = True
    error: Optional[str] = None


class Orchestrator:
    """Manages lifecycle of Redis, Celery, and proxy availability."""

    def __init__(self):
        self.redis_process: Optional[subprocess.Popen] = None
        self.celery_process: Optional[subprocess.Popen] = None
        self.celery_log_handle = None
        self._shutdown_registered = False
        self._redis_client: Optional[redis.Redis] = None

    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for progress tracking."""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_BROKER_DB", "0")),
                decode_responses=True,
            )
        return self._redis_client

    def get_refresh_progress(self, job_id: str) -> Dict[str, Any]:
        """
        Get progress of a proxy refresh job from Redis.

        Args:
            job_id: The job ID (dispatcher task ID)

        Returns:
            Dict with: job_id, total_chunks, completed_chunks, status, progress_pct
        """
        try:
            r = self._get_redis_client()
            total = r.get(job_total_chunks_key(job_id))
            completed = r.get(job_completed_chunks_key(job_id))
            status = r.get(job_status_key(job_id))
            result_count = r.get(job_result_count_key(job_id))

            total_int = int(total) if total else 0
            completed_int = int(completed) if completed else 0

            return {
                "job_id": job_id,
                "total_chunks": total_int,
                "completed_chunks": completed_int,
                "status": status if status else "UNKNOWN",
                "progress_pct": (completed_int / total_int * 100) if total_int > 0 else 0,
                "result_count": int(result_count) if result_count else None,
            }
        except Exception as e:
            logger.warning(f"Failed to get refresh progress for {job_id}: {e}")
            return {
                "job_id": job_id,
                "total_chunks": 0,
                "completed_chunks": 0,
                "status": "ERROR",
                "progress_pct": 0,
                "result_count": None,
            }

    def start_site_scraping(self, site_name: str, start_urls: list) -> dict:
        """Dispatch site scraping task."""
        from scraping.tasks import dispatch_site_scraping

        result = dispatch_site_scraping.delay(site_name, start_urls)
        return {"task_id": result.id, "site": site_name}

    def start_all_sites_scraping(self, sites_config: dict) -> dict:
        """Dispatch all sites in parallel."""
        from scraping.tasks import scrape_all_sites

        result = scrape_all_sites.delay(sites_config)
        return {"group_id": result.id}

    def get_scraping_progress(self, job_id: str) -> dict:
        """Get scraping job progress from Redis."""
        from scraping.redis_keys import ScrapingKeys

        r = self._get_redis_client()
        return {
            "job_id": job_id,
            "status": r.get(ScrapingKeys.status(job_id)) or "UNKNOWN",
            "total_chunks": int(r.get(ScrapingKeys.total_chunks(job_id)) or 0),
            "completed_chunks": int(r.get(ScrapingKeys.completed_chunks(job_id)) or 0),
            "result_count": int(r.get(ScrapingKeys.result_count(job_id)) or 0),
            "error_count": int(r.get(ScrapingKeys.error_count(job_id)) or 0),
        }

    def __enter__(self):
        """Context manager entry."""
        print("[INFO] Cleaning up stale processes...")
        self.cleanup_stale_processes()
        self._register_shutdown_handlers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stops all processes."""
        self.stop_all()
        return False  # Don't suppress exceptions

    def cleanup_stale_processes(self) -> int:
        """
        Kill stale celery and mubeng processes from crashed sessions.

        Returns:
            Count of processes killed.
        """
        killed = 0
        # Pattern matches: celery -A celery_app worker (the actual command)
        # More specific to avoid matching Python processes that import celery
        killed += self._kill_process_by_pattern(r"celery\s+-A\s+\S+\s+worker")
        killed += self._kill_process_by_pattern(r"mubeng")
        if killed > 0:
            logger.info(f"Cleaned up {killed} stale processes")
            print(f"[INFO] Cleaned up {killed} stale processes")
        else:
            logger.debug("No stale processes found")
        return killed

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

    def _kill_process_by_pattern(self, pattern: str) -> int:
        """Kill all processes matching pattern. Returns count killed."""
        killed = 0
        for proc in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if re.search(pattern, cmdline):
                    logger.info(f"Killing stale process: PID {proc.pid} - {cmdline[:80]}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        logger.warning(f"Process {proc.pid} did not terminate, killing...")
                        proc.kill()
                        proc.wait(timeout=2)
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed

    def _health_check_redis(self) -> bool:
        """Check if Redis is healthy by sending PING command."""
        try:
            client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                socket_timeout=2.0,
            )
            return client.ping()
        except (redis.ConnectionError, redis.TimeoutError, redis.RedisError):
            return False

    def _health_check_celery(self) -> bool:
        """Check if Celery worker is healthy by sending ping."""
        try:
            from celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=5.0)
            ping_result = inspect.ping()
            return ping_result is not None and len(ping_result) > 0
        except Exception:
            return False

    def start_redis(self) -> bool:
        """
        Start Redis if not running.

        Returns:
            True if Redis is available, False otherwise.
        """
        # Check if Redis is already running and healthy
        if self._health_check_redis():
            logger.info("Redis is already running and healthy")
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

            # Wait for Redis to start and be healthy (PING responds)
            for _ in range(10):
                time.sleep(0.5)
                if self._health_check_redis():
                    logger.info("Redis started and healthy (PING OK)")
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
        # Check if a worker is already running and responding to pings
        if self._health_check_celery():
            logger.info("Celery worker already running and healthy")
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

            # Wait for Celery worker to respond to health check (up to 15s more)
            logger.info(f"Celery process started (PID: {self.celery_process.pid}), waiting for health check...")
            for i in range(15):
                if self._health_check_celery():
                    logger.info("Celery worker healthy (ping OK)")
                    print(f"[SUCCESS] Celery worker started (log: {CELERY_LOG_FILE})")
                    return True
                time.sleep(1)

            # Process is running but not responding to pings
            logger.warning("Celery started but not responding to ping, continuing anyway")
            print(f"[WARNING] Celery started but ping check failed (log: {CELERY_LOG_FILE})")
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

    def wait_for_proxies(self, min_count: int = MIN_PROXIES_FOR_SCRAPING, timeout: int = 2400) -> bool:
        """
        Wait for USABLE proxies to be available.

        Checks filtered proxy count (http/https + Anonymous/Elite).
        Triggers a refresh if count is below threshold.

        Args:
            min_count: Minimum number of usable proxies required.
            timeout: Timeout is a safety net fallback only (default 40 minutes).
                     Primary wait mechanism is Celery chord completion signal.

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
        mtime_before, task_id = self.trigger_proxy_refresh()

        # Use signal-based wait (chord/Redis) instead of blind file polling
        # Pass timeout to enforce caller's timeout preference (default 2400s)
        return self.wait_for_refresh_completion(mtime_before, min_count, timeout=timeout, task_id=task_id)

    def wait_for_refresh_completion(
        self,
        mtime_before: float,
        min_count: int = MIN_PROXIES_FOR_SCRAPING,
        timeout: int = 0,
        task_id: Optional[str] = None,
    ) -> bool:
        """
        Wait for a proxy refresh to complete.

        Tries multiple strategies in order:
        1. Chord-based wait (most reliable)
        2. Redis progress polling (fallback)
        3. File modification monitoring (last resort)

        Args:
            mtime_before: File mtime before refresh (for fallback).
            min_count: Minimum usable proxies required.
            timeout: Max seconds to wait (0 = forever).
            task_id: Celery chain task ID to track.

        Returns:
            True if sufficient proxies available, False on failure.
        """
        start_time = time.time()
        check_interval = 15

        print("[INFO] Waiting for proxy refresh to complete...")

        # Phase 1: Wait for chain dispatch to get job_id/chord_id
        dispatch = self._wait_for_chain_dispatch(task_id, start_time, check_interval)
        if not dispatch.success:
            return False

        # Phase 2: Try chord-based wait (preferred) with fallback
        if dispatch.chord_id:
            chord_result = self._wait_via_chord(
                dispatch.chord_id, dispatch.job_id, start_time, timeout, min_count, check_interval,
                total_chunks=dispatch.total_chunks
            )
            # chord_result: True/False = chord completed (return as-is), None = timeout/failure (try fallback)
            if chord_result is not None or not dispatch.job_id:
                return chord_result if chord_result is not None else False
            # Chord timed out or failed - fall back to Redis polling
            print("[INFO] Chord timed out or failed, falling back to Redis polling...")

        # Phase 3: Try Redis progress polling
        if dispatch.job_id:
            return self._wait_via_redis_polling(
                dispatch.job_id, start_time, timeout, min_count, check_interval
            )

        # Phase 4: File-based fallback
        return self._wait_via_file_monitoring(
            mtime_before, start_time, timeout, min_count, check_interval
        )

    def _wait_for_chain_dispatch(
        self, task_id: Optional[str], start_time: float, check_interval: int
    ) -> DispatchResult:
        """Wait for chain task to complete and extract job_id/chord_id."""
        import ast

        if not task_id:
            return DispatchResult()  # No task to wait for

        pending_warn_threshold = 120

        while True:
            if not self.restart_celery_if_dead():
                return DispatchResult(success=False, error="Celery failed to restart")

            elapsed = int(time.time() - start_time)
            mins, secs = elapsed // 60, elapsed % 60
            task_state, task_result = self.get_task_state(task_id)

            if task_state == "FAILURE":
                logger.error(f"Refresh task failed: {task_result}")
                print(f"[ERROR] Refresh task failed: {task_result}")
                return DispatchResult(success=False, error=str(task_result))

            if task_state == "SUCCESS":
                return self._parse_dispatch_result(task_result)

            if task_state == "PENDING" and elapsed > pending_warn_threshold:
                print(f"[WARNING] Chain task still PENDING after {mins}m {secs}s")

            if task_state in ("STARTED", "PENDING"):
                print(f"[WAIT] Scrape/dispatch in progress... ({mins}m {secs}s, task: {task_state})")

            time.sleep(check_interval)

    def _parse_dispatch_result(self, task_result: Any) -> DispatchResult:
        """Parse dispatcher result to extract job_id and chord_id."""
        import ast

        logger.info(f"Dispatcher completed: {task_result}")
        try:
            result_dict = ast.literal_eval(task_result) if isinstance(task_result, str) else task_result
            if isinstance(result_dict, dict) and "job_id" in result_dict:
                job_id = result_dict["job_id"]
                chord_id = result_dict.get("chord_id")
                total_chunks = result_dict.get("total_chunks", 0)
                print(f"[INFO] Dispatcher done. Job {job_id} ({total_chunks} chunks)")
                if chord_id:
                    print(f"[INFO] Using chord_id {chord_id} for event-based wait")
                else:
                    print("[INFO] No chord_id - falling back to Redis progress tracking")
                return DispatchResult(job_id=job_id, chord_id=chord_id, total_chunks=total_chunks)
        except Exception as e:
            logger.warning(f"Failed to parse dispatcher result: {e}")

        logger.warning("Dispatcher returned old format, using file-based fallback")
        return DispatchResult()

    def _wait_via_chord(
        self,
        chord_id: str,
        job_id: Optional[str],
        start_time: float,
        timeout: int,
        min_count: int,
        check_interval: int,
        total_chunks: int = 0,
    ) -> Optional[bool]:
        """Wait for chord completion using Celery's event-based tracking.

        Returns:
            True: Chord completed with enough proxies
            False: Chord completed but not enough proxies
            None: Chord timed out or failed (triggers fallback)
        """
        from celery.result import AsyncResult
        from celery_app import celery_app

        print("[INFO] Blocking on chord completion...")
        chord_result = AsyncResult(chord_id, app=celery_app)

        stop_progress = threading.Event()
        progress_thread = self._start_progress_thread(
            stop_progress, job_id, start_time, check_interval
        )

        try:
            # Calculate dynamic timeout based on chunk count (per spec 105)
            # Formula: (chunks / workers) * time_per_chunk * buffer
            if timeout > 0:
                timeout_val = timeout
            elif total_chunks > 0:
                workers = 8  # Match Celery concurrency
                time_per_chunk = 900  # seconds (15min hard limit per chunk)
                buffer = 1.5  # 50% safety margin
                rounds = (total_chunks + workers - 1) // workers
                calculated = int(rounds * time_per_chunk * buffer)
                timeout_val = max(calculated, 600)  # At least 10 min
                print(f"[INFO] Dynamic timeout: {timeout_val}s ({total_chunks} chunks, {rounds} rounds)")
            else:
                timeout_val = 1800  # 30 min default
                print(f"[INFO] Using default timeout: {timeout_val}s")

            final_result = chord_result.get(timeout=timeout_val, propagate=False)
            self._stop_progress_thread(stop_progress, progress_thread)

            elapsed = int(time.time() - start_time)
            mins, secs = elapsed // 60, elapsed % 60

            if chord_result.failed():
                logger.error(f"Chord failed: {final_result}")
                print(f"[ERROR] Chord failed: {final_result}")
                return None  # Trigger fallback

            usable_count = self.get_usable_proxy_count()
            print(f"[SUCCESS] Chord complete! {usable_count} usable proxies after {mins}m {secs}s", flush=True)
            logger.info(f"Chord {chord_id} completed, {usable_count} usable proxies")
            # Return True/False based on proxy count - chord DID complete, no fallback needed
            return usable_count >= min_count

        except Exception as e:
            self._stop_progress_thread(stop_progress, progress_thread)
            return self._handle_chord_error(e, start_time, timeout)

    def _start_progress_thread(
        self, stop_event: threading.Event, job_id: Optional[str], start_time: float, interval: int
    ) -> threading.Thread:
        """Start background thread to show progress during chord wait."""

        def show_progress():
            while not stop_event.is_set():
                if not self.restart_celery_if_dead():
                    return
                elapsed = int(time.time() - start_time)
                mins, secs = elapsed // 60, elapsed % 60
                if job_id:
                    progress = self.get_refresh_progress(job_id)
                    print(f"[PROGRESS] {progress['completed_chunks']}/{progress['total_chunks']} "
                          f"chunks ({progress['progress_pct']:.0f}%) - {mins}m {secs}s")
                else:
                    print(f"[WAIT] Waiting for chord... ({mins}m {secs}s)")
                stop_event.wait(interval)

        thread = threading.Thread(target=show_progress, daemon=True)
        thread.start()
        return thread

    def _stop_progress_thread(self, stop_event: threading.Event, thread: threading.Thread) -> None:
        """Stop the progress display thread."""
        stop_event.set()
        thread.join(timeout=2)

    def _handle_chord_error(self, error: Exception, start_time: float, timeout: int) -> None:
        """Handle errors during chord wait. Returns None to trigger fallback."""
        elapsed = int(time.time() - start_time)
        mins, secs = elapsed // 60, elapsed % 60

        if "TimeoutError" in type(error).__name__ or "timeout" in str(error).lower():
            logger.warning(f"Chord wait timed out after {timeout}s, will try fallback")
            print(f"[WARNING] Chord timeout after {mins}m {secs}s (will try Redis fallback)")
        else:
            logger.error(f"Error waiting for chord: {error}")
            print(f"[ERROR] Chord wait failed: {error}")
        return None

    def _wait_via_redis_polling(
        self, job_id: str, start_time: float, timeout: int, min_count: int, check_interval: int
    ) -> bool:
        """Wait for job completion by polling Redis progress."""
        print("[INFO] Falling back to Redis progress tracking...")

        while True:
            if not self.restart_celery_if_dead():
                logger.error("Celery failed to restart")
                print("[ERROR] Celery worker cannot be restarted")
                return False

            elapsed = int(time.time() - start_time)
            mins, secs = elapsed // 60, elapsed % 60

            progress = self.get_refresh_progress(job_id)
            status = progress["status"]

            if status == "COMPLETE":
                usable_count = self.get_usable_proxy_count()
                print(f"[SUCCESS] Refresh complete! {usable_count} usable proxies after {mins}m {secs}s")
                logger.info(f"Job {job_id} completed, {usable_count} usable")
                return usable_count >= min_count

            if status == "FAILED":
                print(f"[ERROR] Refresh job {job_id} failed")
                return False

            if status in ("DISPATCHED", "PROCESSING"):
                celery_status = "alive" if self.is_celery_alive() else "DEAD"
                print(f"[PROGRESS] {progress['completed_chunks']}/{progress['total_chunks']} "
                      f"({progress['progress_pct']:.0f}%) - {mins}m {secs}s - celery: {celery_status}")
            else:
                print(f"[WAIT] Job status: {status} - {mins}m {secs}s")

            time.sleep(check_interval)

            if timeout > 0 and elapsed >= timeout:
                logger.error(f"Timeout waiting for proxy refresh after {timeout}s")
                print(f"[ERROR] Timeout after {mins}m {secs}s")
                return False

    def _wait_via_file_monitoring(
        self, mtime_before: float, start_time: float, timeout: int, min_count: int, check_interval: int
    ) -> bool:
        """Wait for proxy file to be updated (last resort fallback)."""
        print("[INFO] No job tracking available, using file-based fallback...")

        while True:
            if not self.restart_celery_if_dead():
                logger.error("Celery failed to restart")
                print("[ERROR] Celery worker cannot be restarted")
                return False

            elapsed = int(time.time() - start_time)
            mins, secs = elapsed // 60, elapsed % 60

            current_mtime = self.get_proxy_file_mtime()
            if current_mtime > mtime_before:
                usable_count = self.get_usable_proxy_count()
                if usable_count >= min_count:
                    print(f"[SUCCESS] Refresh complete! {usable_count} usable proxies after {mins}m {secs}s")
                    return True
                print(f"[INFO] File updated, {usable_count} usable proxies so far...")
                mtime_before = current_mtime
            else:
                celery_status = "alive" if self.is_celery_alive() else "DEAD"
                print(f"[WAIT] Waiting for results... ({mins}m {secs}s, celery: {celery_status})")

            time.sleep(check_interval)

            if timeout > 0 and elapsed >= timeout:
                logger.error(f"Timeout waiting for proxy refresh after {timeout}s")
                print(f"[ERROR] Timeout after {mins}m {secs}s")
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
