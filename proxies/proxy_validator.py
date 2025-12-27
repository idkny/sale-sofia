"""
Proxy Validator - Pre-flight checking and scoring system for proxy quality.

Features:
1. Multiple test URLs (rotates to avoid rate limiting any single service)
2. Pre-flight check before browser use
3. Scoring system with auto-removal of consistently failing proxies

Test URLs are all designed for automated IP checking and won't ban you:
- httpbin.org - Kenneth Reitz's testing service
- icanhazip.com - Cloudflare-maintained
- checkip.amazonaws.com - AWS-maintained
- ifconfig.me - Simple IP checker
- ident.me - Lightweight IP service
- api.ipify.org - Popular IP API
"""

import json
import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

from paths import PROXIES_DIR
from config.settings import (
    SCORE_SUCCESS_MULTIPLIER,
    SCORE_FAILURE_MULTIPLIER,
    MAX_PROXY_FAILURES,
    MIN_PROXY_SCORE,
    PROXY_VALIDATION_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Test URLs designed for proxy checking (all return your IP)
# These services expect high-volume automated traffic
TEST_URLS = [
    ("https://httpbin.org/ip", "json"),  # Returns {"origin": "IP"}
    ("https://icanhazip.com", "text"),  # Cloudflare - plain text IP
    ("https://checkip.amazonaws.com", "text"),  # AWS - plain text IP
    ("https://ifconfig.me/ip", "text"),  # Plain text IP
    ("https://ident.me", "text"),  # Plain text IP
    ("https://api.ipify.org", "text"),  # Plain text IP
]

# Aliases for backward compatibility
MAX_FAILURES = MAX_PROXY_FAILURES
MIN_SCORE = MIN_PROXY_SCORE

# Quick validation timeout (shorter than scraping timeout for fast checks)
DEFAULT_TIMEOUT = PROXY_VALIDATION_TIMEOUT


@dataclass
class ProxyScore:
    """Tracks proxy performance metrics."""

    host: str
    port: int
    protocol: str = "http"
    score: float = 1.0
    failures: int = 0
    successes: int = 0
    last_check: float = 0.0
    last_response_time: float = 0.0

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "score": self.score,
            "failures": self.failures,
            "successes": self.successes,
            "last_check": self.last_check,
            "last_response_time": self.last_response_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyScore":
        return cls(
            host=data["host"],
            port=data["port"],
            protocol=data.get("protocol", "http"),
            score=data.get("score", 1.0),
            failures=data.get("failures", 0),
            successes=data.get("successes", 0),
            last_check=data.get("last_check", 0.0),
            last_response_time=data.get("last_response_time", 0.0),
        )


class ProxyValidator:
    """
    Validates proxies with multi-URL testing and scoring system.

    Usage:
        validator = ProxyValidator()

        # Pre-flight check before browser use
        if validator.check_proxy_liveness("http://localhost:8089"):
            # Proxy is working, proceed with browser
            ...

        # Or check a specific proxy from the pool
        proxy_url = validator.get_validated_proxy()
        if proxy_url:
            # Use this proxy
            ...
    """

    def __init__(self, scores_file: Optional[Path] = None):
        self.scores_file = scores_file or PROXIES_DIR / "proxy_scores.json"
        self.scores: dict[str, ProxyScore] = {}
        self._test_url_index = 0
        self._load_scores()

    def _load_scores(self) -> None:
        """Load proxy scores from file."""
        if self.scores_file.exists():
            try:
                with open(self.scores_file, "r") as f:
                    data = json.load(f)
                    self.scores = {
                        k: ProxyScore.from_dict(v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.scores)} proxy scores from {self.scores_file}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load proxy scores: {e}")
                self.scores = {}

    def _save_scores(self) -> None:
        """Save proxy scores to file."""
        try:
            with open(self.scores_file, "w") as f:
                json.dump(
                    {k: v.to_dict() for k, v in self.scores.items()},
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save proxy scores: {e}")

    def _get_next_test_url(self) -> tuple[str, str]:
        """Get next test URL in rotation (round-robin to avoid rate limits)."""
        url, response_type = TEST_URLS[self._test_url_index]
        self._test_url_index = (self._test_url_index + 1) % len(TEST_URLS)
        return url, response_type

    def _get_random_test_url(self) -> tuple[str, str]:
        """Get a random test URL."""
        return random.choice(TEST_URLS)

    def _validate_response(
        self, response: requests.Response, response_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate proxy response and extract IP.

        Args:
            response: The HTTP response object
            response_type: Expected type ("json" or "text")

        Returns:
            Tuple of (is_valid, extracted_ip)
        """
        if response.status_code != 200:
            return False, None

        if response_type == "json":
            try:
                data = response.json()
                ip = data.get("origin") or data.get("ip")
                if ip:
                    return True, ip
            except (ValueError, KeyError):
                pass
            return False, None

        # Text response - basic IP validation
        ip = response.text.strip()
        if "." in ip and len(ip) < 50:
            return True, ip
        return False, None

    def check_proxy_liveness(
        self,
        proxy_url: str,
        timeout: int = DEFAULT_TIMEOUT,
        update_score: bool = True,
    ) -> bool:
        """
        Perform a quick liveness check on a proxy URL.

        This is the PRE-FLIGHT CHECK - call this before passing proxy to browser.

        Args:
            proxy_url: Full proxy URL (e.g., "http://localhost:8089")
            timeout: Request timeout in seconds
            update_score: Whether to update the proxy's score

        Returns:
            True if proxy is working, False otherwise
        """
        test_url, response_type = self._get_next_test_url()

        try:
            start_time = time.time()
            response = requests.get(
                test_url,
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (proxy-check)"},
            )
            response_time = time.time() - start_time

            is_valid, ip = self._validate_response(response, response_type)
            if is_valid:
                logger.debug(
                    f"Proxy {proxy_url} passed liveness check "
                    f"via {test_url} ({response_time:.2f}s) - IP: {ip}"
                )
                if update_score:
                    self._record_success(proxy_url, response_time)
                return True

            logger.debug(f"Proxy {proxy_url} failed liveness check via {test_url}")
            if update_score:
                self._record_failure(proxy_url)
            return False

        except requests.exceptions.RequestException as e:
            logger.debug(f"Proxy {proxy_url} failed liveness check: {e}")
            if update_score:
                self._record_failure(proxy_url)
            return False

    def check_proxy_with_multiple_urls(
        self,
        proxy_url: str,
        num_tests: int = 3,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> tuple[bool, float]:
        """
        Check proxy against multiple test URLs for thorough validation.

        Args:
            proxy_url: Full proxy URL
            num_tests: Number of different URLs to test against
            timeout: Request timeout per test

        Returns:
            Tuple of (is_valid, success_rate)
        """
        successes = 0
        total_time = 0.0

        # Use different URLs for each test
        test_urls = random.sample(TEST_URLS, min(num_tests, len(TEST_URLS)))

        for test_url, response_type in test_urls:
            try:
                start_time = time.time()
                response = requests.get(
                    test_url,
                    proxies={"http": proxy_url, "https": proxy_url},
                    timeout=timeout,
                    headers={"User-Agent": "Mozilla/5.0 (proxy-check)"},
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    successes += 1
                    total_time += response_time

            except requests.exceptions.RequestException:
                pass

        success_rate = successes / num_tests
        avg_time = total_time / successes if successes > 0 else 0

        logger.info(
            f"Proxy {proxy_url} multi-check: {successes}/{num_tests} "
            f"({success_rate:.0%}), avg time: {avg_time:.2f}s"
        )

        return success_rate >= 0.5, success_rate

    def _record_success(self, proxy_url: str, response_time: float) -> None:
        """Record a successful proxy check."""
        key = proxy_url
        if key not in self.scores:
            self.scores[key] = ProxyScore(
                host=proxy_url,
                port=0,
                protocol="http",
            )

        score = self.scores[key]
        score.score = min(score.score * SCORE_SUCCESS_MULTIPLIER, 10.0)  # Cap at 10
        score.failures = 0  # Reset consecutive failures
        score.successes += 1
        score.last_check = time.time()
        score.last_response_time = response_time

        self._save_scores()

    def _record_failure(self, proxy_url: str) -> None:
        """Record a failed proxy check and potentially remove proxy."""
        key = proxy_url
        if key not in self.scores:
            self.scores[key] = ProxyScore(
                host=proxy_url,
                port=0,
                protocol="http",
            )

        score = self.scores[key]
        score.score *= SCORE_FAILURE_MULTIPLIER
        score.failures += 1
        score.last_check = time.time()

        # Check if proxy should be removed
        should_remove = score.failures >= MAX_FAILURES or score.score < MIN_SCORE

        if should_remove:
            logger.warning(
                f"Proxy {proxy_url} marked for removal: "
                f"failures={score.failures}, score={score.score:.4f}"
            )
            # Mark as dead but keep in scores for reference
            score.score = 0.0

        self._save_scores()

    def is_proxy_usable(self, proxy_url: str) -> bool:
        """Check if a proxy is still usable based on its score."""
        key = proxy_url
        if key not in self.scores:
            return True  # Unknown proxy, assume usable

        score = self.scores[key]
        return score.score >= MIN_SCORE and score.failures < MAX_FAILURES

    def get_proxy_stats(self, proxy_url: str) -> Optional[dict]:
        """Get statistics for a specific proxy."""
        key = proxy_url
        if key in self.scores:
            return self.scores[key].to_dict()
        return None

    def get_all_stats(self) -> dict:
        """Get statistics for all tracked proxies."""
        return {
            "total_tracked": len(self.scores),
            "usable": sum(1 for s in self.scores.values() if s.score >= MIN_SCORE),
            "dead": sum(1 for s in self.scores.values() if s.score < MIN_SCORE),
            "proxies": {k: v.to_dict() for k, v in self.scores.items()},
        }

    def cleanup_dead_proxies(self) -> int:
        """Remove dead proxies from the scores file. Returns count removed."""
        dead_keys = [k for k, v in self.scores.items() if v.score < MIN_SCORE]
        for key in dead_keys:
            del self.scores[key]
        self._save_scores()
        logger.info(f"Cleaned up {len(dead_keys)} dead proxies from scores")
        return len(dead_keys)


# Module-level validator instance for convenience
_validator: Optional[ProxyValidator] = None


def get_validator() -> ProxyValidator:
    """Get or create the global validator instance."""
    global _validator
    if _validator is None:
        _validator = ProxyValidator()
    return _validator


def preflight_check(proxy_url: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """
    Quick pre-flight liveness check for a proxy rotator endpoint.

    This is the main function to call before using a proxy with a browser.
    NOTE: This does NOT update scores because it checks the rotator endpoint
    (e.g., localhost:8089), not individual proxies. Individual proxy scoring
    happens during the mubeng --check phase in Celery tasks.

    Args:
        proxy_url: The proxy URL to check (e.g., "http://localhost:8089")
        timeout: Request timeout in seconds

    Returns:
        True if proxy is working, False otherwise

    Example:
        from proxies.proxy_validator import preflight_check

        if preflight_check("http://localhost:8089"):
            # Proxy is good, start browser
            browser = await create_instance(proxy=proxy_url)
        else:
            # Proxy failed, handle error
            print("Proxy not working!")
    """
    # update_score=False because we're checking the rotator endpoint, not an individual proxy
    return get_validator().check_proxy_liveness(proxy_url, timeout, update_score=False)


def is_proxy_usable(proxy_url: str) -> bool:
    """Check if a proxy is still usable based on historical performance."""
    return get_validator().is_proxy_usable(proxy_url)
