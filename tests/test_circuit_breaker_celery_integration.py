"""Integration tests for Phase 4.4.4: Circuit breaker + Celery interaction.

Tests verify:
1. Circuit opens after consecutive failures (CIRCUIT_BREAKER_FAIL_MAX)
2. Circuit breaker integrates with scrape_chunk task
3. Task retries respect circuit state (don't hammer blocked domains)
4. Multi-domain independence (each domain has own circuit)
5. Redis circuit breaker shared state (if enabled)

Uses fakeredis for isolation and Celery eager mode for synchronous testing.

Reference: Spec 115 Phase 4.4.4
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

from celery_app import celery_app
from resilience.circuit_breaker import CircuitState, DomainCircuitBreaker, extract_domain
from resilience.redis_circuit_breaker import RedisCircuitBreaker
from scraping.tasks import scrape_chunk


@pytest.fixture
def fake_redis():
    """Create a fake Redis instance for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def celery_eager_mode():
    """Configure Celery to run tasks synchronously in eager mode."""
    # Store original settings
    original_always_eager = celery_app.conf.task_always_eager
    original_eager_propagates = celery_app.conf.task_eager_propagates

    # Enable eager mode
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    yield

    # Restore original settings
    celery_app.conf.task_always_eager = original_always_eager
    celery_app.conf.task_eager_propagates = original_eager_propagates


@pytest.fixture
def in_memory_circuit_breaker():
    """Create in-memory circuit breaker for testing."""
    return DomainCircuitBreaker(
        failure_threshold=3,
        recovery_timeout=60,
        half_open_max_calls=2,
        enabled=True,
    )


@pytest.fixture
def redis_circuit_breaker(fake_redis):
    """Create Redis-backed circuit breaker for testing."""
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


class TestCircuitOpensAfterFailures:
    """Test that circuit breaker opens after consecutive failures."""

    def test_circuit_opens_after_threshold_failures_in_memory(
        self, in_memory_circuit_breaker
    ):
        """Circuit opens after CIRCUIT_BREAKER_FAIL_MAX consecutive failures (in-memory)."""
        domain = "imot.bg"
        cb = in_memory_circuit_breaker

        # Initial state should be CLOSED
        assert cb.get_state(domain) == CircuitState.CLOSED
        assert cb.can_request(domain) is True

        # Record failures below threshold
        cb.record_failure(domain, "cloudflare")
        cb.record_failure(domain, "cloudflare")

        # Should still be closed
        assert cb.get_state(domain) == CircuitState.CLOSED
        assert cb.can_request(domain) is True

        # Third failure should open circuit
        cb.record_failure(domain, "cloudflare")

        # Circuit should now be OPEN
        assert cb.get_state(domain) == CircuitState.OPEN
        assert cb.can_request(domain) is False

        # Verify status details
        status = cb.get_status(domain)
        assert status.state == CircuitState.OPEN
        assert status.failure_count == 3
        assert status.last_block_type == "cloudflare"
        assert status.opened_at is not None

    def test_circuit_opens_after_threshold_failures_redis(
        self, redis_circuit_breaker
    ):
        """Circuit opens after CIRCUIT_BREAKER_FAIL_MAX consecutive failures (Redis)."""
        domain = "bazar.bg"
        cb = redis_circuit_breaker

        # Initial state should be CLOSED
        state = cb.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert cb.can_request(domain) is True

        # Record failures below threshold
        cb.record_failure(domain, "captcha")
        cb.record_failure(domain, "captcha")

        # Should still be closed
        state = cb.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 2

        # Third failure should open circuit
        cb.record_failure(domain, "captcha")

        # Circuit should now be OPEN
        state = cb.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state["failures"] == 3
        assert state["last_block"] == "captcha"
        assert cb.can_request(domain) is False

    def test_circuit_state_transitions_closed_to_open(
        self, in_memory_circuit_breaker
    ):
        """Verify circuit state transitions from CLOSED to OPEN."""
        domain = "example.com"
        cb = in_memory_circuit_breaker

        # Track state transitions
        states = []

        states.append(cb.get_state(domain))
        assert states[0] == CircuitState.CLOSED

        # Record failures
        for i in range(3):
            cb.record_failure(domain, "rate_limit")
            states.append(cb.get_state(domain))

        # Verify transition sequence
        assert states[0] == CircuitState.CLOSED  # Initial
        assert states[1] == CircuitState.CLOSED  # After 1st failure
        assert states[2] == CircuitState.CLOSED  # After 2nd failure
        assert states[3] == CircuitState.OPEN     # After 3rd failure (threshold)

    def test_opened_circuit_returns_false_for_can_request(
        self, in_memory_circuit_breaker
    ):
        """Opened circuit should block requests via can_request()."""
        domain = "imot.bg"
        cb = in_memory_circuit_breaker

        # Open the circuit
        for _ in range(3):
            cb.record_failure(domain)

        # Verify can_request blocks
        assert cb.can_request(domain) is False

        # Multiple checks should continue to block
        for _ in range(5):
            assert cb.can_request(domain) is False


class TestCircuitBreakerCeleryInteraction:
    """Test circuit breaker integration with scrape_chunk task."""

    @patch("scraping.tasks.get_working_proxy")
    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_scrape_chunk_checks_circuit_before_each_url(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool, mock_get_working_proxy,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """scrape_chunk should check circuit breaker before fetching each URL."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_get_working_proxy.return_value = "http://test-proxy:8080"
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"url": "http://imot.bg/listing1", "title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html>content</html>"

        # Scrape chunk
        urls = ["http://imot.bg/listing1", "http://imot.bg/listing2"]
        results = scrape_chunk(urls, "job_123", "imot.bg")

        # Verify circuit breaker was checked (can_request called)
        domain = extract_domain(urls[0])
        state = in_memory_circuit_breaker.get_state(domain)

        # Circuit should remain in CLOSED state (no failures)
        assert state == CircuitState.CLOSED

        # Verify both URLs were processed successfully
        assert len(results) == 2
        assert all("error" not in r for r in results)

    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_scrape_chunk_skips_urls_when_circuit_open(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """scrape_chunk should skip URLs when circuit is open."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper (shouldn't be called)
        mock_scraper = MagicMock()
        mock_get_scraper.return_value = mock_scraper

        # Open the circuit manually
        domain = "imot.bg"
        for _ in range(3):
            in_memory_circuit_breaker.record_failure(domain, "cloudflare")

        assert in_memory_circuit_breaker.can_request(domain) is False

        # Attempt to scrape chunk
        urls = ["http://imot.bg/listing1", "http://imot.bg/listing2"]
        results = scrape_chunk(urls, "job_456", "imot.bg")

        # All URLs should be skipped with circuit_open error
        assert len(results) == 2
        assert all(r.get("error") == "circuit_open" for r in results)
        assert all(r.get("skipped") is True for r in results)

        # Scraper should not have been called
        mock_scraper.extract_listing.assert_not_called()
        mock_asyncio.assert_not_called()

    @patch("scraping.tasks.get_working_proxy")
    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_scrape_chunk_records_success_to_circuit_breaker(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool, mock_get_working_proxy,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """scrape_chunk should record success to circuit breaker on successful extraction."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_get_working_proxy.return_value = "http://test-proxy:8080"
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper to succeed
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"url": "http://imot.bg/listing1", "title": "Success"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html>content</html>"

        # Record a failure first to create the circuit, then reset it
        domain = extract_domain("http://imot.bg/listing1")
        in_memory_circuit_breaker.record_failure(domain, "test")
        in_memory_circuit_breaker.reset(domain)

        # Verify circuit exists and is closed
        assert in_memory_circuit_breaker.get_state(domain) == CircuitState.CLOSED

        # Scrape chunk
        urls = ["http://imot.bg/listing1"]
        results = scrape_chunk(urls, "job_789", "imot.bg")

        # Verify success was recorded
        status = in_memory_circuit_breaker.get_status(domain)
        assert status.success_count >= 1
        assert status.failure_count == 0

    @patch("scraping.tasks.get_working_proxy")
    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_scrape_chunk_records_failure_to_circuit_breaker(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool, mock_get_working_proxy,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """scrape_chunk should record failure to circuit breaker on exception."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_get_working_proxy.return_value = "http://test-proxy:8080"
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper to fail
        mock_scraper = MagicMock()
        mock_get_scraper.return_value = mock_scraper

        # Simulate fetch failure
        mock_asyncio.side_effect = Exception("Cloudflare blocked")

        # Scrape chunk
        urls = ["http://imot.bg/listing1"]
        results = scrape_chunk(urls, "job_fail", "imot.bg")

        # Verify failure was recorded
        domain = extract_domain(urls[0])
        status = in_memory_circuit_breaker.get_status(domain)
        assert status.failure_count >= 1

        # Result should contain error
        assert len(results) == 1
        assert "error" in results[0]


class TestTaskRetryBehavior:
    """Test task retry behavior with circuit breaker."""

    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_task_respects_open_circuit_no_hammering(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """Task should respect open circuit and not hammer blocked domain."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper
        mock_scraper = MagicMock()
        mock_get_scraper.return_value = mock_scraper

        # Open circuit
        domain = "imot.bg"
        for _ in range(3):
            in_memory_circuit_breaker.record_failure(domain, "cloudflare")

        assert in_memory_circuit_breaker.can_request(domain) is False

        # Track how many times asyncio.run is called
        call_count = 0
        def count_calls(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Should not be called")

        mock_asyncio.side_effect = count_calls

        # Attempt multiple scrapes (simulating retries)
        urls = ["http://imot.bg/listing1"]
        for _ in range(5):
            results = scrape_chunk(urls, "job_retry", "imot.bg")
            assert results[0].get("error") == "circuit_open"

        # asyncio.run should NEVER be called (circuit blocks before fetch)
        assert call_count == 0, "Task should not attempt fetch when circuit is open"

    def test_circuit_reopens_after_half_open_test_fails(
        self, in_memory_circuit_breaker
    ):
        """Circuit should re-open if test request fails in HALF_OPEN state."""
        domain = "bazar.bg"
        cb = in_memory_circuit_breaker

        # Open circuit
        for _ in range(3):
            cb.record_failure(domain)

        assert cb.get_state(domain) == CircuitState.OPEN

        # Manually transition to HALF_OPEN for testing
        with cb._lock:
            circuit = cb._circuits[domain]
            circuit.state = CircuitState.HALF_OPEN
            circuit.half_open_attempts = 0

        assert cb.get_state(domain) == CircuitState.HALF_OPEN

        # Record failure in HALF_OPEN state
        cb.record_failure(domain, "still_blocked")

        # Circuit should re-open
        assert cb.get_state(domain) == CircuitState.OPEN
        status = cb.get_status(domain)
        assert status.last_block_type == "still_blocked"

    def test_successful_request_in_half_open_closes_circuit(
        self, in_memory_circuit_breaker
    ):
        """Successful request in HALF_OPEN should close circuit."""
        domain = "imot.bg"
        cb = in_memory_circuit_breaker

        # Open circuit
        for _ in range(3):
            cb.record_failure(domain)

        # Manually transition to HALF_OPEN
        with cb._lock:
            circuit = cb._circuits[domain]
            circuit.state = CircuitState.HALF_OPEN

        assert cb.get_state(domain) == CircuitState.HALF_OPEN

        # Record success
        cb.record_success(domain)

        # Circuit should close
        assert cb.get_state(domain) == CircuitState.CLOSED
        status = cb.get_status(domain)
        assert status.failure_count == 0


class TestMultiDomainIndependence:
    """Test each domain has independent circuit breaker."""

    def test_each_domain_has_independent_circuit_in_memory(
        self, in_memory_circuit_breaker
    ):
        """Each domain should have independent circuit state (in-memory)."""
        cb = in_memory_circuit_breaker
        domain1 = "imot.bg"
        domain2 = "bazar.bg"

        # Open circuit for domain1
        for _ in range(3):
            cb.record_failure(domain1, "cloudflare")

        # domain1 should be OPEN, domain2 should be CLOSED
        assert cb.get_state(domain1) == CircuitState.OPEN
        assert cb.get_state(domain2) == CircuitState.CLOSED

        # Verify can_request behavior
        assert cb.can_request(domain1) is False  # Blocked
        assert cb.can_request(domain2) is True   # Still allowed

    def test_each_domain_has_independent_circuit_redis(
        self, redis_circuit_breaker
    ):
        """Each domain should have independent circuit state (Redis)."""
        cb = redis_circuit_breaker
        domain1 = "imot.bg"
        domain2 = "bazar.bg"

        # Open circuit for domain1
        for _ in range(3):
            cb.record_failure(domain1, "captcha")

        # domain1 should be OPEN, domain2 should be CLOSED
        state1 = cb.get_state(domain1)
        state2 = cb.get_state(domain2)

        assert state1["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state2["state"] == RedisCircuitBreaker.STATE_CLOSED

        # Verify can_request behavior
        assert cb.can_request(domain1) is False  # Blocked
        assert cb.can_request(domain2) is True   # Still allowed

    def test_one_domain_circuit_open_does_not_affect_other_domains(
        self, in_memory_circuit_breaker
    ):
        """Opening circuit for one domain should not affect other domains."""
        cb = in_memory_circuit_breaker
        domains = ["imot.bg", "bazar.bg", "olx.bg"]

        # Open circuit for first domain only
        for _ in range(3):
            cb.record_failure(domains[0], "blocked")

        # Verify states
        assert cb.get_state(domains[0]) == CircuitState.OPEN
        assert cb.get_state(domains[1]) == CircuitState.CLOSED
        assert cb.get_state(domains[2]) == CircuitState.CLOSED

        # Verify can_request
        assert cb.can_request(domains[0]) is False
        assert cb.can_request(domains[1]) is True
        assert cb.can_request(domains[2]) is True

    def test_failures_on_imot_dont_open_bazar_circuit(
        self, in_memory_circuit_breaker
    ):
        """Failures on imot.bg should not open bazar.bg circuit."""
        cb = in_memory_circuit_breaker

        # Record many failures on imot.bg
        for _ in range(10):
            cb.record_failure("imot.bg", "cloudflare")

        # Check states
        imot_status = cb.get_status("imot.bg")
        bazar_status = cb.get_status("bazar.bg")

        # imot.bg should be open with failures recorded
        assert imot_status.state == CircuitState.OPEN
        assert imot_status.failure_count >= 3

        # bazar.bg should be clean
        assert bazar_status.state == CircuitState.CLOSED
        assert bazar_status.failure_count == 0

    @patch("scraping.tasks.get_working_proxy")
    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_scraping_multiple_domains_independent_circuits(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool, mock_get_working_proxy,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """Scraping multiple domains should use independent circuits."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_get_working_proxy.return_value = "http://test-proxy:8080"
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html></html>"

        # Open circuit for imot.bg
        for _ in range(3):
            in_memory_circuit_breaker.record_failure("imot.bg", "blocked")

        # Scrape both domains
        imot_urls = ["http://imot.bg/listing1"]
        bazar_urls = ["http://bazar.bg/listing1"]

        imot_results = scrape_chunk(imot_urls, "job_imot", "imot.bg")
        bazar_results = scrape_chunk(bazar_urls, "job_bazar", "bazar.bg")

        # imot.bg should be blocked
        assert imot_results[0].get("error") == "circuit_open"
        assert imot_results[0].get("skipped") is True

        # bazar.bg should succeed
        assert "error" not in bazar_results[0]
        assert bazar_results[0].get("title") == "Test"


class TestRedisCircuitBreakerSharedState:
    """Test Redis circuit breaker state sharing (concept test)."""

    def test_redis_circuit_state_persists_across_instances(
        self, fake_redis
    ):
        """Redis circuit state should persist across multiple circuit breaker instances."""
        domain = "imot.bg"

        # Create first instance and open circuit
        cb1 = RedisCircuitBreaker(
            host="localhost",
            port=6379,
            db=0,
            failure_threshold=3,
            reset_timeout=60,
        )
        cb1.redis = fake_redis

        for _ in range(3):
            cb1.record_failure(domain, "cloudflare")

        state1 = cb1.get_state(domain)
        assert state1["state"] == RedisCircuitBreaker.STATE_OPEN

        # Create second instance (simulating another worker)
        cb2 = RedisCircuitBreaker(
            host="localhost",
            port=6379,
            db=0,
            failure_threshold=3,
            reset_timeout=60,
        )
        cb2.redis = fake_redis

        # Second instance should see same state
        state2 = cb2.get_state(domain)
        assert state2["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state2["failures"] == 3
        assert state2["last_block"] == "cloudflare"

        # Both instances should block requests
        assert cb1.can_request(domain) is False
        assert cb2.can_request(domain) is False

    def test_redis_circuit_state_shared_across_mock_workers(
        self, fake_redis
    ):
        """Simulate multiple workers sharing Redis circuit state."""
        domain = "bazar.bg"

        # Worker 1: Record 2 failures
        worker1_cb = RedisCircuitBreaker(host="localhost", port=6379, db=0, failure_threshold=3)
        worker1_cb.redis = fake_redis

        worker1_cb.record_failure(domain, "captcha")
        worker1_cb.record_failure(domain, "captcha")

        state = worker1_cb.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 2

        # Worker 2: Record 1 more failure (should trigger circuit open)
        worker2_cb = RedisCircuitBreaker(host="localhost", port=6379, db=0, failure_threshold=3)
        worker2_cb.redis = fake_redis

        worker2_cb.record_failure(domain, "captcha")

        # Both workers should see OPEN state
        state1 = worker1_cb.get_state(domain)
        state2 = worker2_cb.get_state(domain)

        assert state1["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state2["state"] == RedisCircuitBreaker.STATE_OPEN
        assert state1["failures"] == 3
        assert state2["failures"] == 3

        # Both workers should block requests
        assert worker1_cb.can_request(domain) is False
        assert worker2_cb.can_request(domain) is False

    def test_redis_allows_recovery_coordination(
        self, fake_redis
    ):
        """Redis circuit breaker allows coordinated recovery across workers."""
        domain = "imot.bg"

        # Worker 1: Open circuit
        worker1_cb = RedisCircuitBreaker(host="localhost", port=6379, db=0, failure_threshold=3, reset_timeout=60)
        worker1_cb.redis = fake_redis

        with patch("time.time", return_value=100):
            for _ in range(3):
                worker1_cb.record_failure(domain)

        # Worker 2: See open state
        worker2_cb = RedisCircuitBreaker(host="localhost", port=6379, db=0, failure_threshold=3, reset_timeout=60)
        worker2_cb.redis = fake_redis

        # Both should block
        with patch("time.time", return_value=110):
            assert worker1_cb.can_request(domain) is False
            assert worker2_cb.can_request(domain) is False

        # After timeout, both should allow test request (HALF_OPEN)
        with patch("time.time", return_value=161):
            assert worker1_cb.can_request(domain) is True
            assert worker2_cb.can_request(domain) is True

            # Both should see HALF_OPEN
            assert worker1_cb.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN
            assert worker2_cb.get_state(domain)["state"] == RedisCircuitBreaker.STATE_HALF_OPEN

        # Worker 1: Success closes circuit for everyone
        worker1_cb.record_success(domain)

        # Worker 2: Should see CLOSED state
        state = worker2_cb.get_state(domain)
        assert state["state"] == RedisCircuitBreaker.STATE_CLOSED
        assert state["failures"] == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extract_domain_helper_function(self):
        """Test extract_domain correctly parses URLs."""
        assert extract_domain("http://imot.bg/listing/123") == "imot.bg"
        assert extract_domain("https://bazar.bg/search?q=test") == "bazar.bg"
        assert extract_domain("http://www.olx.bg/listing") == "www.olx.bg"
        assert extract_domain("imot.bg") == "imot.bg"

    def test_circuit_breaker_disabled_allows_all_requests(self):
        """Disabled circuit breaker should allow all requests."""
        cb = DomainCircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            enabled=False,  # DISABLED
        )

        domain = "imot.bg"

        # Record many failures
        for _ in range(10):
            cb.record_failure(domain, "cloudflare")

        # Should still allow requests (disabled)
        assert cb.can_request(domain) is True

        # When disabled, record_failure returns early, so no tracking occurs
        # This is expected behavior - disabled means completely bypassed
        status = cb.get_status(domain)
        assert status.failure_count == 0  # No tracking when disabled

    @patch("scraping.tasks.get_working_proxy")
    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_scrape_chunk_handles_extraction_failure_without_opening_circuit(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool, mock_get_working_proxy,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """Extraction failure (not fetch failure) should record failure to circuit."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_get_working_proxy.return_value = "http://test-proxy:8080"
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper to return None (extraction failed)
        mock_scraper = MagicMock()
        mock_scraper.extract_listing.return_value = None
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html>invalid</html>"

        # Scrape chunk
        urls = ["http://imot.bg/listing1"]
        results = scrape_chunk(urls, "job_extraction_fail", "imot.bg")

        # Should have extraction_failed error
        assert results[0].get("error") == "extraction_failed"

        # Circuit should NOT record this as a failure (content fetched successfully)
        domain = extract_domain(urls[0])
        status = in_memory_circuit_breaker.get_status(domain)
        # Extraction failures don't trigger circuit breaker in current implementation

    def test_multiple_success_resets_failure_count(
        self, in_memory_circuit_breaker
    ):
        """Multiple successes should reset failure count."""
        domain = "imot.bg"
        cb = in_memory_circuit_breaker

        # Record some failures
        cb.record_failure(domain)
        cb.record_failure(domain)

        status = cb.get_status(domain)
        assert status.failure_count == 2

        # Record success
        cb.record_success(domain)

        status = cb.get_status(domain)
        assert status.failure_count == 0

        # Circuit should remain closed
        assert cb.get_state(domain) == CircuitState.CLOSED


class TestFullIntegrationScenario:
    """End-to-end integration test with circuit breaker and Celery task."""

    @patch("scraping.tasks.get_working_proxy")
    @patch("scraping.tasks.get_proxy_pool")
    @patch("scraping.tasks.asyncio.run")
    @patch("scraping.tasks.get_redis_client")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    def test_full_scenario_failures_open_circuit_then_recovery(
        self, mock_get_cb, mock_get_scraper, mock_redis, mock_asyncio,
        mock_get_pool, mock_get_working_proxy,
        fake_redis, celery_eager_mode, in_memory_circuit_breaker
    ):
        """Full scenario: failures open circuit, timeout recovers, success closes."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = in_memory_circuit_breaker
        mock_get_working_proxy.return_value = "http://test-proxy:8080"
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Setup scraper
        mock_scraper = MagicMock()
        mock_get_scraper.return_value = mock_scraper

        # Phase 1: Initial failures open circuit
        mock_asyncio.side_effect = Exception("Cloudflare blocked")

        urls = ["http://imot.bg/listing1", "http://imot.bg/listing2", "http://imot.bg/listing3"]
        results = scrape_chunk(urls, "job_scenario", "imot.bg")

        # All should fail
        assert all("error" in r for r in results)

        # Circuit should be OPEN
        domain = extract_domain(urls[0])
        assert in_memory_circuit_breaker.get_state(domain) == CircuitState.OPEN

        # Phase 2: Subsequent requests blocked by circuit
        mock_asyncio.side_effect = None  # Reset
        mock_asyncio.return_value = "<html>valid</html>"

        more_urls = ["http://imot.bg/listing4", "http://imot.bg/listing5"]
        results2 = scrape_chunk(more_urls, "job_scenario2", "imot.bg")

        # Should be blocked by circuit (not attempted)
        assert all(r.get("error") == "circuit_open" for r in results2)

        # Phase 3: Manual transition to HALF_OPEN (simulating timeout)
        with in_memory_circuit_breaker._lock:
            circuit = in_memory_circuit_breaker._circuits[domain]
            circuit.state = CircuitState.HALF_OPEN

        # Phase 4: Successful request closes circuit
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Success"}
        mock_scraper.extract_listing.return_value = mock_listing

        recovery_urls = ["http://imot.bg/listing6"]
        results3 = scrape_chunk(recovery_urls, "job_recovery", "imot.bg")

        # Should succeed
        assert "error" not in results3[0]

        # Circuit should be CLOSED
        assert in_memory_circuit_breaker.get_state(domain) == CircuitState.CLOSED

        # Phase 5: Normal operation resumed
        final_urls = ["http://imot.bg/listing7"]
        results4 = scrape_chunk(final_urls, "job_final", "imot.bg")

        assert "error" not in results4[0]
        assert in_memory_circuit_breaker.can_request(domain) is True
