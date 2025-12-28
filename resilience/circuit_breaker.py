"""Domain-level circuit breaker for scraper fault tolerance.

Prevents cascade failures from blocked domains by tracking failure counts
and implementing automatic recovery with CLOSED -> OPEN -> HALF_OPEN states.

Reference: Spec 112 Section 2.1
"""

import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from loguru import logger


def extract_domain(url: str) -> str:
    """Extract domain from URL for rate limiting and circuit breaker tracking."""
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split("/")[0]

# Import settings with fallback defaults
try:
    from config.settings import (
        CIRCUIT_BREAKER_ENABLED,
        CIRCUIT_BREAKER_FAIL_MAX,
        CIRCUIT_BREAKER_HALF_OPEN_CALLS,
        CIRCUIT_BREAKER_RESET_TIMEOUT,
    )
except ImportError:
    CIRCUIT_BREAKER_FAIL_MAX = 5
    CIRCUIT_BREAKER_RESET_TIMEOUT = 60
    CIRCUIT_BREAKER_HALF_OPEN_CALLS = 2
    CIRCUIT_BREAKER_ENABLED = True


class CircuitState(Enum):
    """Circuit breaker state."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class DomainCircuitStatus:
    """Circuit status for a single domain."""

    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[datetime]
    opened_at: Optional[datetime]
    half_open_attempts: int
    last_block_type: Optional[str]  # cloudflare, captcha, rate_limit, etc.


class DomainCircuitBreaker:
    """
    Circuit breaker for domain-level fault tolerance.

    State transitions:
    - CLOSED (normal) -> failures >= threshold -> OPEN (blocked)
    - OPEN -> timeout expires -> HALF_OPEN (testing)
    - HALF_OPEN -> success -> CLOSED
    - HALF_OPEN -> failure -> OPEN

    Safety features:
    - Fail-open design: If circuit breaker has bugs, defaults to allowing requests
    - Configurable enable/disable flag
    - Thread-safe state mutations
    """

    def __init__(
        self,
        failure_threshold: int = CIRCUIT_BREAKER_FAIL_MAX,
        recovery_timeout: int = CIRCUIT_BREAKER_RESET_TIMEOUT,
        half_open_max_calls: int = CIRCUIT_BREAKER_HALF_OPEN_CALLS,
        enabled: bool = CIRCUIT_BREAKER_ENABLED,
    ):
        """
        Initialize domain circuit breaker.

        Args:
            failure_threshold: Consecutive failures before opening circuit
            recovery_timeout: Seconds before testing recovery
            half_open_max_calls: Test requests allowed in half-open state
            enabled: Master switch to enable/disable circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.enabled = enabled

        # Thread-safe state storage
        self._lock = threading.Lock()
        self._circuits: dict[str, DomainCircuitStatus] = {}

        # Metrics tracking
        self._total_blocked_requests = 0
        self._total_allowed_requests = 0

    def _create_default_status(self) -> DomainCircuitStatus:
        """Create a new circuit status in CLOSED state."""
        return DomainCircuitStatus(
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            opened_at=None,
            half_open_attempts=0,
            last_block_type=None,
        )

    def _reset_circuit(self, circuit: DomainCircuitStatus) -> None:
        """Reset a circuit to CLOSED state with cleared counters."""
        circuit.state = CircuitState.CLOSED
        circuit.failure_count = 0
        circuit.last_failure_time = None
        circuit.opened_at = None
        circuit.half_open_attempts = 0

    def _open_circuit(
        self, circuit: DomainCircuitStatus, block_type: Optional[str] = None
    ) -> None:
        """Transition a circuit to OPEN state."""
        circuit.state = CircuitState.OPEN
        circuit.opened_at = datetime.now()
        circuit.half_open_attempts = 0
        if block_type:
            circuit.last_block_type = block_type

    def can_request(self, domain: str) -> bool:
        """
        Check if request to domain is allowed based on circuit state.

        FAIL-OPEN DESIGN: If enabled=False or any error occurs, allows request.

        Args:
            domain: Domain to check (e.g., "imot.bg")

        Returns:
            True if request allowed, False if blocked
        """
        # SAFETY: Fail-open if disabled
        if not self.enabled:
            return True

        # SAFETY: Fail-open on empty domain
        if not domain:
            return True

        try:
            with self._lock:
                state = self._get_state_locked(domain)

                if state == CircuitState.CLOSED:
                    self._total_allowed_requests += 1
                    return True

                if state == CircuitState.OPEN:
                    self._total_blocked_requests += 1
                    logger.debug(f"[CIRCUIT] Domain {domain} blocked (circuit OPEN)")
                    return False

                if state == CircuitState.HALF_OPEN:
                    circuit = self._circuits[domain]
                    if circuit.half_open_attempts < self.half_open_max_calls:
                        circuit.half_open_attempts += 1
                        self._total_allowed_requests += 1
                        logger.debug(
                            f"[CIRCUIT] Domain {domain} test request "
                            f"{circuit.half_open_attempts}/{self.half_open_max_calls}"
                        )
                        return True
                    self._total_blocked_requests += 1
                    return False

                # Unknown state - fail open
                return True

        except Exception as e:
            # SAFETY: Fail-open on any error
            logger.warning(
                f"[CIRCUIT] Error checking domain {domain}, allowing request: {e}"
            )
            return True

    def record_success(self, domain: str) -> None:
        """
        Record successful request to domain.

        State transitions:
            - CLOSED: Increment success counter, reset failure counter
            - HALF_OPEN: Transition to CLOSED
            - OPEN: No effect

        Args:
            domain: Domain that succeeded
        """
        if not self.enabled or not domain:
            return

        try:
            with self._lock:
                if domain not in self._circuits:
                    return

                circuit = self._circuits[domain]

                if circuit.state == CircuitState.HALF_OPEN:
                    logger.info(f"[CIRCUIT] Domain {domain} recovered, closing circuit")
                    self._reset_circuit(circuit)
                elif circuit.state == CircuitState.CLOSED:
                    circuit.failure_count = 0
                    circuit.success_count += 1
                    circuit.last_failure_time = None

        except Exception as e:
            logger.warning(f"[CIRCUIT] Error recording success for {domain}: {e}")

    def record_failure(self, domain: str, block_type: Optional[str] = None) -> None:
        """
        Record failed request to domain.

        State transitions:
            - CLOSED: Increment failure count, open if threshold reached
            - HALF_OPEN: Transition back to OPEN
            - OPEN: No effect

        Args:
            domain: Domain that failed
            block_type: Type of block (cloudflare, captcha, rate_limit, etc.)
        """
        if not self.enabled or not domain:
            return

        try:
            with self._lock:
                if domain not in self._circuits:
                    self._circuits[domain] = self._create_default_status()

                circuit = self._circuits[domain]
                now = datetime.now()

                if circuit.state == CircuitState.CLOSED:
                    circuit.failure_count += 1
                    circuit.last_failure_time = now

                    if circuit.failure_count >= self.failure_threshold:
                        self._open_circuit(circuit, block_type)
                        logger.warning(
                            f"[CIRCUIT] Domain {domain} circuit OPENED "
                            f"(failures={circuit.failure_count}, "
                            f"block_type={block_type})"
                        )

                elif circuit.state == CircuitState.HALF_OPEN:
                    self._open_circuit(circuit, block_type)
                    logger.info(
                        f"[CIRCUIT] Domain {domain} still blocked, circuit re-opened"
                    )

        except Exception as e:
            logger.warning(f"[CIRCUIT] Error recording failure for {domain}: {e}")

    def get_state(self, domain: str) -> CircuitState:
        """
        Get current circuit state for domain.

        May transition OPEN -> HALF_OPEN if recovery timeout has elapsed.

        Args:
            domain: Domain to check

        Returns:
            Current circuit state
        """
        with self._lock:
            return self._get_state_locked(domain)

    def _get_state_locked(self, domain: str) -> CircuitState:
        """Get state with lock already held."""
        if domain not in self._circuits:
            return CircuitState.CLOSED

        circuit = self._circuits[domain]

        # Check for OPEN -> HALF_OPEN transition
        if circuit.state == CircuitState.OPEN and circuit.opened_at:
            elapsed = (datetime.now() - circuit.opened_at).total_seconds()
            if elapsed >= self.recovery_timeout:
                circuit.state = CircuitState.HALF_OPEN
                circuit.half_open_attempts = 0
                logger.info(
                    f"[CIRCUIT] Domain {domain} entering HALF_OPEN for testing"
                )

        return circuit.state

    def reset(self, domain: str) -> None:
        """
        Manually reset circuit to CLOSED state.

        Args:
            domain: Domain to reset
        """
        with self._lock:
            if domain in self._circuits:
                self._reset_circuit(self._circuits[domain])
                logger.info(f"[CIRCUIT] Domain {domain} manually reset to CLOSED")

    def get_status(self, domain: str) -> DomainCircuitStatus:
        """
        Get detailed circuit status for debugging/monitoring.

        Args:
            domain: Domain to inspect

        Returns:
            DomainCircuitStatus with state, counters, and timestamps
        """
        with self._lock:
            if domain not in self._circuits:
                return self._create_default_status()
            return self._circuits[domain]

    def get_open_circuits(self) -> list[str]:
        """
        Get list of domains with open circuits.

        Returns:
            List of domain names with OPEN circuits
        """
        with self._lock:
            return [
                domain
                for domain, circuit in self._circuits.items()
                if circuit.state == CircuitState.OPEN
            ]

    def get_metrics(self) -> dict:
        """
        Get circuit breaker metrics for monitoring.

        Returns:
            Dict with blocked/allowed counts and circuit states
        """
        with self._lock:
            open_count = sum(
                1 for c in self._circuits.values() if c.state == CircuitState.OPEN
            )
            half_open_count = sum(
                1 for c in self._circuits.values() if c.state == CircuitState.HALF_OPEN
            )

            return {
                "enabled": self.enabled,
                "total_domains_tracked": len(self._circuits),
                "open_circuits": open_count,
                "half_open_circuits": half_open_count,
                "total_blocked_requests": self._total_blocked_requests,
                "total_allowed_requests": self._total_allowed_requests,
            }


# Module-level singleton
_circuit_breaker: Optional[DomainCircuitBreaker] = None


def get_circuit_breaker() -> DomainCircuitBreaker:
    """Get the singleton circuit breaker instance."""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = DomainCircuitBreaker()
    return _circuit_breaker
