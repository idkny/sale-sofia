"""
Runtime Proxy Pool with failure tracking and auto-pruning.

This module provides random proxy selection with consecutive failure tracking.
Proxies are automatically removed after MAX_CONSECUTIVE_PROXY_FAILURES failures.

Usage:
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

    # Get a random proxy
    proxy = pool.select_proxy()

    # Record result after using the proxy
    try:
        # ... use proxy ...
        pool.record_result(proxy["url"], success=True)
    except Exception:
        pool.record_result(proxy["url"], success=False)
"""

import json
import logging
import random
import threading
import time
from pathlib import Path
from typing import Optional

from proxies import proxy_to_url
from config.settings import MAX_CONSECUTIVE_PROXY_FAILURES

logger = logging.getLogger(__name__)


class ScoredProxyPool:
    """
    Thread-safe proxy pool with random selection and failure tracking.

    Proxies are selected using random choice. Consecutive failures are
    tracked and proxies are auto-removed after MAX_CONSECUTIVE_PROXY_FAILURES.

    Attributes:
        proxies_file: Path to live_proxies.json
        proxies: List of proxy dictionaries from live_proxies.json
        scores: Dict mapping proxy keys to failure tracking metadata
        lock: Thread lock for safe concurrent access
    """

    def __init__(self, proxies_file: Path):
        """
        Initialize the scored proxy pool.

        Args:
            proxies_file: Path to live_proxies.json file
        """
        self.proxies_file = Path(proxies_file)
        self.proxies: list[dict] = []
        self.scores: dict[str, dict] = {}
        self.lock = threading.RLock()  # Use RLock to allow reentrant locking (record_result -> remove_proxy)

        # Load proxies and initialize failure tracking
        self._load_proxies()
        self._initialize_scores()

    def _load_proxies(self) -> None:
        """Load proxies from live_proxies.json."""
        if not self.proxies_file.exists():
            logger.warning(f"Proxies file not found: {self.proxies_file}")
            self.proxies = []
            return

        try:
            with open(self.proxies_file, "r") as f:
                self.proxies = json.load(f)
            logger.info(f"Loaded {len(self.proxies)} proxies from {self.proxies_file}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load proxies: {e}")
            self.proxies = []

    def _initialize_scores(self) -> None:
        """Initialize failure tracking for all proxies."""
        with self.lock:
            for proxy in self.proxies:
                proxy_key = self._get_proxy_key(proxy)
                if proxy_key not in self.scores:
                    self.scores[proxy_key] = {
                        "failures": 0,
                        "last_used": None,
                    }

    def _get_proxy_key(self, proxy: dict) -> str:
        """
        Get unique key for a proxy.

        Args:
            proxy: Proxy dictionary with host/port

        Returns:
            String key in format "host:port"
        """
        return f"{proxy['host']}:{proxy['port']}"

    def _get_proxy_url(self, proxy: dict) -> str:
        """
        Get full proxy URL from proxy dict.

        Args:
            proxy: Proxy dictionary with protocol/host/port

        Returns:
            Full proxy URL like "http://host:port"
        """
        protocol = proxy.get("protocol", "http")
        host = proxy["host"]
        port = proxy["port"]
        return proxy_to_url(host, port, protocol)

    def select_proxy(self) -> Optional[dict]:
        """Select a random proxy from the pool."""
        with self.lock:
            if not self.proxies:
                logger.warning("No proxies available for selection")
                return None

            selected = random.choice(self.proxies)
            proxy_key = self._get_proxy_key(selected)
            if proxy_key in self.scores:
                self.scores[proxy_key]["last_used"] = time.time()
            logger.debug(f"Selected proxy {proxy_key}")
            return selected

    def record_result(self, proxy_key: str, success: bool) -> None:
        """Update proxy failure count based on success/failure."""
        if "://" in proxy_key:
            proxy_key = proxy_key.split("://")[1]

        with self.lock:
            if proxy_key not in self.scores:
                logger.warning(f"Proxy {proxy_key} not found in scores")
                return

            score_data = self.scores[proxy_key]

            if success:
                score_data["failures"] = 0
                logger.debug(f"Proxy {proxy_key} success - failures reset")
            else:
                score_data["failures"] += 1
                logger.debug(f"Proxy {proxy_key} failure - failures: {score_data['failures']}")

                if score_data["failures"] >= MAX_CONSECUTIVE_PROXY_FAILURES:
                    logger.warning(f"Auto-removing proxy {proxy_key}: failures={score_data['failures']}")
                    self.remove_proxy(proxy_key)

    def remove_proxy(self, proxy_key: str) -> bool:
        """
        Remove a proxy from the pool.

        Thread-safe: acquires lock during removal.

        Args:
            proxy_key: Proxy key in format "host:port"

        Returns:
            True if proxy was removed, False if not found
        """
        # Handle both "host:port" and full URL formats
        if "://" in proxy_key:
            proxy_key = proxy_key.split("://")[1]

        with self.lock:
            # Remove from scores
            if proxy_key in self.scores:
                del self.scores[proxy_key]

            # Remove from proxies list
            original_count = len(self.proxies)
            self.proxies = [
                p for p in self.proxies
                if self._get_proxy_key(p) != proxy_key
            ]
            removed = len(self.proxies) < original_count

            if removed:
                logger.info(
                    f"Removed proxy {proxy_key} from pool "
                    f"({original_count} -> {len(self.proxies)})"
                )

        return removed

    def get_proxy_url(self) -> Optional[str]:
        """
        Select a proxy and return its URL in format "protocol://host:port".

        Convenience method that combines select_proxy() and URL formatting.

        Returns:
            Proxy URL string, or None if no proxies available
        """
        proxy = self.select_proxy()
        if proxy:
            return self._get_proxy_url(proxy)
        return None

    def get_stats(self) -> dict:
        """Export proxy statistics for reporting."""
        with self.lock:
            total = len(self.proxies)
            with_failures = sum(1 for s in self.scores.values() if s.get("failures", 0) > 0)

            return {
                "total_proxies": total,
                "proxies_with_failures": with_failures,
            }

    def reload_proxies(self) -> None:
        """
        Reload proxies from live_proxies.json.

        Useful when the proxy pool has been refreshed by Celery tasks.
        Thread-safe: acquires lock during reload.
        """
        with self.lock:
            old_count = len(self.proxies)
            self._load_proxies()
            self._initialize_scores()
            new_count = len(self.proxies)
            logger.info(f"Reloaded proxy pool: {old_count} -> {new_count} proxies")
