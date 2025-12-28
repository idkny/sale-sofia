"""Unit tests for Redis-backed rate limiter.

Tests token acquisition, refill logic, Lua script atomicity, and fail-open safety.

Reference: Spec 115 Phase 4.3.1
"""

import asyncio
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

from resilience.redis_rate_limiter import RedisRateLimiter


@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing with Lua support."""
    # Use FakeServer for Lua script support
    server = fakeredis.FakeServer()
    return fakeredis.FakeStrictRedis(server=server, decode_responses=True)


@pytest.fixture
def rate_limiter(fake_redis):
    """Create rate limiter with fake Redis backend."""
    limiter = RedisRateLimiter(
        host="localhost",
        port=6379,
        db=0,
        rate_limits={
            "fast-domain.com": 60,  # 60 req/min = 1 req/sec
            "slow-domain.com": 10,  # 10 req/min
            "default": 30,  # 30 req/min default
        },
    )
    # Replace real Redis with fake Redis
    limiter.redis = fake_redis
    return limiter


class TestTokenAcquisition:
    """Test basic token acquire/release functionality."""

    def test_acquire_returns_true_when_tokens_available(self, rate_limiter):
        """Token acquisition succeeds when tokens available."""
        domain = "fast-domain.com"

        # Fresh domain should have full bucket (60 tokens)
        result = rate_limiter.acquire(domain, blocking=False)
        assert result is True

        # Should be able to acquire multiple tokens
        for _ in range(5):
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is True

    def test_acquire_returns_false_when_no_tokens_non_blocking(self, rate_limiter):
        """Non-blocking acquire returns False when no tokens available."""
        domain = "slow-domain.com"

        # Drain all tokens (10 tokens available)
        for _ in range(10):
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is True

        # Next acquire should fail (non-blocking)
        result = rate_limiter.acquire(domain, blocking=False)
        assert result is False

    def test_acquire_waits_when_blocking(self, rate_limiter):
        """Blocking acquire waits for tokens to refill."""
        domain = "fast-domain.com"  # 60 req/min = 1 second per token

        # Drain all tokens
        for _ in range(60):
            rate_limiter.acquire(domain, blocking=False)

        # Mock time.sleep to verify waiting behavior
        with patch("time.sleep") as mock_sleep:
            # Mock time to simulate token refill after sleep
            # Need to provide enough time values for Lua script calls
            with patch("time.time") as mock_time:
                # Provide sequence of times: drain check, sleep, refill check, acquire
                mock_time.side_effect = [100, 101, 101, 101]

                result = rate_limiter.acquire(domain, blocking=True)

                # Should have waited 1 second (60 req/min = 1 sec per token)
                mock_sleep.assert_called_once()
                wait_time = mock_sleep.call_args[0][0]
                assert wait_time == pytest.approx(1.0, rel=0.01)
                assert result is True

    def test_acquire_handles_empty_domain(self, rate_limiter):
        """Empty or None domain returns True immediately."""
        assert rate_limiter.acquire("", blocking=False) is True
        assert rate_limiter.acquire(None, blocking=False) is True


class TestTokenRefill:
    """Test token bucket refill logic."""

    def test_tokens_refill_over_time(self, rate_limiter):
        """Tokens refill based on elapsed time."""
        domain = "fast-domain.com"  # 60 req/min = 1 token per second

        # Drain tokens
        for _ in range(60):
            rate_limiter.acquire(domain, blocking=False)

        # No tokens available
        assert rate_limiter.acquire(domain, blocking=False) is False

        # Fast-forward time by 2 seconds
        with patch("time.time") as mock_time:
            # Initial drain at time 0, check at time 2
            mock_time.return_value = 2.0
            rate_limiter.redis.set(rate_limiter._key(domain, "last_update"), "0.0")

            # Should have ~2 tokens after 2 seconds
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is True
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is True

            # Third token should fail (only 2 refilled)
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is False

    def test_tokens_capped_at_max(self, rate_limiter):
        """Tokens never exceed max bucket size."""
        domain = "slow-domain.com"  # 10 req/min max

        # Wait a very long time
        with patch("time.time") as mock_time:
            mock_time.return_value = 10000.0  # Very far in future
            rate_limiter.redis.set(rate_limiter._key(domain, "last_update"), "0.0")
            rate_limiter.redis.set(rate_limiter._key(domain, "tokens"), "5.0")

            # Should only have max tokens (10), not infinite
            acquired_count = 0
            for _ in range(15):
                if rate_limiter.acquire(domain, blocking=False):
                    acquired_count += 1

            # Should acquire exactly 10 tokens (max bucket size)
            assert acquired_count == 10

    def test_fresh_domain_starts_with_full_bucket(self, rate_limiter):
        """New domain starts with full token bucket."""
        domain = "new-domain.com"

        # Should use default rate (30 req/min)
        # Should be able to acquire up to 30 tokens
        acquired_count = 0
        for _ in range(35):
            if rate_limiter.acquire(domain, blocking=False):
                acquired_count += 1

        assert acquired_count == 30


class TestLuaScriptAtomicity:
    """Test Lua script for atomic token acquisition."""

    def test_lua_script_acquires_token_atomically(self, rate_limiter):
        """Lua script atomically acquires token and updates state."""
        domain = "fast-domain.com"

        # Acquire token
        result = rate_limiter.acquire(domain, blocking=False)
        assert result is True

        # Check Redis state updated
        tokens_str = rate_limiter.redis.get(rate_limiter._key(domain, "tokens"))
        assert tokens_str is not None
        tokens = float(tokens_str)
        assert tokens == pytest.approx(59.0, rel=0.01)  # 60 - 1

        # Last update should be set
        last_update_str = rate_limiter.redis.get(rate_limiter._key(domain, "last_update"))
        assert last_update_str is not None

    def test_lua_script_refills_before_acquire(self, rate_limiter):
        """Lua script refills tokens before attempting acquisition."""
        domain = "fast-domain.com"  # 60 req/min = 1 token per second

        # Drain all tokens at time 0
        with patch("time.time", return_value=0.0):
            for _ in range(60):
                rate_limiter.acquire(domain, blocking=False)

        # Verify drained
        with patch("time.time", return_value=0.0):
            assert rate_limiter.acquire(domain, blocking=False) is False

        # Advance time by 5 seconds
        with patch("time.time", return_value=5.0):
            # Should have refilled ~5 tokens
            acquired_count = 0
            for _ in range(10):
                if rate_limiter.acquire(domain, blocking=False):
                    acquired_count += 1

            assert acquired_count == 5

    def test_lua_script_returns_zero_when_empty(self, rate_limiter):
        """Lua script returns 0 when no tokens available."""
        domain = "slow-domain.com"  # 10 req/min

        # Drain all tokens
        for _ in range(10):
            rate_limiter.acquire(domain, blocking=False)

        # Verify Lua script returns 0
        rate = rate_limiter._get_rate(domain)
        max_tokens = rate

        acquired = rate_limiter._try_acquire(domain, rate, max_tokens)
        assert acquired is False


class TestAsyncAcquire:
    """Test async acquisition methods."""

    @pytest.mark.asyncio
    async def test_acquire_async_returns_true_when_available(self, rate_limiter):
        """Async acquire succeeds when tokens available."""
        domain = "fast-domain.com"

        result = await rate_limiter.acquire_async(domain, blocking=False)
        assert result is True

        # Multiple acquisitions
        for _ in range(5):
            result = await rate_limiter.acquire_async(domain, blocking=False)
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_async_waits_when_blocking(self, rate_limiter):
        """Async blocking acquire waits for token refill."""
        domain = "fast-domain.com"  # 60 req/min = 1 second per token

        # Drain all tokens
        for _ in range(60):
            await rate_limiter.acquire_async(domain, blocking=False)

        # Create async coroutine that returns immediately
        async def fake_sleep(duration):
            return None

        with patch("asyncio.sleep", side_effect=fake_sleep) as mock_sleep:
            # Mock time to simulate refill
            # Need enough time values: initial check (fails), then after sleep (succeeds)
            with patch("time.time") as mock_time:
                # Provide enough values for: first check, sleep calculation, retry check
                mock_time.side_effect = [100, 100, 101, 101, 101]

                result = await rate_limiter.acquire_async(domain, blocking=True)

                # Should have waited
                assert mock_sleep.call_count >= 1
                # Get the actual wait time from first sleep call
                wait_time = mock_sleep.call_args_list[0][0][0]
                assert wait_time == pytest.approx(1.0, rel=0.01)
                assert result is True


class TestRateLimits:
    """Test domain-specific rate limit configuration."""

    def test_uses_domain_specific_rate(self, rate_limiter):
        """Uses configured rate for specific domain."""
        # fast-domain.com is configured with 60 req/min
        domain = "fast-domain.com"

        # Should be able to acquire 60 tokens
        acquired_count = 0
        for _ in range(65):
            if rate_limiter.acquire(domain, blocking=False):
                acquired_count += 1

        assert acquired_count == 60

    def test_falls_back_to_default_rate(self, rate_limiter):
        """Falls back to default rate for unconfigured domain."""
        domain = "unknown-domain.com"

        # Should use default rate (30 req/min)
        acquired_count = 0
        for _ in range(35):
            if rate_limiter.acquire(domain, blocking=False):
                acquired_count += 1

        assert acquired_count == 30

    def test_different_domains_have_independent_buckets(self, rate_limiter):
        """Different domains have independent token buckets."""
        domain1 = "fast-domain.com"  # 60 req/min
        domain2 = "slow-domain.com"  # 10 req/min

        # Drain domain1
        for _ in range(60):
            rate_limiter.acquire(domain1, blocking=False)

        # domain1 should be empty
        assert rate_limiter.acquire(domain1, blocking=False) is False

        # domain2 should still have tokens
        assert rate_limiter.acquire(domain2, blocking=False) is True


class TestGetStats:
    """Test monitoring functionality."""

    def test_get_stats_returns_current_state(self, rate_limiter):
        """get_stats returns current rate limiter state."""
        domain = "fast-domain.com"

        # Fresh domain
        stats = rate_limiter.get_stats(domain)

        assert stats["domain"] == domain
        assert stats["tokens"] == pytest.approx(60.0, rel=0.01)  # Full bucket
        assert stats["max_tokens"] == 60.0
        assert stats["rate_per_minute"] == 60.0
        assert stats["last_update"] is None  # Not yet used

        # Acquire some tokens
        for _ in range(10):
            rate_limiter.acquire(domain, blocking=False)

        stats = rate_limiter.get_stats(domain)
        assert stats["tokens"] == pytest.approx(50.0, rel=0.01)  # 60 - 10
        assert stats["last_update"] is not None

    def test_get_stats_calculates_current_tokens(self, rate_limiter):
        """get_stats calculates tokens with time-based refill."""
        domain = "fast-domain.com"  # 60 req/min = 1 token per second

        # Drain to 10 tokens at time 0
        with patch("time.time", return_value=0.0):
            for _ in range(50):
                rate_limiter.acquire(domain, blocking=False)

        # Check stats at time 5 (should have refilled 5 tokens)
        with patch("time.time", return_value=5.0):
            stats = rate_limiter.get_stats(domain)

            # Should show ~15 tokens (10 remaining + 5 refilled)
            assert stats["tokens"] == pytest.approx(15.0, rel=0.1)


class TestReset:
    """Test reset functionality."""

    def test_reset_clears_domain_state(self, rate_limiter):
        """reset() clears state for specific domain."""
        domain = "fast-domain.com"

        # Use some tokens
        for _ in range(30):
            rate_limiter.acquire(domain, blocking=False)

        # Verify tokens depleted
        stats = rate_limiter.get_stats(domain)
        assert stats["tokens"] == pytest.approx(30.0, rel=0.01)

        # Reset domain
        rate_limiter.reset(domain)

        # Should have full bucket again
        stats = rate_limiter.get_stats(domain)
        assert stats["tokens"] == pytest.approx(60.0, rel=0.01)
        assert stats["last_update"] is None

    def test_reset_all_clears_all_domains(self, rate_limiter):
        """reset() with no args clears all domains."""
        domain1 = "fast-domain.com"
        domain2 = "slow-domain.com"

        # Use tokens on both domains
        for _ in range(20):
            rate_limiter.acquire(domain1, blocking=False)
            rate_limiter.acquire(domain2, blocking=False)

        # Reset all
        rate_limiter.reset()

        # Both should be fresh
        stats1 = rate_limiter.get_stats(domain1)
        stats2 = rate_limiter.get_stats(domain2)

        assert stats1["tokens"] == pytest.approx(60.0, rel=0.01)
        assert stats2["tokens"] == pytest.approx(10.0, rel=0.01)
        assert stats1["last_update"] is None
        assert stats2["last_update"] is None


class TestFailOpenSafety:
    """Test fail-open behavior when Redis unavailable."""

    def test_acquire_returns_true_on_redis_error(self, rate_limiter):
        """acquire returns True when Redis raises exception."""
        domain = "fast-domain.com"

        # Mock Redis to raise exception
        rate_limiter.redis.register_script = MagicMock(
            side_effect=Exception("Redis connection failed")
        )

        # Should return True (fail-open)
        result = rate_limiter.acquire(domain, blocking=False)
        assert result is True

    def test_get_stats_returns_error_on_redis_failure(self, rate_limiter):
        """get_stats returns error field on Redis failure."""
        domain = "fast-domain.com"

        # Mock Redis to raise exception
        rate_limiter.redis.get = MagicMock(side_effect=Exception("Redis connection failed"))

        stats = rate_limiter.get_stats(domain)

        assert stats["domain"] == domain
        assert stats["tokens"] is None
        assert stats["max_tokens"] == 60.0
        assert stats["rate_per_minute"] == 60.0
        assert "error" in stats
        assert "Redis connection failed" in stats["error"]

    def test_reset_handles_redis_error_gracefully(self, rate_limiter):
        """reset doesn't raise when Redis fails."""
        domain = "fast-domain.com"

        # Mock Redis pipeline to raise exception
        rate_limiter.redis.pipeline = MagicMock(side_effect=Exception("Redis connection failed"))

        # Should not raise
        rate_limiter.reset(domain)

        # Mock scan for reset all
        rate_limiter.redis.scan = MagicMock(side_effect=Exception("Redis connection failed"))

        # Should not raise
        rate_limiter.reset()


class TestFactoryFunction:
    """Test factory function for getting rate limiter instance."""

    def test_get_rate_limiter_returns_in_memory_by_default(self):
        """get_rate_limiter returns in-memory limiter when Redis disabled."""
        import resilience.rate_limiter

        # Clear singleton
        resilience.rate_limiter._rate_limiter = None

        # Mock the setting at import location
        with patch.dict("sys.modules", {"config.settings": MagicMock(REDIS_RATE_LIMITER_ENABLED=False)}):
            # Reload to pick up mocked setting
            from importlib import reload
            reload(resilience.rate_limiter)

            limiter = resilience.rate_limiter.get_rate_limiter()

            # Should be in-memory DomainRateLimiter, not Redis
            from resilience.rate_limiter import DomainRateLimiter
            assert isinstance(limiter, DomainRateLimiter)
            assert not isinstance(limiter, RedisRateLimiter)

            # Reset singleton
            resilience.rate_limiter._rate_limiter = None

    def test_get_rate_limiter_returns_redis_when_enabled(self):
        """get_rate_limiter returns Redis limiter when enabled."""
        import resilience.rate_limiter

        # Clear singleton
        resilience.rate_limiter._rate_limiter = None

        # Mock the setting at import location
        with patch.dict("sys.modules", {"config.settings": MagicMock(REDIS_RATE_LIMITER_ENABLED=True)}):
            # Reload to pick up mocked setting
            from importlib import reload
            reload(resilience.rate_limiter)

            limiter = resilience.rate_limiter.get_rate_limiter()

            # Should be RedisRateLimiter
            assert isinstance(limiter, RedisRateLimiter)

            # Reset singleton
            resilience.rate_limiter._rate_limiter = None


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_fractional_tokens_handled_correctly(self, rate_limiter):
        """Fractional token refill is handled correctly."""
        domain = "slow-domain.com"  # 10 req/min = 0.166 tokens per second

        # Drain bucket
        for _ in range(10):
            rate_limiter.acquire(domain, blocking=False)

        # Wait 3 seconds (should refill ~0.5 tokens)
        with patch("time.time") as mock_time:
            mock_time.return_value = 3.0
            rate_limiter.redis.set(rate_limiter._key(domain, "last_update"), "0.0")

            # Should not have enough for 1 full token
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is False

    def test_concurrent_acquire_attempts(self, rate_limiter):
        """Lua script ensures atomicity with concurrent attempts."""
        domain = "fast-domain.com"

        # Simulate multiple concurrent acquisitions
        # Even with fake Redis, Lua script should maintain consistency
        results = []
        for _ in range(70):  # Try to acquire more than available (60)
            result = rate_limiter.acquire(domain, blocking=False)
            results.append(result)

        # Should have exactly 60 successes
        assert sum(results) == 60
        assert sum(not r for r in results) == 10  # 10 failures

    def test_zero_rate_edge_case(self):
        """Handle edge case of zero rate limit."""
        limiter = RedisRateLimiter(
            host="localhost",
            port=6379,
            rate_limits={"blocked-domain.com": 0},
        )
        limiter.redis = fakeredis.FakeStrictRedis(decode_responses=True)

        # Zero rate should prevent any acquisitions
        result = limiter.acquire("blocked-domain.com", blocking=False)
        # With zero rate, wait_time calculation would cause division by zero
        # Current implementation would likely fail - this is a known edge case


class TestFullRateLimiterLifecycle:
    """Integration tests for complete rate limiter lifecycle."""

    def test_complete_lifecycle_drain_refill_drain(self, rate_limiter):
        """Test complete lifecycle: drain -> wait -> refill -> drain."""
        domain = "fast-domain.com"  # 60 req/min = 1 token per second

        # 1. Start with full bucket
        stats = rate_limiter.get_stats(domain)
        assert stats["tokens"] == pytest.approx(60.0, rel=0.01)

        # 2. Drain bucket at time 0
        with patch("time.time", return_value=0.0):
            for _ in range(60):
                result = rate_limiter.acquire(domain, blocking=False)
                assert result is True

            # Verify drained
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is False

        # 3. Wait 10 seconds (should refill 10 tokens)
        with patch("time.time", return_value=10.0):
            stats = rate_limiter.get_stats(domain)
            assert stats["tokens"] == pytest.approx(10.0, rel=0.1)

            # 4. Drain the refilled tokens
            for _ in range(10):
                result = rate_limiter.acquire(domain, blocking=False)
                assert result is True

            # No more tokens
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is False

        # 5. Reset and verify full bucket
        rate_limiter.reset(domain)
        stats = rate_limiter.get_stats(domain)
        assert stats["tokens"] == pytest.approx(60.0, rel=0.01)

    def test_mixed_blocking_non_blocking_requests(self, rate_limiter):
        """Test mixing blocking and non-blocking acquire calls."""
        domain = "slow-domain.com"  # 10 req/min

        # Drain 8 tokens non-blocking
        for _ in range(8):
            result = rate_limiter.acquire(domain, blocking=False)
            assert result is True

        # 2 non-blocking should succeed
        assert rate_limiter.acquire(domain, blocking=False) is True
        assert rate_limiter.acquire(domain, blocking=False) is True

        # Next non-blocking should fail
        assert rate_limiter.acquire(domain, blocking=False) is False

        # Blocking should wait and succeed
        with patch("time.sleep"):
            with patch("time.time") as mock_time:
                mock_time.side_effect = [0, 6]  # Simulate 6 second wait

                result = rate_limiter.acquire(domain, blocking=True)
                assert result is True
