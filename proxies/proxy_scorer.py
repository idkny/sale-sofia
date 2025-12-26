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

import json
import logging
import random
import threading
import time
from pathlib import Path
from typing import Optional

from proxies import proxy_to_url

logger = logging.getLogger(__name__)

# Scoring configuration
SCORE_SUCCESS_MULTIPLIER = 1.1  # +10% reward on success
SCORE_FAILURE_MULTIPLIER = 0.5  # -50% penalty on failure
MAX_FAILURES = 3  # Auto-remove after this many consecutive failures
MIN_SCORE = 0.01  # Auto-remove if score drops below this


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
        self.scores_file = self.proxies_file.parent / "proxy_scores.json"
        self.proxies: list[dict] = []
        self.scores: dict[str, dict] = {}
        self.lock = threading.RLock()  # Use RLock to allow reentrant locking (record_result -> remove_proxy)

        # Solution F: Proxy order tracking for X-Proxy-Offset header
        self._proxy_order: list[str] = []  # Ordered list of proxy keys matching mubeng file
        self._index_map: dict[str, int] = {}  # proxy_key -> index for O(1) lookup
        self._mubeng_proxy_file: Optional[Path] = None  # Path to mubeng's proxy file for --watch

        # Load proxies and scores
        self._load_proxies()
        self.load_scores()

        # Initialize scores for any new proxies
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

    def load_scores(self) -> None:
        """
        Load proxy scores from disk.

        Scores are stored in proxy_scores.json in the format:
        {
            "host:port": {
                "score": 1.0,
                "failures": 0,
                "last_used": timestamp
            }
        }
        """
        if not self.scores_file.exists():
            logger.info(f"No existing scores file at {self.scores_file}")
            self.scores = {}
            return

        try:
            with open(self.scores_file, "r") as f:
                self.scores = json.load(f)
            logger.info(f"Loaded scores for {len(self.scores)} proxies from {self.scores_file}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load scores: {e}")
            self.scores = {}

    def save_scores(self) -> None:
        """
        Persist proxy scores to disk.

        Thread-safe: acquires lock before saving.
        """
        with self.lock:
            try:
                with open(self.scores_file, "w") as f:
                    json.dump(self.scores, f, indent=2)
                logger.debug(f"Saved scores for {len(self.scores)} proxies to {self.scores_file}")
            except IOError as e:
                logger.error(f"Failed to save scores: {e}")

    def _initialize_scores(self) -> None:
        """
        Initialize scores for new proxies that don't have scores yet.

        Initial score is based on response time from validation:
        - score = 1.0 / response_time (faster proxies get higher initial scores)
        - If no timeout data, default to 1.0
        """
        with self.lock:
            for proxy in self.proxies:
                proxy_key = self._get_proxy_key(proxy)

                if proxy_key not in self.scores:
                    # Calculate initial score from response time
                    timeout = proxy.get("timeout")
                    if timeout and timeout > 0:
                        initial_score = 1.0 / timeout
                    else:
                        initial_score = 1.0

                    self.scores[proxy_key] = {
                        "score": initial_score,
                        "failures": 0,
                        "last_used": None,
                    }
                    logger.debug(f"Initialized score for {proxy_key}: {initial_score:.3f}")

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

    def _calculate_selection_weights(self) -> tuple[list[dict], list[float]]:
        """
        Calculate selection weights for all valid proxies.

        Returns:
            Tuple of (valid_proxies, weights) where weights are normalized probabilities.
            Returns empty lists if no valid proxies available.
        """
        scores = []
        valid_proxies = []

        for proxy in self.proxies:
            proxy_key = self._get_proxy_key(proxy)
            if proxy_key in self.scores:
                score = self.scores[proxy_key]["score"]
                if score > 0:
                    scores.append(score)
                    valid_proxies.append(proxy)

        if not valid_proxies:
            return [], []

        total_score = sum(scores)
        if total_score <= 0:
            # Uniform weights if all scores are 0
            weights = [1.0 / len(valid_proxies)] * len(valid_proxies)
        else:
            weights = [s / total_score for s in scores]

        return valid_proxies, weights

    def select_proxy(self) -> Optional[dict]:
        """
        Select a proxy using weighted random choice based on scores.

        Higher-scored proxies are more likely to be selected.
        Thread-safe: acquires lock during selection.

        Returns:
            Selected proxy dictionary, or None if no proxies available
        """
        with self.lock:
            if not self.proxies:
                logger.warning("No proxies available for selection")
                return None

            valid_proxies, weights = self._calculate_selection_weights()
            if not valid_proxies:
                logger.warning("No valid proxies with positive scores")
                return None

            selected = random.choices(valid_proxies, weights=weights, k=1)[0]

            # Update last_used timestamp
            proxy_key = self._get_proxy_key(selected)
            self.scores[proxy_key]["last_used"] = time.time()

            logger.debug(
                f"Selected proxy {proxy_key} with score "
                f"{self.scores[proxy_key]['score']:.3f}"
            )

            return selected

    def record_result(self, proxy_key: str, success: bool) -> None:
        """
        Update proxy score based on success/failure.

        Success: score *= 1.1, reset failures counter
        Failure: score *= 0.5, increment failures counter
        Auto-prune: Remove if failures >= 3 OR score < 0.01

        Thread-safe: acquires lock during update.

        Args:
            proxy_key: Proxy key in format "host:port" or full URL
            success: True if request succeeded, False otherwise
        """
        # Handle both "host:port" and full URL formats
        if "://" in proxy_key:
            # Extract host:port from URL like "http://1.2.3.4:8080"
            proxy_key = proxy_key.split("://")[1]

        with self.lock:
            if proxy_key not in self.scores:
                logger.warning(f"Proxy {proxy_key} not found in scores")
                return

            score_data = self.scores[proxy_key]

            if success:
                # Reward success: +10% score, reset failures
                score_data["score"] *= SCORE_SUCCESS_MULTIPLIER
                score_data["failures"] = 0
                logger.debug(
                    f"Proxy {proxy_key} success - new score: {score_data['score']:.3f}"
                )
            else:
                # Penalize failure: -50% score, increment failures
                score_data["score"] *= SCORE_FAILURE_MULTIPLIER
                score_data["failures"] += 1
                logger.debug(
                    f"Proxy {proxy_key} failure - new score: {score_data['score']:.3f}, "
                    f"failures: {score_data['failures']}"
                )

                # Check if proxy should be removed
                if (score_data["failures"] >= MAX_FAILURES or
                    score_data["score"] < MIN_SCORE):
                    logger.warning(
                        f"Auto-removing proxy {proxy_key}: "
                        f"failures={score_data['failures']}, "
                        f"score={score_data['score']:.4f}"
                    )
                    self.remove_proxy(proxy_key)
                    return

        # Save updated scores (outside lock to avoid holding during I/O)
        self.save_scores()

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

        # Save updated scores (outside lock to avoid holding during I/O)
        self.save_scores()

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
        """
        Get statistics about the proxy pool.

        Returns:
            Dictionary with pool statistics
        """
        with self.lock:
            total = len(self.proxies)
            scored = len(self.scores)

            if scored > 0:
                avg_score = sum(s["score"] for s in self.scores.values()) / scored
                failed = sum(1 for s in self.scores.values() if s["failures"] > 0)
            else:
                avg_score = 0.0
                failed = 0

            return {
                "total_proxies": total,
                "scored_proxies": scored,
                "average_score": avg_score,
                "proxies_with_failures": failed,
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
            # Write proxy URLs to file (one per line)
            with open(self._mubeng_proxy_file, 'w') as f:
                for proxy_key in self._proxy_order:
                    # Convert "host:port" to "http://host:port" for mubeng
                    f.write(f"http://{proxy_key}\n")

            logger.info(
                f"Updated mubeng proxy file: {len(self._proxy_order)} proxies "
                f"written to {self._mubeng_proxy_file}"
            )
            return True

        except IOError as e:
            logger.error(f"Failed to save proxy file: {e}")
            return False
