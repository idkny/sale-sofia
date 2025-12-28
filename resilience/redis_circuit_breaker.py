"""Redis-backed circuit breaker for distributed workers.

Provides shared circuit breaker state across multiple Celery workers.
Each worker can see when other workers have tripped a circuit.

States: CLOSED (normal) -> OPEN (blocked) -> HALF_OPEN (testing)

Redis keys per domain:
    circuit:{domain}:state       - CLOSED|OPEN|HALF_OPEN
    circuit:{domain}:failures    - consecutive failure count
    circuit:{domain}:opened_at   - timestamp when opened
    circuit:{domain}:last_block  - block type (cloudflare, captcha, etc)

Reference: Spec 115 Phase 4.3.1
"""

import time
from typing import Optional

from loguru import logger

# Import settings with fallback defaults
try:
    from config.settings import (
        CIRCUIT_BREAKER_FAIL_MAX,
        CIRCUIT_BREAKER_RESET_TIMEOUT,
    )
except ImportError:
    CIRCUIT_BREAKER_FAIL_MAX = 5
    CIRCUIT_BREAKER_RESET_TIMEOUT = 60

# Import Redis settings from celery_app (consistent with existing usage)
try:
    from celery_app import REDIS_HOST, REDIS_PORT
    REDIS_DB = 0  # Use broker DB for resilience state
except ImportError:
    REDIS_HOST = "localhost"
    REDIS_PORT = "6379"
    REDIS_DB = 0


class RedisCircuitBreaker:
    """
    Circuit breaker with Redis-backed state for distributed workers.

    State transitions:
    - CLOSED (normal) -> failures >= threshold -> OPEN (blocked)
    - OPEN -> timeout expires -> HALF_OPEN (testing)
    - HALF_OPEN -> success -> CLOSED
    - HALF_OPEN -> failure -> OPEN

    Safety features:
    - Fail-open design: If Redis unavailable, allows requests
    - Uses pipeline for atomic multi-key operations
    - Logs warnings on Redis errors
    """

    # Circuit states
    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = int(REDIS_PORT),
        db: int = REDIS_DB,
        failure_threshold: int = CIRCUIT_BREAKER_FAIL_MAX,
        reset_timeout: int = CIRCUIT_BREAKER_RESET_TIMEOUT,
    ):
        """
        Initialize Redis-backed circuit breaker.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            failure_threshold: Consecutive failures before opening circuit
            reset_timeout: Seconds before testing recovery (OPEN -> HALF_OPEN)
        """
        import redis

        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )
        self.fail_max = failure_threshold
        self.reset_timeout = reset_timeout

    def _key(self, domain: str, field: str) -> str:
        """Build Redis key for domain field."""
        return f"circuit:{domain}:{field}"

    def can_request(self, domain: str) -> bool:
        """
        Check if requests to domain are allowed.

        FAIL-OPEN DESIGN: If Redis unavailable or any error, allows request.

        Args:
            domain: Domain to check (e.g., "imot.bg")

        Returns:
            True if request allowed, False if blocked
        """
        if not domain:
            return True

        try:
            state = self.redis.get(self._key(domain, "state")) or self.STATE_CLOSED

            if state == self.STATE_CLOSED:
                return True

            if state == self.STATE_OPEN:
                opened_at_str = self.redis.get(self._key(domain, "opened_at"))
                opened_at = float(opened_at_str) if opened_at_str else 0

                if time.time() - opened_at >= self.reset_timeout:
                    # Transition to HALF_OPEN
                    self.redis.set(self._key(domain, "state"), self.STATE_HALF_OPEN)
                    logger.info(
                        f"[REDIS_CIRCUIT] Domain {domain} entering HALF_OPEN for testing"
                    )
                    return True

                logger.debug(f"[REDIS_CIRCUIT] Domain {domain} blocked (circuit OPEN)")
                return False

            if state == self.STATE_HALF_OPEN:
                # Allow limited test requests in half-open state
                return True

            # Unknown state - fail open
            return True

        except Exception as e:
            # FAIL-OPEN: Redis error, allow request
            logger.warning(
                f"[REDIS_CIRCUIT] Redis error checking {domain}, allowing request: {e}"
            )
            return True

    def record_success(self, domain: str) -> None:
        """
        Record successful request to domain.

        State transitions:
            - CLOSED: Reset failure counter
            - HALF_OPEN: Transition to CLOSED
            - OPEN: No effect

        Args:
            domain: Domain that succeeded
        """
        if not domain:
            return

        try:
            state = self.redis.get(self._key(domain, "state")) or self.STATE_CLOSED

            if state == self.STATE_HALF_OPEN:
                # Close circuit on success during test
                pipe = self.redis.pipeline()
                pipe.set(self._key(domain, "state"), self.STATE_CLOSED)
                pipe.set(self._key(domain, "failures"), 0)
                pipe.execute()
                logger.info(f"[REDIS_CIRCUIT] Domain {domain} recovered, closing circuit")

            elif state == self.STATE_CLOSED:
                # Reset failure count
                self.redis.set(self._key(domain, "failures"), 0)

        except Exception as e:
            logger.warning(
                f"[REDIS_CIRCUIT] Redis error recording success for {domain}: {e}"
            )

    def record_failure(self, domain: str, block_type: str = "unknown") -> None:
        """
        Record failed request to domain, possibly opening circuit.

        State transitions:
            - CLOSED: Increment failure count, open if threshold reached
            - HALF_OPEN: Transition back to OPEN
            - OPEN: No effect

        Args:
            domain: Domain that failed
            block_type: Type of block (cloudflare, captcha, rate_limit, etc.)
        """
        if not domain:
            return

        try:
            state = self.redis.get(self._key(domain, "state")) or self.STATE_CLOSED

            if state == self.STATE_HALF_OPEN:
                # Re-open on failure during test
                pipe = self.redis.pipeline()
                pipe.set(self._key(domain, "state"), self.STATE_OPEN)
                pipe.set(self._key(domain, "opened_at"), time.time())
                pipe.set(self._key(domain, "last_block"), block_type)
                pipe.execute()
                logger.info(
                    f"[REDIS_CIRCUIT] Domain {domain} still blocked, circuit re-opened"
                )
                return

            if state == self.STATE_CLOSED:
                # Ensure state key exists for get_all_states() tracking
                self.redis.setnx(self._key(domain, "state"), self.STATE_CLOSED)

                # Increment failures atomically
                failures = self.redis.incr(self._key(domain, "failures"))

                if failures >= self.fail_max:
                    pipe = self.redis.pipeline()
                    pipe.set(self._key(domain, "state"), self.STATE_OPEN)
                    pipe.set(self._key(domain, "opened_at"), time.time())
                    pipe.set(self._key(domain, "last_block"), block_type)
                    pipe.execute()
                    logger.warning(
                        f"[REDIS_CIRCUIT] Domain {domain} circuit OPENED "
                        f"(failures={failures}, block_type={block_type})"
                    )

        except Exception as e:
            logger.warning(
                f"[REDIS_CIRCUIT] Redis error recording failure for {domain}: {e}"
            )

    def get_state(self, domain: str) -> dict:
        """
        Get current circuit state for monitoring.

        Args:
            domain: Domain to check

        Returns:
            Dict with domain, state, failures, opened_at, last_block
        """
        try:
            return {
                "domain": domain,
                "state": self.redis.get(self._key(domain, "state")) or self.STATE_CLOSED,
                "failures": int(self.redis.get(self._key(domain, "failures")) or 0),
                "opened_at": self.redis.get(self._key(domain, "opened_at")),
                "last_block": self.redis.get(self._key(domain, "last_block")),
            }
        except Exception as e:
            logger.warning(f"[REDIS_CIRCUIT] Redis error getting state for {domain}: {e}")
            return {
                "domain": domain,
                "state": self.STATE_CLOSED,
                "failures": 0,
                "opened_at": None,
                "last_block": None,
                "error": str(e),
            }

    def get_all_states(self) -> dict[str, dict]:
        """
        Get circuit states for all tracked domains.

        Scans Redis for all circuit:*:state keys and returns their states.

        Returns:
            Dict mapping domain names to their state dicts
        """
        try:
            states = {}
            # Scan for all circuit state keys
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(
                    cursor=cursor,
                    match="circuit:*:state",
                    count=100,
                )
                for key in keys:
                    # Extract domain from key pattern "circuit:{domain}:state"
                    parts = key.split(":")
                    if len(parts) >= 3:
                        domain = parts[1]
                        states[domain] = self.get_state(domain)

                if cursor == 0:
                    break

            return states

        except Exception as e:
            logger.warning(f"[REDIS_CIRCUIT] Redis error getting all states: {e}")
            return {}

    def reset(self, domain: str) -> None:
        """
        Manually reset circuit to CLOSED state.

        Args:
            domain: Domain to reset
        """
        try:
            pipe = self.redis.pipeline()
            pipe.set(self._key(domain, "state"), self.STATE_CLOSED)
            pipe.set(self._key(domain, "failures"), 0)
            pipe.delete(self._key(domain, "opened_at"))
            pipe.delete(self._key(domain, "last_block"))
            pipe.execute()
            logger.info(f"[REDIS_CIRCUIT] Domain {domain} manually reset to CLOSED")

        except Exception as e:
            logger.warning(f"[REDIS_CIRCUIT] Redis error resetting {domain}: {e}")


# Module-level singleton
_redis_circuit_breaker: Optional[RedisCircuitBreaker] = None


def get_redis_circuit_breaker() -> RedisCircuitBreaker:
    """Get the singleton Redis circuit breaker instance."""
    global _redis_circuit_breaker
    if _redis_circuit_breaker is None:
        _redis_circuit_breaker = RedisCircuitBreaker()
    return _redis_circuit_breaker
