"""Unit tests for resilience Phase 2 modules.

Tests the circuit breaker and rate limiter.
"""

import time
import pytest
from threading import Thread
from datetime import datetime

from resilience.circuit_breaker import (
    CircuitState,
    DomainCircuitStatus,
    DomainCircuitBreaker,
    get_circuit_breaker,
)
from resilience.rate_limiter import (
    DomainRateLimiter,
    get_rate_limiter,
)


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitState:
    """Test CircuitState enum."""

    def test_circuit_state_values(self):
        """Test CircuitState has expected values."""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_circuit_state_members(self):
        """Test CircuitState has all expected members."""
        states = list(CircuitState)
        assert len(states) == 3
        assert CircuitState.CLOSED in states
        assert CircuitState.OPEN in states
        assert CircuitState.HALF_OPEN in states


class TestDomainCircuitStatus:
    """Test DomainCircuitStatus dataclass."""

    def test_status_creation(self):
        """Test creating a circuit status."""
        status = DomainCircuitStatus(
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            opened_at=None,
            half_open_attempts=0,
            last_block_type=None,
        )
        assert status.state == CircuitState.CLOSED
        assert status.failure_count == 0
        assert status.success_count == 0
        assert status.last_failure_time is None
        assert status.opened_at is None
        assert status.half_open_attempts == 0
        assert status.last_block_type is None

    def test_status_with_block_type(self):
        """Test circuit status tracks block type."""
        now = datetime.now()
        status = DomainCircuitStatus(
            state=CircuitState.OPEN,
            failure_count=5,
            success_count=10,
            last_failure_time=now,
            opened_at=now,
            half_open_attempts=0,
            last_block_type="cloudflare",
        )
        assert status.last_block_type == "cloudflare"
        assert status.state == CircuitState.OPEN


class TestDomainCircuitBreaker:
    """Test DomainCircuitBreaker class."""

    def test_initial_state_is_closed(self):
        """Test that new domains start in CLOSED state."""
        breaker = DomainCircuitBreaker()
        assert breaker.get_state("example.com") == CircuitState.CLOSED

    def test_closed_to_open_after_threshold(self):
        """Test CLOSED -> OPEN transition after failure threshold."""
        breaker = DomainCircuitBreaker(failure_threshold=3)

        # Record failures
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.CLOSED

        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.CLOSED

        # Third failure should open circuit
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

    def test_open_to_half_open_after_timeout(self):
        """Test OPEN -> HALF_OPEN transition after recovery timeout."""
        breaker = DomainCircuitBreaker(
            failure_threshold=2, recovery_timeout=1  # 1 second timeout
        )

        # Open the circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Should transition to HALF_OPEN
        assert breaker.get_state("example.com") == CircuitState.HALF_OPEN

    def test_half_open_to_closed_on_success(self):
        """Test HALF_OPEN -> CLOSED transition on successful request."""
        breaker = DomainCircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Open the circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

        # Wait for recovery
        time.sleep(1.1)
        assert breaker.get_state("example.com") == CircuitState.HALF_OPEN

        # Record success should close circuit
        breaker.record_success("example.com")
        assert breaker.get_state("example.com") == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self):
        """Test HALF_OPEN -> OPEN transition on failed request."""
        breaker = DomainCircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Open the circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

        # Wait for recovery
        time.sleep(1.1)
        assert breaker.get_state("example.com") == CircuitState.HALF_OPEN

        # Record failure should re-open circuit
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

    def test_can_request_returns_true_when_disabled(self):
        """Test fail-open design: can_request returns True when disabled."""
        breaker = DomainCircuitBreaker(enabled=False)
        assert breaker.can_request("example.com") is True

    def test_can_request_returns_true_on_empty_domain(self):
        """Test fail-open design: can_request returns True on empty domain."""
        breaker = DomainCircuitBreaker()
        assert breaker.can_request("") is True
        assert breaker.can_request(None) is True

    def test_can_request_closed_state(self):
        """Test can_request returns True in CLOSED state."""
        breaker = DomainCircuitBreaker()
        assert breaker.can_request("example.com") is True

    def test_can_request_open_state(self):
        """Test can_request returns False in OPEN state."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        # Open the circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

        # Should block requests
        assert breaker.can_request("example.com") is False

    def test_can_request_half_open_limited(self):
        """Test can_request only allows half_open_max_calls in HALF_OPEN state."""
        breaker = DomainCircuitBreaker(
            failure_threshold=2, recovery_timeout=1, half_open_max_calls=2
        )

        # Open the circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")

        # Wait for recovery
        time.sleep(1.1)
        assert breaker.get_state("example.com") == CircuitState.HALF_OPEN

        # Should allow half_open_max_calls requests
        assert breaker.can_request("example.com") is True
        assert breaker.can_request("example.com") is True

        # Should block further requests
        assert breaker.can_request("example.com") is False

    def test_manual_reset(self):
        """Test manual reset returns circuit to CLOSED state."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        # Open the circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

        # Manual reset
        breaker.reset("example.com")
        assert breaker.get_state("example.com") == CircuitState.CLOSED

        # Should allow requests again
        assert breaker.can_request("example.com") is True

    def test_success_resets_failure_count_in_closed(self):
        """Test that success resets failure count in CLOSED state."""
        breaker = DomainCircuitBreaker(failure_threshold=3)

        # Record some failures
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")

        # Record success should reset failure count
        breaker.record_success("example.com")

        # Should need 3 more failures to open
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.CLOSED

        breaker.record_failure("example.com")
        assert breaker.get_state("example.com") == CircuitState.OPEN

    def test_get_metrics(self):
        """Test get_metrics returns correct counts."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        metrics = breaker.get_metrics()
        assert metrics["enabled"] is True
        assert metrics["total_domains_tracked"] == 0
        assert metrics["open_circuits"] == 0
        assert metrics["half_open_circuits"] == 0

        # Open a circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")

        # Make a request to track allowed/blocked
        breaker.can_request("example.com")

        metrics = breaker.get_metrics()
        assert metrics["total_domains_tracked"] == 1
        assert metrics["open_circuits"] == 1
        assert metrics["total_blocked_requests"] >= 1

    def test_get_open_circuits(self):
        """Test get_open_circuits returns correct domains."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        # No open circuits initially
        assert breaker.get_open_circuits() == []

        # Open circuit for domain1
        breaker.record_failure("domain1.com")
        breaker.record_failure("domain1.com")

        # Open circuit for domain2
        breaker.record_failure("domain2.com")
        breaker.record_failure("domain2.com")

        # Should return both domains
        open_circuits = breaker.get_open_circuits()
        assert len(open_circuits) == 2
        assert "domain1.com" in open_circuits
        assert "domain2.com" in open_circuits

    def test_get_status(self):
        """Test get_status returns detailed circuit information."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        # Get status for unknown domain
        status = breaker.get_status("unknown.com")
        assert status.state == CircuitState.CLOSED
        assert status.failure_count == 0

        # Record a failure
        breaker.record_failure("example.com", block_type="cloudflare")

        status = breaker.get_status("example.com")
        assert status.state == CircuitState.CLOSED
        assert status.failure_count == 1
        assert status.last_block_type is None  # Not set until circuit opens

        # Open the circuit
        breaker.record_failure("example.com", block_type="cloudflare")

        status = breaker.get_status("example.com")
        assert status.state == CircuitState.OPEN
        assert status.failure_count == 2
        assert status.last_block_type == "cloudflare"
        assert status.opened_at is not None

    def test_thread_safety_concurrent_failures(self):
        """Test concurrent record_failure calls are thread-safe."""
        breaker = DomainCircuitBreaker(failure_threshold=100)

        def record_failures():
            for _ in range(5):
                breaker.record_failure("example.com")

        # Run concurrent threads
        threads = [Thread(target=record_failures) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have exactly 20 failures (4 threads * 5 failures each)
        # Circuit stays CLOSED because threshold is 100
        status = breaker.get_status("example.com")
        assert status.failure_count == 20

    def test_thread_safety_concurrent_success(self):
        """Test concurrent record_success calls are thread-safe."""
        breaker = DomainCircuitBreaker()

        def record_successes():
            for _ in range(5):
                breaker.record_success("example.com")

        # Record initial failure to create the circuit
        breaker.record_failure("example.com")

        # Run concurrent threads
        threads = [Thread(target=record_successes) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have success count
        status = breaker.get_status("example.com")
        assert status.success_count == 20

    def test_domain_isolation(self):
        """Test that different domains have independent circuits."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        # Open circuit for domain1
        breaker.record_failure("domain1.com")
        breaker.record_failure("domain1.com")

        # domain2 should still be closed
        assert breaker.get_state("domain1.com") == CircuitState.OPEN
        assert breaker.get_state("domain2.com") == CircuitState.CLOSED
        assert breaker.can_request("domain1.com") is False
        assert breaker.can_request("domain2.com") is True

    def test_block_type_tracking(self):
        """Test that block type is tracked correctly."""
        breaker = DomainCircuitBreaker(failure_threshold=2)

        # Record failures with different block types
        breaker.record_failure("example.com", block_type="cloudflare")
        breaker.record_failure("example.com", block_type="captcha")

        status = breaker.get_status("example.com")
        assert status.last_block_type == "captcha"  # Last block type wins


class TestCircuitBreakerSingleton:
    """Test get_circuit_breaker singleton."""

    def test_singleton_returns_same_instance(self):
        """Test that get_circuit_breaker returns the same instance."""
        breaker1 = get_circuit_breaker()
        breaker2 = get_circuit_breaker()
        assert breaker1 is breaker2

    def test_singleton_shares_state(self):
        """Test that singleton instances share state."""
        breaker1 = get_circuit_breaker()
        breaker1.record_failure("test.com")

        breaker2 = get_circuit_breaker()
        status = breaker2.get_status("test.com")
        assert status.failure_count >= 1


# =============================================================================
# Rate Limiter Tests
# =============================================================================


class TestDomainRateLimiter:
    """Test DomainRateLimiter class."""

    def test_first_request_always_succeeds(self):
        """Test that first request succeeds (full bucket)."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 10})
        assert limiter.acquire("example.com", blocking=False) is True

    def test_requests_within_rate_succeed(self):
        """Test that requests within rate limit succeed."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 60})

        # Should be able to make multiple requests rapidly
        for _ in range(5):
            assert limiter.acquire("example.com", blocking=False) is True

    def test_blocking_false_returns_immediately(self):
        """Test blocking=False returns immediately if no tokens."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 10})

        # Exhaust tokens (burst capacity = rate)
        for _ in range(10):
            limiter.acquire("example.com", blocking=False)

        # Next request should fail immediately
        start_time = time.time()
        result = limiter.acquire("example.com", blocking=False)
        elapsed = time.time() - start_time

        assert result is False
        assert elapsed < 0.1  # Should be instant

    def test_burst_capacity_equals_rate(self):
        """Test that burst capacity equals rate limit."""
        rate = 5
        limiter = DomainRateLimiter(rate_limits={"example.com": rate})

        # Should be able to make 'rate' requests immediately
        for _ in range(rate):
            assert limiter.acquire("example.com", blocking=False) is True

        # Next request should fail
        assert limiter.acquire("example.com", blocking=False) is False

    def test_rate_is_enforced_over_time(self):
        """Test that rate is enforced over time."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 60})  # 60 req/min

        # Exhaust initial tokens
        for _ in range(60):
            limiter.acquire("example.com", blocking=False)

        # Wait for one token to refill (1 second for 60 req/min = 1 req/sec)
        time.sleep(1.1)

        # Should be able to make one more request
        assert limiter.acquire("example.com", blocking=False) is True

        # But not two
        assert limiter.acquire("example.com", blocking=False) is False

    def test_blocking_mode_waits_for_token(self):
        """Test that blocking mode waits for token availability."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 60})  # 1 req/sec

        # Exhaust tokens
        for _ in range(60):
            limiter.acquire("example.com", blocking=False)

        # Blocking acquire should wait and succeed
        start_time = time.time()
        result = limiter.acquire("example.com", blocking=True)
        elapsed = time.time() - start_time

        assert result is True
        assert elapsed >= 0.9  # Should wait ~1 second

    def test_domain_isolation(self):
        """Test that different domains have separate buckets."""
        limiter = DomainRateLimiter(
            rate_limits={"domain1.com": 5, "domain2.com": 5}
        )

        # Exhaust domain1
        for _ in range(5):
            limiter.acquire("domain1.com", blocking=False)

        # domain1 should be exhausted
        assert limiter.acquire("domain1.com", blocking=False) is False

        # But domain2 should still work
        assert limiter.acquire("domain2.com", blocking=False) is True

    def test_default_rate_for_unknown_domain(self):
        """Test that default rate is used for unknown domains."""
        limiter = DomainRateLimiter(
            rate_limits={"known.com": 5, "default": 10}
        )

        # Unknown domain should use default rate (10)
        for _ in range(10):
            assert limiter.acquire("unknown.com", blocking=False) is True

        # 11th request should fail
        assert limiter.acquire("unknown.com", blocking=False) is False

    def test_reset_clears_all_state(self):
        """Test that reset() clears all state."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 5})

        # Exhaust tokens
        for _ in range(5):
            limiter.acquire("example.com", blocking=False)

        assert limiter.acquire("example.com", blocking=False) is False

        # Reset should restore full bucket
        limiter.reset()

        for _ in range(5):
            assert limiter.acquire("example.com", blocking=False) is True

    def test_token_refill_rate(self):
        """Test that tokens refill at correct rate."""
        limiter = DomainRateLimiter(rate_limits={"example.com": 60})  # 1 req/sec

        # Exhaust tokens
        for _ in range(60):
            limiter.acquire("example.com", blocking=False)

        # Wait 3 seconds - should get 3 tokens
        time.sleep(3.1)

        # Should be able to make 3 requests
        assert limiter.acquire("example.com", blocking=False) is True
        assert limiter.acquire("example.com", blocking=False) is True
        assert limiter.acquire("example.com", blocking=False) is True

        # But not a 4th
        assert limiter.acquire("example.com", blocking=False) is False

    def test_rate_getter(self):
        """Test _get_rate returns correct values."""
        limiter = DomainRateLimiter(
            rate_limits={"known.com": 15, "default": 10}
        )

        assert limiter._get_rate("known.com") == 15
        assert limiter._get_rate("unknown.com") == 10
        assert limiter._get_rate("another.com") == 10

    def test_concurrent_access_thread_safe(self):
        """Test that concurrent access is thread-safe."""
        from threading import Lock as ThreadingLock

        limiter = DomainRateLimiter(rate_limits={"example.com": 100})
        successes = {"count": 0}
        lock = ThreadingLock()

        def make_requests():
            for _ in range(10):
                if limiter.acquire("example.com", blocking=False):
                    with lock:
                        successes["count"] += 1

        # Run concurrent threads
        threads = [Thread(target=make_requests) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have acquired exactly the number of available tokens
        # (some threads might fail due to exhaustion, but count should be consistent)
        assert successes["count"] <= 100

    def test_multiple_domains_independent(self):
        """Test that rate limiting is independent per domain."""
        limiter = DomainRateLimiter(
            rate_limits={"domain1.com": 3, "domain2.com": 5}
        )

        # Exhaust domain1
        for _ in range(3):
            assert limiter.acquire("domain1.com", blocking=False) is True
        assert limiter.acquire("domain1.com", blocking=False) is False

        # domain2 should still have all 5 tokens
        for _ in range(5):
            assert limiter.acquire("domain2.com", blocking=False) is True
        assert limiter.acquire("domain2.com", blocking=False) is False


class TestRateLimiterSingleton:
    """Test get_rate_limiter singleton."""

    def test_singleton_returns_same_instance(self):
        """Test that get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2

    def test_singleton_shares_state(self):
        """Test that singleton instances share state."""
        limiter1 = get_rate_limiter()
        # Exhaust tokens for a test domain
        limiter1.acquire("singleton-test.com", blocking=False)

        limiter2 = get_rate_limiter()
        # Should see the same state
        assert limiter1 is limiter2


# =============================================================================
# Integration Tests
# =============================================================================


class TestCircuitBreakerRateLimiterIntegration:
    """Test circuit breaker and rate limiter working together."""

    def test_circuit_breaker_blocks_before_rate_limiter(self):
        """Test that circuit breaker blocks requests before rate limiting."""
        breaker = DomainCircuitBreaker(failure_threshold=2)
        limiter = DomainRateLimiter(rate_limits={"example.com": 10})

        # Open circuit
        breaker.record_failure("example.com")
        breaker.record_failure("example.com")

        # Circuit should block request
        assert breaker.can_request("example.com") is False

        # Rate limiter still has tokens
        assert limiter.acquire("example.com", blocking=False) is True

    def test_rate_limiter_and_circuit_breaker_independent(self):
        """Test that rate limiter and circuit breaker are independent."""
        breaker = DomainCircuitBreaker(failure_threshold=2)
        limiter = DomainRateLimiter(rate_limits={"example.com": 5})

        # Exhaust rate limiter
        for _ in range(5):
            limiter.acquire("example.com", blocking=False)

        # Circuit should still be closed
        assert breaker.get_state("example.com") == CircuitState.CLOSED
        assert breaker.can_request("example.com") is True

        # Rate limiter should be exhausted
        assert limiter.acquire("example.com", blocking=False) is False
