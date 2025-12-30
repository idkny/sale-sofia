"""
Runtime Proxy Scoring System based on the Competitor-Intel pattern.

This module provides weighted proxy selection with runtime scoring and auto-pruning.
Proxies are scored based on success/failure rates and response times, with automatic
removal of consistently failing proxies.

Usage:
    pool = ScoredProxyPool(PROXIES_DIR / "live_proxies.json")

    # Get a proxy (weighted random based on scores)
    proxy = pool.select_proxy()

    # Record result after using the proxy
    try:
        # ... use proxy ...
        pool.record_result(proxy["url"], success=True)
    except Exception:
        pool.record_result(proxy["url"], success=False)
"""

import fcntl
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
    Thread-safe proxy pool with runtime scoring and weighted selection.

    Proxies are selected using weighted random choice based on their scores.
    Scores are updated based on success/failure and persisted to disk.
    Proxies with excessive failures or very low scores are automatically removed.

    Attributes:
        proxies_file: Path to live_proxies.json
        scores_file: Path to proxy_scores.json (persisted scores)
        proxies: List of proxy dictionaries from live_proxies.json
        scores: Dict mapping proxy URLs to score metadata
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

        # Solution F: Proxy order tracking for X-Proxy-Offset header
        self._proxy_order: list[str] = []  # Ordered list of proxy keys matching mubeng file
        self._index_map: dict[str, int] = {}  # proxy_key -> index for O(1) lookup
        self._mubeng_proxy_file: Optional[Path] = None  # Path to mubeng's proxy file for --watch

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
        Remove a proxy from the pool and persist to mubeng's proxy file.

        Solution F: When a proxy is removed, we update the proxy file
        and mubeng's --watch flag triggers an automatic reload.

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

            # Solution F: Remove from proxy order and rebuild index map
            if proxy_key in self._proxy_order:
                self._proxy_order.remove(proxy_key)
                self._rebuild_index_map()
                logger.debug(f"Removed {proxy_key} from proxy order, new count: {len(self._proxy_order)}")

            if removed:
                logger.info(
                    f"Removed proxy {proxy_key} from pool "
                    f"({original_count} -> {len(self.proxies)})"
                )

                # Solution F: Persist to mubeng proxy file (triggers --watch reload)
                if self._mubeng_proxy_file:
                    self._save_proxy_file()
                    # Give mubeng time to detect file change and reload
                    time.sleep(0.2)

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
        Also updates _proxy_order for X-Proxy-Offset synchronization.
        """
        with self.lock:
            old_count = len(self.proxies)
            self._load_proxies()
            self._initialize_scores()
            new_count = len(self.proxies)

            # Rebuild proxy order for X-Proxy-Offset (Solution F hook)
            new_order = [f"{p['host']}:{p['port']}" for p in self.proxies]
            self._proxy_order = new_order
            self._index_map = {key: idx for idx, key in enumerate(new_order)}

            logger.info(f"Reloaded proxy pool: {old_count} -> {new_count} proxies, order updated")

    # =========================================================================
    # Solution F: Proxy Order Tracking for X-Proxy-Offset
    # =========================================================================

    def set_proxy_order(self, ordered_proxy_keys: list[str]) -> None:
        """
        Set the proxy order to match mubeng's loaded proxy file.

        This establishes the mapping between proxy keys and their index
        for use with the X-Proxy-Offset header in Solution F.

        Args:
            ordered_proxy_keys: List of proxy keys ("host:port") in file order
        """
        with self.lock:
            self._proxy_order = list(ordered_proxy_keys)  # Copy to avoid external mutation
            self._index_map = {key: idx for idx, key in enumerate(ordered_proxy_keys)}
            logger.info(f"Set proxy order: {len(self._proxy_order)} proxies mapped")

    def get_proxy_index(self, proxy_key: str) -> Optional[int]:
        """
        Get the index of a proxy for use with X-Proxy-Offset header.

        Args:
            proxy_key: Proxy key in format "host:port" or full URL

        Returns:
            Index (0-based) if found, None if proxy not in order map
        """
        # Handle both "host:port" and full URL formats
        if "://" in proxy_key:
            proxy_key = proxy_key.split("://")[1]

        with self.lock:
            return self._index_map.get(proxy_key)

    def _rebuild_index_map(self) -> None:
        """Rebuild the index map from current proxy order. Must hold lock."""
        self._index_map = {key: idx for idx, key in enumerate(self._proxy_order)}

    def set_mubeng_proxy_file(self, proxy_file: Path) -> None:
        """
        Set the path to mubeng's proxy file for live updates.

        When proxies are removed, we update this file and mubeng's --watch
        flag will detect the change and reload automatically.

        Args:
            proxy_file: Path to the temp proxy file used by mubeng
        """
        with self.lock:
            self._mubeng_proxy_file = Path(proxy_file)
            logger.info(f"Set mubeng proxy file: {self._mubeng_proxy_file}")

    def _save_proxy_file(self) -> bool:
        """
        Write current proxy order to mubeng's proxy file.

        This triggers mubeng's --watch reload. Must hold lock before calling.

        Returns:
            True if file was written successfully, False otherwise
        """
        if not self._mubeng_proxy_file:
            logger.warning("Cannot save proxy file: _mubeng_proxy_file not set")
            return False

        if not self._proxy_order:
            logger.warning("Cannot save proxy file: _proxy_order is empty")
            return False

        try:
            # Write proxy URLs to file with exclusive lock
            with open(self._mubeng_proxy_file, 'w') as f:
                fcntl.flock(f, fcntl.LOCK_EX)  # Exclusive lock
                try:
                    for proxy_key in self._proxy_order:
                        # Convert "host:port" to "http://host:port" for mubeng
                        f.write(f"http://{proxy_key}\n")
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)  # Release lock

            logger.info(
                f"Updated mubeng proxy file: {len(self._proxy_order)} proxies "
                f"written to {self._mubeng_proxy_file}"
            )
            return True

        except IOError as e:
            logger.error(f"Failed to save proxy file: {e}")
            return False
