"""Unit tests for Redis-backed circuit breaker.

Tests state transitions, failure thresholds, timeout behavior, and fail-open safety.

Reference: Spec 115 Phase 4.3.1
"""


import time
from unittest.mock import MagicMock, patch

import pytest

# Import fakeredis for isolated testing
try:
    import fakeredis
    HAS_FAKEREDIS = True
except ImportError:
    HAS_FAKEREDIS = False
    pytest.skip("fakeredis not installed", allow_module_level=True)

from resilience.redis_circuit_breaker import RedisCircuitBreaker


@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def circuit_breaker(fake_redis):
    """Create circuit breaker with fake Redis backend."""
    cb = RedisCircuitBreaker(
        host="localhost",
        port=6379,
        db=0,
        failure_threshold=3,
        reset_timeout=60,
    )
    # Replace real Redis with fake Redis
    cb.redis = fake_redis
    return cb


class TestCircuitBreakerStateTransitions:
    """Test state transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""

    def test_initial_state_is_closed(self, circuit_breaker):
        """Circuit should start in CLOSED state."""
        state = circuit_breaker.get_state("example.com")
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0
        assert state["opened_at"] is None

    def test_closed_to_open_after_threshold_failures(self, circuit_breaker):
        """Circuit opens after reaching failure threshold."""
        domain = "example.com"

        # Record failures below threshold
        circuit_breaker.record_failure(domain, "cloudflare")
        circuit_breaker.record_failure(domain, "cloudflare")

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 2

        # Third failure should open circuit
        circuit_breaker.record_failure(domain, "cloudflare")

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["failures"] == 3
        assert state["last_block"] == "cloudflare"
        assert state["opened_at"] is not None

    def test_open_to_half_open_after_timeout(self, circuit_breaker):
        """Circuit transitions to HALF_OPEN after timeout expires."""
        domain = "example.com"

        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure(domain)

        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_OPEN

        # Fast-forward time past reset timeout
        with patch("time.time") as mock_time:
            # Set opened_at to 0, current time to 61 (past 60s timeout)
            mock_time.return_value = 61
            circuit_breaker.redis.set(circuit_breaker._key(domain, "opened_at"), "0")

            # can_request should transition to HALF_OPEN
            result = circuit_breaker.can_request(domain)

            assert result is True
            assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN

    def test_half_open_to_closed_on_success(self, circuit_breaker):
        """Circuit closes when request succeeds in HALF_OPEN state."""
        domain = "example.com"

        # Set circuit to HALF_OPEN manually
        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_HALF_OPEN)
        circuit_breaker.redis.set(circuit_breaker._key(domain, "failures"), "3")

        # Record success
        circuit_breaker.record_success(domain)

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0

    def test_half_open_to_open_on_failure(self, circuit_breaker):
        """Circuit re-opens when request fails in HALF_OPEN state."""
        domain = "example.com"

        # Set circuit to HALF_OPEN manually
        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_HALF_OPEN)

        # Record failure
        with patch("time.time", return_value=100):
            circuit_breaker.record_failure(domain, "captcha")

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["last_block"] == "captcha"
        assert state["opened_at"] == "100"


class TestCanRequest:
    """Test can_request() behavior across different states."""

    def test_can_request_returns_true_when_closed(self, circuit_breaker):
        """Requests allowed in CLOSED state."""
        assert circuit_breaker.can_request("example.com") is True

    def test_can_request_returns_false_when_open_before_timeout(self, circuit_breaker):
        """Requests blocked in OPEN state before timeout."""
        domain = "example.com"

        # Open the circuit
        for _ in range(3):
            circuit_breaker.record_failure(domain)

        # Set opened_at to current time
        with patch("time.time", return_value=100):
            circuit_breaker.redis.set(circuit_breaker._key(domain, "opened_at"), "100")

            # Check immediately - should be blocked
            result = circuit_breaker.can_request(domain)
            assert result is False

    def test_can_request_returns_true_when_open_after_timeout(self, circuit_breaker):
        """Requests allowed after timeout, transitioning to HALF_OPEN."""
        domain = "example.com"

        # Open the circuit at time 0
        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_OPEN)
        circuit_breaker.redis.set(circuit_breaker._key(domain, "opened_at"), "0")

        # Check at time 61 (past 60s timeout)
        with patch("time.time", return_value=61):
            result = circuit_breaker.can_request(domain)

            assert result is True
            assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN

    def test_can_request_returns_true_when_half_open(self, circuit_breaker):
        """Requests allowed in HALF_OPEN state for testing."""
        domain = "example.com"

        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_HALF_OPEN)

        assert circuit_breaker.can_request(domain) is True

    def test_can_request_handles_empty_domain(self, circuit_breaker):
        """Empty domain should return True."""
        assert circuit_breaker.can_request("") is True
        assert circuit_breaker.can_request(None) is True


class TestRecordFailure:
    """Test record_failure() behavior."""

    def test_record_failure_increments_counter_in_closed_state(self, circuit_breaker):
        """Failures increment counter in CLOSED state."""
        domain = "example.com"

        circuit_breaker.record_failure(domain)
        assert circuit_breaker.get_state(domain)["failures"] == 1

        circuit_breaker.record_failure(domain)
        assert circuit_breaker.get_state(domain)["failures"] == 2

    def test_record_failure_opens_circuit_at_threshold(self, circuit_breaker):
        """Circuit opens when failure threshold reached."""
        domain = "example.com"

        # Threshold is 3
        circuit_breaker.record_failure(domain, "rate_limit")
        circuit_breaker.record_failure(domain, "rate_limit")
        circuit_breaker.record_failure(domain, "rate_limit")

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["last_block"] == "rate_limit"

    def test_record_failure_reopens_from_half_open(self, circuit_breaker):
        """Failure in HALF_OPEN re-opens circuit."""
        domain = "example.com"

        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_HALF_OPEN)

        with patch("time.time", return_value=200):
            circuit_breaker.record_failure(domain, "cloudflare")

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["opened_at"] == "200"

    def test_record_failure_handles_empty_domain(self, circuit_breaker):
        """Empty domain should not raise error."""
        circuit_breaker.record_failure("")
        circuit_breaker.record_failure(None)
        # Should complete without error


class TestRecordSuccess:
    """Test record_success() behavior."""

    def test_record_success_resets_failures_in_closed_state(self, circuit_breaker):
        """Success resets failure counter in CLOSED state."""
        domain = "example.com"

        circuit_breaker.record_failure(domain)
        circuit_breaker.record_failure(domain)
        assert circuit_breaker.get_state(domain)["failures"] == 2

        circuit_breaker.record_success(domain)
        assert circuit_breaker.get_state(domain)["failures"] == 0

    def test_record_success_closes_circuit_from_half_open(self, circuit_breaker):
        """Success in HALF_OPEN closes circuit."""
        domain = "example.com"

        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_HALF_OPEN)
        circuit_breaker.redis.set(circuit_breaker._key(domain, "failures"), "5")

        circuit_breaker.record_success(domain)

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0

    def test_record_success_handles_empty_domain(self, circuit_breaker):
        """Empty domain should not raise error."""
        circuit_breaker.record_success("")
        circuit_breaker.record_success(None)
        # Should complete without error


class TestGetState:
    """Test get_state() monitoring functionality."""

    def test_get_state_returns_correct_state_dict(self, circuit_breaker):
        """get_state returns complete state information."""
        domain = "example.com"

        # Open circuit
        for _ in range(3):
            circuit_breaker.record_failure(domain, "cloudflare")

        state = circuit_breaker.get_state(domain)

        assert state["domain"] == domain
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["failures"] == 3
        assert state["last_block"] == "cloudflare"
        assert state["opened_at"] is not None

    def test_get_state_returns_default_for_new_domain(self, circuit_breaker):
        """get_state returns CLOSED for untracked domain."""
        state = circuit_breaker.get_state("new-domain.com")

        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0
        assert state["opened_at"] is None
        assert state["last_block"] is None


class TestGetAllStates:
    """Test get_all_states() for monitoring all domains."""

    def test_get_all_states_returns_all_tracked_domains(self, circuit_breaker):
        """get_all_states returns all domains with circuit state."""
        # Create states for multiple domains
        circuit_breaker.record_failure("domain1.com", "cloudflare")
        circuit_breaker.record_failure("domain2.com", "captcha")
        circuit_breaker.record_failure("domain2.com", "captcha")
        circuit_breaker.record_failure("domain2.com", "captcha")

        all_states = circuit_breaker.get_all_states()

        assert len(all_states) == 2
        assert "domain1.com" in all_states
        assert "domain2.com" in all_states

        assert all_states["domain1.com"]["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert all_states["domain1.com"]["failures"] == 1

        assert all_states["domain2.com"]["state"] == RedisCircuitBreaker.STATE_OPEN
        assert all_states["domain2.com"]["failures"] == 3

    def test_get_all_states_returns_empty_for_no_domains(self, circuit_breaker):
        """get_all_states returns empty dict when no domains tracked."""
        all_states = circuit_breaker.get_all_states()
        assert all_states == {}


class TestReset:
    """Test reset() functionality."""

    def test_reset_resets_circuit_to_closed(self, circuit_breaker):
        """reset() returns circuit to CLOSED state."""
        domain = "example.com"

        # Open circuit
        for _ in range(3):
            circuit_breaker.record_failure(domain, "cloudflare")

        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_OPEN

        # Reset
        circuit_breaker.reset(domain)

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0
        assert state["opened_at"] is None
        assert state["last_block"] is None

    def test_reset_clears_all_fields(self, circuit_breaker):
        """reset() removes all Redis keys for domain."""
        domain = "example.com"

        # Set all fields
        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_OPEN)
        circuit_breaker.redis.set(circuit_breaker._key(domain, "failures"), "5")
        circuit_breaker.redis.set(circuit_breaker._key(domain, "opened_at"), "123456")
        circuit_breaker.redis.set(circuit_breaker._key(domain, "last_block"), "cloudflare")

        # Reset
        circuit_breaker.reset(domain)

        # Check fields cleared
        assert circuit_breaker.redis.get(circuit_breaker._key(domain, "state")) == RedisCircuitBreaker.STATE_CLOSED
        assert circuit_breaker.redis.get(circuit_breaker._key(domain, "failures")) == "0"
        assert circuit_breaker.redis.get(circuit_breaker._key(domain, "opened_at")) is None
        assert circuit_breaker.redis.get(circuit_breaker._key(domain, "last_block")) is None


class TestFailOpenSafety:
    """Test fail-open behavior when Redis unavailable."""

    def test_can_request_returns_true_on_redis_error(self, circuit_breaker):
        """can_request returns True when Redis raises exception."""
        domain = "example.com"

        # Mock Redis to raise exception
        circuit_breaker.redis.get = MagicMock(side_effect=Exception("Redis connection failed"))

        # Should return True (fail-open)
        result = circuit_breaker.can_request(domain)
        assert result is True

    def test_record_failure_handles_redis_error_gracefully(self, circuit_breaker):
        """record_failure doesn't raise when Redis fails."""
        domain = "example.com"

        # Mock Redis to raise exception
        circuit_breaker.redis.get = MagicMock(side_effect=Exception("Redis connection failed"))

        # Should not raise
        circuit_breaker.record_failure(domain, "cloudflare")

    def test_record_success_handles_redis_error_gracefully(self, circuit_breaker):
        """record_success doesn't raise when Redis fails."""
        domain = "example.com"

        # Mock Redis to raise exception
        circuit_breaker.redis.get = MagicMock(side_effect=Exception("Redis connection failed"))

        # Should not raise
        circuit_breaker.record_success(domain)

    def test_get_state_returns_default_on_redis_error(self, circuit_breaker):
        """get_state returns default state with error field on Redis failure."""
        domain = "example.com"

        # Mock Redis to raise exception
        circuit_breaker.redis.get = MagicMock(side_effect=Exception("Redis connection failed"))

        state = circuit_breaker.get_state(domain)

        assert state["domain"] == domain
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0
        assert "error" in state

    def test_get_all_states_returns_empty_on_redis_error(self, circuit_breaker):
        """get_all_states returns empty dict on Redis failure."""
        # Mock Redis scan to raise exception
        circuit_breaker.redis.scan = MagicMock(side_effect=Exception("Redis connection failed"))

        states = circuit_breaker.get_all_states()
        assert states == {}

    def test_reset_handles_redis_error_gracefully(self, circuit_breaker):
        """reset doesn't raise when Redis fails."""
        domain = "example.com"

        # Mock Redis pipeline to raise exception
        circuit_breaker.redis.pipeline = MagicMock(side_effect=Exception("Redis connection failed"))

        # Should not raise
        circuit_breaker.reset(domain)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_exact_threshold_opens_circuit(self, circuit_breaker):
        """Circuit opens at exactly failure_threshold, not after."""
        domain = "example.com"

        # Threshold is 3
        circuit_breaker.record_failure(domain)
        circuit_breaker.record_failure(domain)

        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_CLOSED

        circuit_breaker.record_failure(domain)

        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_OPEN

    def test_timeout_boundary_condition(self, circuit_breaker):
        """Circuit opens at exactly reset_timeout, not before."""
        domain = "example.com"

        # Open circuit at time 0
        circuit_breaker.redis.set(circuit_breaker._key(domain, "state"), RedisCircuitBreaker.STATE_OPEN)
        circuit_breaker.redis.set(circuit_breaker._key(domain, "opened_at"), "0")

        # Check at time 59 (just before timeout)
        with patch("time.time", return_value=59):
            result = circuit_breaker.can_request(domain)
            assert result is False
            assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_OPEN

        # Check at time 60 (exactly at timeout)
        with patch("time.time", return_value=60):
            result = circuit_breaker.can_request(domain)
            assert result is True
            assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN

    def test_multiple_domains_independent(self, circuit_breaker):
        """Different domains maintain independent circuit states."""
        domain1 = "site1.com"
        domain2 = "site2.com"

        # Open circuit for domain1
        for _ in range(3):
            circuit_breaker.record_failure(domain1)

        # domain1 should be open, domain2 should be closed
        assert circuit_breaker.get_state(domain1)["state"] == RedisCircuitBreaker.STATE_OPEN
        assert circuit_breaker.get_state(domain2)["state"] == RedisCircuitBreaker.STATE_CLOSED

        # domain2 requests should still work
        assert circuit_breaker.can_request(domain2) is True
        assert circuit_breaker.can_request(domain1) is False

    def test_failure_after_open_does_not_increment_counter(self, circuit_breaker):
        """Failures in OPEN state don't increment counter."""
        domain = "example.com"

        # Open circuit
        for _ in range(3):
            circuit_breaker.record_failure(domain)

        assert circuit_breaker.get_state(domain)["failures"] == 3

        # Additional failures in OPEN state
        circuit_breaker.record_failure(domain)
        circuit_breaker.record_failure(domain)

        # Counter should not increase
        assert circuit_breaker.get_state(domain)["failures"] == 3


class TestFullCircuitLifecycle:
    """Integration tests for complete circuit lifecycle."""

    def test_complete_lifecycle_closed_to_open_to_half_open_to_closed(self, circuit_breaker):
        """Test complete circuit lifecycle with all state transitions."""
        domain = "example.com"

        # 1. Start in CLOSED state
        assert circuit_breaker.can_request(domain) is True
        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_CLOSED

        # 2. Record failures until circuit opens
        with patch("time.time", return_value=100):
            for _ in range(3):
                circuit_breaker.record_failure(domain, "cloudflare")

        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_OPEN

        # 3. Requests blocked while open
        with patch("time.time", return_value=120):
            assert circuit_breaker.can_request(domain) is False

        # 4. After timeout, transitions to HALF_OPEN
        with patch("time.time", return_value=161):
            assert circuit_breaker.can_request(domain) is True
            assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN

        # 5. Success in HALF_OPEN closes circuit
        circuit_breaker.record_success(domain)

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0

        # 6. Circuit fully functional again
        assert circuit_breaker.can_request(domain) is True

    def test_circuit_reopens_on_persistent_failure(self, circuit_breaker):
        """Circuit re-opens if failures persist after HALF_OPEN."""
        domain = "example.com"

        # Open circuit
        with patch("time.time", return_value=0):
            for _ in range(3):
                circuit_breaker.record_failure(domain)

        # Transition to HALF_OPEN after timeout
        with patch("time.time", return_value=61):
            circuit_breaker.can_request(domain)

        assert circuit_breaker.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN

        # Failure in HALF_OPEN re-opens circuit
        with patch("time.time", return_value=65):
            circuit_breaker.record_failure(domain, "still_blocked")

        state = circuit_breaker.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["opened_at"] == "65"
        assert state["last_block"] == "still_blocked"
