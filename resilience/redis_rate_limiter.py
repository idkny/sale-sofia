"""Redis-backed token bucket rate limiter for distributed workers.

Provides shared rate limiting state across multiple Celery workers.
Uses Lua scripting for atomic token acquisition to prevent race conditions.

Redis keys per domain:
    ratelimit:{domain}:tokens      - current token count (float)
    ratelimit:{domain}:last_update - last refill timestamp

Reference: Spec 115 Phase 4.3.1
"""

import asyncio
import time
from typing import Optional

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

# Import Redis settings from celery_app (consistent with existing usage)
try:
    from celery_app import REDIS_HOST, REDIS_PORT
    REDIS_DB = 0  # Use broker DB for resilience state
except ImportError:
    REDIS_HOST = "localhost"
    REDIS_PORT = "6379"
    REDIS_DB = 0


# Lua script for atomic token acquisition
# Returns 1 if token acquired, 0 if not enough tokens
LUA_ACQUIRE_TOKEN = """
local tokens_key = KEYS[1]
local last_update_key = KEYS[2]
local rate = tonumber(ARGV[1])
local max_tokens = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Get current state (default to full bucket)
local tokens = tonumber(redis.call('GET', tokens_key) or max_tokens)
local last_update = tonumber(redis.call('GET', last_update_key) or now)

-- Refill tokens based on elapsed time
local elapsed = now - last_update
local refill = elapsed * (rate / 60.0)
tokens = math.min(max_tokens, tokens + refill)

-- Try to consume one token
if tokens >= 1 then
    tokens = tokens - 1
    redis.call('SET', tokens_key, tokens)
    redis.call('SET', last_update_key, now)
    return 1
else
    -- Still update state for accurate tracking
    redis.call('SET', tokens_key, tokens)
    redis.call('SET', last_update_key, now)
    return 0
end
"""


class RedisRateLimiter:
    """
    Token bucket rate limiter with Redis-backed state for distributed workers.

    Usage:
        limiter = RedisRateLimiter()
        limiter.acquire("imot.bg")  # Blocks if rate exceeded
        result = fetch_page(url)

    Safety features:
    - Fail-open design: If Redis unavailable, allows requests
    - Uses Lua script for atomic token acquisition
    - Logs warnings on Redis errors
    """

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = int(REDIS_PORT),
        db: int = REDIS_DB,
        rate_limits: dict = None,
    ):
        """
        Initialize Redis-backed rate limiter.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            rate_limits: Dict mapping domain to requests per minute.
                         Uses DOMAIN_RATE_LIMITS from settings if not provided.
        """
        import redis

        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )
        self.rate_limits = rate_limits or DOMAIN_RATE_LIMITS
        self._lua_script = None

    def _key(self, domain: str, field: str) -> str:
        """Build Redis key for domain field."""
        return f"ratelimit:{domain}:{field}"

    def _get_rate(self, domain: str) -> float:
        """
        Get requests per minute for domain.

        Args:
            domain: Target domain

        Returns:
            Requests per minute allowed for this domain
        """
        return float(self.rate_limits.get(domain, self.rate_limits.get("default", 10)))

    def _try_acquire(self, domain: str, rate: float, max_tokens: float) -> bool:
        """
        Attempt atomic token acquisition using Lua script.

        Args:
            domain: Target domain
            rate: Requests per minute for this domain
            max_tokens: Maximum tokens (bucket size)

        Returns:
            True if token acquired, False otherwise
        """
        try:
            # Register script once for efficiency
            if self._lua_script is None:
                self._lua_script = self.redis.register_script(LUA_ACQUIRE_TOKEN)

            tokens_key = self._key(domain, "tokens")
            last_update_key = self._key(domain, "last_update")
            now = time.time()

            result = self._lua_script(
                keys=[tokens_key, last_update_key],
                args=[rate, max_tokens, now],
            )
            return result == 1

        except Exception as e:
            # FAIL-OPEN: Redis error, allow request
            logger.warning(
                f"[REDIS_RATELIMIT] Redis error acquiring token for {domain}, "
                f"allowing request: {e}"
            )
            return True

    def acquire(self, domain: str, blocking: bool = True) -> bool:
        """
        Acquire a token for the domain.

        FAIL-OPEN DESIGN: If Redis unavailable, allows request.

        Args:
            domain: Target domain
            blocking: If True, wait until token available.
                      If False, return False immediately if no token.

        Returns:
            True if token acquired, False if not (only when blocking=False)
        """
        if not domain:
            return True

        rate = self._get_rate(domain)
        max_tokens = rate  # Bucket size equals rate

        acquired = self._try_acquire(domain, rate, max_tokens)

        if acquired:
            return True

        if not blocking:
            return False

        # Calculate wait time for one token
        wait_time = 60.0 / rate
        logger.debug(f"[REDIS_RATELIMIT] Rate limit for {domain}, waiting {wait_time:.2f}s")
        time.sleep(wait_time)

        # Retry acquisition after waiting
        return self.acquire(domain, blocking=True)

    async def acquire_async(self, domain: str, blocking: bool = True) -> bool:
        """
        Acquire a token for the domain (async version).

        FAIL-OPEN DESIGN: If Redis unavailable, allows request.

        Args:
            domain: Target domain
            blocking: If True, wait until token available.
                      If False, return False immediately if no token.

        Returns:
            True if token acquired, False if not (only when blocking=False)
        """
        if not domain:
            return True

        rate = self._get_rate(domain)
        max_tokens = rate  # Bucket size equals rate

        acquired = self._try_acquire(domain, rate, max_tokens)

        if acquired:
            return True

        if not blocking:
            return False

        # Calculate wait time for one token
        wait_time = 60.0 / rate
        logger.debug(f"[REDIS_RATELIMIT] Rate limit for {domain}, waiting {wait_time:.2f}s")
        await asyncio.sleep(wait_time)

        # Retry acquisition after waiting
        return await self.acquire_async(domain, blocking=True)

    def reset(self, domain: str = None) -> None:
        """
        Reset rate limiter state.

        Args:
            domain: Specific domain to reset. If None, resets all domains.
        """
        try:
            if domain:
                # Reset specific domain
                pipe = self.redis.pipeline()
                pipe.delete(self._key(domain, "tokens"))
                pipe.delete(self._key(domain, "last_update"))
                pipe.execute()
                logger.info(f"[REDIS_RATELIMIT] Reset rate limiter for {domain}")
            else:
                # Reset all rate limiter keys
                cursor = 0
                keys_deleted = 0
                while True:
                    cursor, keys = self.redis.scan(
                        cursor=cursor,
                        match="ratelimit:*",
                        count=100,
                    )
                    if keys:
                        self.redis.delete(*keys)
                        keys_deleted += len(keys)

                    if cursor == 0:
                        break

                logger.info(
                    f"[REDIS_RATELIMIT] Reset all rate limiters ({keys_deleted} keys deleted)"
                )

        except Exception as e:
            logger.warning(f"[REDIS_RATELIMIT] Redis error resetting: {e}")

    def get_stats(self, domain: str) -> dict:
        """
        Get current rate limiter stats for monitoring.

        Args:
            domain: Domain to check

        Returns:
            Dict with domain, tokens, last_update, rate, max_tokens
        """
        try:
            tokens_str = self.redis.get(self._key(domain, "tokens"))
            last_update_str = self.redis.get(self._key(domain, "last_update"))

            rate = self._get_rate(domain)
            max_tokens = rate

            # Calculate current tokens with refill
            if tokens_str is not None and last_update_str is not None:
                tokens = float(tokens_str)
                last_update = float(last_update_str)
                now = time.time()
                elapsed = now - last_update
                refill = elapsed * (rate / 60.0)
                current_tokens = min(max_tokens, tokens + refill)
            else:
                current_tokens = max_tokens
                last_update = None

            return {
                "domain": domain,
                "tokens": round(current_tokens, 2),
                "max_tokens": max_tokens,
                "rate_per_minute": rate,
                "last_update": last_update,
            }

        except Exception as e:
            logger.warning(f"[REDIS_RATELIMIT] Redis error getting stats for {domain}: {e}")
            return {
                "domain": domain,
                "tokens": None,
                "max_tokens": self._get_rate(domain),
                "rate_per_minute": self._get_rate(domain),
                "last_update": None,
                "error": str(e),
            }


# Module-level singleton
_redis_rate_limiter: Optional[RedisRateLimiter] = None


def get_redis_rate_limiter() -> RedisRateLimiter:
    """Get the singleton Redis rate limiter instance."""
    global _redis_rate_limiter
    if _redis_rate_limiter is None:
        _redis_rate_limiter = RedisRateLimiter()
    return _redis_rate_limiter
