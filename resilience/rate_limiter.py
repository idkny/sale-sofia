"""Token bucket rate limiter per domain."""

import asyncio
import time
from threading import Lock

from loguru import logger

# Import settings with fallback defaults
try:
    from config.settings import DOMAIN_RATE_LIMITS
except ImportError:
    DOMAIN_RATE_LIMITS = {
        "imot.bg": 10,
        "bazar.bg": 10,
        "default": 10,
    }


class DomainRateLimiter:
    """
    Token bucket rate limiter per domain.

    Usage:
        limiter = DomainRateLimiter()
        limiter.acquire("imot.bg")  # Blocks if rate exceeded
        result = fetch_page(url)
    """

    def __init__(self, rate_limits: dict = None):
        """
        Initialize rate limiter.

        Args:
            rate_limits: Dict mapping domain to requests per minute.
                         Uses DOMAIN_RATE_LIMITS from settings if not provided.
        """
        self.rate_limits = rate_limits or DOMAIN_RATE_LIMITS
        self._tokens: dict[str, float] = {}
        self._last_refill: dict[str, float] = {}
        self._lock = Lock()

    def _get_rate(self, domain: str) -> int:
        """
        Get requests per minute for domain.

        Args:
            domain: Target domain

        Returns:
            Requests per minute allowed for this domain
        """
        return self.rate_limits.get(domain, self.rate_limits.get("default", 10))

    def _refill_tokens(self, domain: str, now: float) -> None:
        """
        Refill tokens based on time elapsed.

        Args:
            domain: Target domain
            now: Current timestamp
        """
        rate = self._get_rate(domain)

        # Initialize if first request for domain
        if domain not in self._tokens:
            self._tokens[domain] = float(rate)
            self._last_refill[domain] = now
            return

        # Calculate tokens to add based on elapsed time
        elapsed = now - self._last_refill[domain]
        refill = elapsed * (rate / 60.0)  # tokens per second = rate / 60
        self._tokens[domain] = min(float(rate), self._tokens[domain] + refill)
        self._last_refill[domain] = now

    def acquire(self, domain: str, blocking: bool = True) -> bool:
        """
        Acquire a token for the domain.

        Args:
            domain: Target domain
            blocking: If True, wait until token available.
                      If False, return False immediately if no token.

        Returns:
            True if token acquired, False if not (only when blocking=False)
        """
        with self._lock:
            now = time.time()
            self._refill_tokens(domain, now)

            # Check if token available
            if self._tokens[domain] >= 1.0:
                self._tokens[domain] -= 1.0
                return True

            if not blocking:
                return False

            # Calculate wait time for one token
            rate = self._get_rate(domain)
            wait_time = 60.0 / rate

        # Wait outside lock to allow other domains
        logger.debug(f"Rate limit for {domain}, waiting {wait_time:.2f}s")
        time.sleep(wait_time)

        # Retry acquisition after waiting
        return self.acquire(domain, blocking=True)

    async def acquire_async(self, domain: str, blocking: bool = True) -> bool:
        """
        Acquire a token for the domain (async version).

        Args:
            domain: Target domain
            blocking: If True, wait until token available.
                      If False, return False immediately if no token.

        Returns:
            True if token acquired, False if not (only when blocking=False)
        """
        with self._lock:
            now = time.time()
            self._refill_tokens(domain, now)

            # Check if token available
            if self._tokens[domain] >= 1.0:
                self._tokens[domain] -= 1.0
                return True

            if not blocking:
                return False

            # Calculate wait time for one token
            rate = self._get_rate(domain)
            wait_time = 60.0 / rate

        # Wait outside lock to allow other domains
        logger.debug(f"Rate limit for {domain}, waiting {wait_time:.2f}s")
        await asyncio.sleep(wait_time)

        # Retry acquisition after waiting
        return await self.acquire_async(domain, blocking=True)

    def reset(self) -> None:
        """Reset all state (for testing)."""
        with self._lock:
            self._tokens.clear()
            self._last_refill.clear()


# Singleton instance
_rate_limiter = None


def get_rate_limiter():
    """
    Get the singleton rate limiter instance.

    Returns Redis-backed or in-memory rate limiter based on config:
    - REDIS_RATE_LIMITER_ENABLED=True: Redis-backed (shared across workers)
    - REDIS_RATE_LIMITER_ENABLED=False: In-memory (single process only)

    Returns:
        DomainRateLimiter or RedisRateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        try:
            from config.settings import REDIS_RATE_LIMITER_ENABLED
        except ImportError:
            REDIS_RATE_LIMITER_ENABLED = False

        if REDIS_RATE_LIMITER_ENABLED:
            from resilience.redis_rate_limiter import RedisRateLimiter
            _rate_limiter = RedisRateLimiter()
            logger.info("[RATE_LIMITER] Using Redis-backed rate limiter")
        else:
            _rate_limiter = DomainRateLimiter()
            logger.debug("[RATE_LIMITER] Using in-memory rate limiter")

    return _rate_limiter
