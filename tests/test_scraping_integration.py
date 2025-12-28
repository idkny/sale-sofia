"""Integration tests for Celery scraping system.

Tests the end-to-end workflow with real Celery chord patterns,
Redis progress tracking, circuit breaker sharing, and rate limiter sharing.

Uses fakeredis for isolation and Celery eager mode for synchronous testing.

Reference: Spec 115 Phase 4.3.2
"""

import os
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
from scraping.redis_keys import ScrapingKeys
from scraping.tasks import (
    PROGRESS_KEY_TTL,
    aggregate_results,
    dispatch_site_scraping,
    scrape_chunk,
)


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
def mock_scraper():
    """Create a mock scraper for testing."""
    scraper = MagicMock()

    # Mock extract_search_results to return listing URLs
    scraper.extract_search_results.return_value = [
        "http://example.com/listing1",
        "http://example.com/listing2",
        "http://example.com/listing3",
    ]

    # Mock extract_listing to return listing data
    mock_listing = MagicMock()
    mock_listing.to_dict.return_value = {
        "url": "http://example.com/listing1",
        "title": "Test Listing",
        "price": 1000,
    }
    scraper.extract_listing.return_value = mock_listing

    return scraper


class TestChordWorkflow:
    """Test chord (workers → callback) pattern execution."""

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    def test_dispatch_creates_chord_with_correct_structure(
        self, mock_redis, mock_config, mock_get_scraper, mock_asyncio, fake_redis, celery_eager_mode
    ):
        """Dispatch should create chord with worker group and aggregate callback."""
        mock_redis.return_value = fake_redis

        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = [
            "http://example.com/1",
            "http://example.com/2",
        ]
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        # Execute dispatch
        result = dispatch_site_scraping("imot.bg", ["http://search.url"])

        # Verify result structure
        assert "job_id" in result
        assert "chord_id" in result
        assert result["total_urls"] == 2
        assert result["total_chunks"] == 1

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    @patch("scraping.tasks.get_redis_client")
    def test_aggregate_results_receives_all_worker_results(
        self, mock_redis, mock_cb, mock_get_scraper, mock_asyncio, mock_save, fake_redis, celery_eager_mode
    ):
        """Aggregate callback should receive results from all workers."""
        mock_redis.return_value = fake_redis

        # Setup circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.can_request.return_value = True
        mock_cb.return_value = mock_circuit_breaker

        # Setup scraper
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test", "url": "http://test.com"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html></html>"

        # Simulate 3 worker chunks
        chunk1 = scrape_chunk(["http://example.com/1"], "job_123", "imot.bg")
        chunk2 = scrape_chunk(["http://example.com/2"], "job_123", "imot.bg")
        chunk3 = scrape_chunk(["http://example.com/3"], "job_123", "imot.bg")

        # Aggregate results
        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results([chunk1, chunk2, chunk3], "job_123", "imot.bg")

        # Verify all chunks processed
        assert result["saved"] == 3
        assert result["errors"] == 0
        assert mock_save.call_count == 3

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    def test_job_completion_status_set_correctly(
        self, mock_redis, mock_config, mock_get_scraper, mock_asyncio, fake_redis, celery_eager_mode
    ):
        """Job status should be set to COMPLETE after aggregation."""
        mock_redis.return_value = fake_redis

        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = ["http://example.com/1"]
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        # Mock save_listing
        with patch("data.data_store_main.save_listing"):
            with patch("websites.ListingData"):
                # Execute full workflow
                result = dispatch_site_scraping("imot.bg", ["http://search.url"])
                job_id = result["job_id"]

        # Verify final status is COMPLETE
        final_status = fake_redis.get(ScrapingKeys.status(job_id))
        assert final_status == "COMPLETE"


class TestProgressTracking:
    """Test Redis progress key updates throughout workflow."""

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    def test_status_transitions_through_all_states(
        self, mock_redis, mock_config, mock_get_scraper, mock_asyncio, fake_redis, celery_eager_mode
    ):
        """Status should transition: COLLECTING → DISPATCHED → PROCESSING → AGGREGATING → COMPLETE."""
        mock_redis.return_value = fake_redis

        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = ["http://example.com/1"]
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        # Track status transitions
        status_history = []

        original_setex = fake_redis.setex
        def track_status(key, ttl, value):
            if ":status" in key:
                status_history.append(value)
            return original_setex(key, ttl, value)

        fake_redis.setex = track_status

        # Execute workflow
        with patch("data.data_store_main.save_listing"):
            with patch("websites.ListingData"):
                with patch("resilience.get_circuit_breaker") as mock_cb:
                    mock_circuit_breaker = MagicMock()
                    mock_circuit_breaker.can_request.return_value = True
                    mock_cb.return_value = mock_circuit_breaker

                    dispatch_site_scraping("imot.bg", ["http://search.url"])

        # Verify status progression
        assert "COLLECTING" in status_history
        assert "DISPATCHED" in status_history
        assert "PROCESSING" in status_history
        assert "AGGREGATING" in status_history
        assert "COMPLETE" in status_history

        # Verify order (COLLECTING before DISPATCHED, etc.)
        collecting_idx = status_history.index("COLLECTING")
        dispatched_idx = status_history.index("DISPATCHED")
        processing_idx = status_history.index("PROCESSING")
        aggregating_idx = status_history.index("AGGREGATING")
        complete_idx = status_history.index("COMPLETE")

        assert collecting_idx < dispatched_idx < processing_idx < aggregating_idx < complete_idx

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    @patch("scraping.tasks.get_redis_client")
    def test_completed_chunks_increments_correctly(
        self, mock_redis, mock_cb, mock_get_scraper, mock_asyncio, fake_redis, celery_eager_mode
    ):
        """Completed chunks counter should increment after each worker completes."""
        mock_redis.return_value = fake_redis

        # Setup circuit breaker
        mock_circuit_breaker = MagicMock()
        mock_circuit_breaker.can_request.return_value = True
        mock_cb.return_value = mock_circuit_breaker

        # Setup scraper
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html></html>"

        # Initialize job
        job_id = "job_123"
        fake_redis.setex(ScrapingKeys.completed_chunks(job_id), PROGRESS_KEY_TTL, 0)

        # Process 3 chunks
        scrape_chunk(["http://example.com/1"], job_id, "imot.bg")
        assert int(fake_redis.get(ScrapingKeys.completed_chunks(job_id))) == 1

        scrape_chunk(["http://example.com/2"], job_id, "imot.bg")
        assert int(fake_redis.get(ScrapingKeys.completed_chunks(job_id))) == 2

        scrape_chunk(["http://example.com/3"], job_id, "imot.bg")
        assert int(fake_redis.get(ScrapingKeys.completed_chunks(job_id))) == 3

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_result_count_and_error_count_accurate(
        self, mock_redis, mock_save, fake_redis, celery_eager_mode
    ):
        """Result count and error count should reflect actual successes and failures."""
        mock_redis.return_value = fake_redis

        # Create mixed results (2 success, 1 error)
        chunk_results = [
            [{"title": "Success 1", "url": "http://example.com/1"}],
            [{"url": "http://example.com/2", "error": "failed"}],
            [{"title": "Success 2", "url": "http://example.com/3"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results(chunk_results, "job_456", "imot.bg")

        # Verify counts
        assert result["saved"] == 2
        assert result["errors"] == 1

        # Verify Redis keys
        assert int(fake_redis.get(ScrapingKeys.result_count("job_456"))) == 2
        assert int(fake_redis.get(ScrapingKeys.error_count("job_456"))) == 1


class TestCircuitBreakerSharing:
    """Test circuit breaker state sharing across simulated workers."""

    @pytest.fixture
    def redis_circuit_breaker(self, fake_redis):
        """Create Redis-backed circuit breaker with fake Redis."""
        from resilience.redis_circuit_breaker import RedisCircuitBreaker

        cb = RedisCircuitBreaker(
            host="localhost",
            port=6379,
            db=0,
            failure_threshold=3,
            reset_timeout=60,
        )
        cb.redis = fake_redis
        return cb

    @patch.dict(os.environ, {"REDIS_CIRCUIT_BREAKER_ENABLED": "true"})
    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    @patch("scraping.tasks.get_redis_client")
    def test_circuit_breaker_state_visible_across_workers(
        self, mock_redis, mock_get_cb, mock_get_scraper, mock_asyncio, fake_redis, redis_circuit_breaker, celery_eager_mode
    ):
        """Circuit breaker state should be shared via Redis across workers."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = redis_circuit_breaker

        # Setup scraper that fails
        mock_scraper = MagicMock()
        mock_scraper.extract_listing.side_effect = Exception("Site down")
        mock_get_scraper.return_value = mock_scraper

        mock_asyncio.return_value = "<html></html>"

        # Worker 1 records 3 failures (opens circuit)
        scrape_chunk(
            ["http://example.com/1", "http://example.com/2", "http://example.com/3"],
            "job_789",
            "imot.bg"
        )

        # Verify circuit is open
        assert redis_circuit_breaker.get_state("example.com")["state"] == "OPEN"

        # Worker 2 sees open circuit (state shared via Redis)
        results = scrape_chunk(["http://example.com/4"], "job_789", "imot.bg")

        # Worker 2 should skip due to open circuit
        assert results[0]["error"] == "circuit_open"
        assert results[0]["skipped"] is True

    @patch.dict(os.environ, {"REDIS_CIRCUIT_BREAKER_ENABLED": "true"})
    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("resilience.get_circuit_breaker")
    @patch("scraping.tasks.get_redis_client")
    def test_one_worker_opening_circuit_affects_another(
        self, mock_redis, mock_get_cb, mock_get_scraper, mock_asyncio, fake_redis, redis_circuit_breaker, celery_eager_mode
    ):
        """When one worker opens circuit, other workers should respect it."""
        mock_redis.return_value = fake_redis
        mock_get_cb.return_value = redis_circuit_breaker

        # Worker 1 scraper fails
        mock_scraper_fail = MagicMock()
        mock_scraper_fail.extract_listing.side_effect = Exception("Cloudflare block")

        # Worker 2 scraper works (but won't be called due to open circuit)
        mock_scraper_ok = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Success"}
        mock_scraper_ok.extract_listing.return_value = mock_listing

        mock_asyncio.return_value = "<html></html>"

        # Worker 1: Open circuit with 3 failures
        mock_get_scraper.return_value = mock_scraper_fail
        scrape_chunk(
            ["http://example.com/1", "http://example.com/2", "http://example.com/3"],
            "job_shared",
            "imot.bg"
        )

        # Circuit should be open
        assert redis_circuit_breaker.can_request("example.com") is False

        # Worker 2: Try to scrape (should be blocked)
        mock_get_scraper.return_value = mock_scraper_ok
        results = scrape_chunk(["http://example.com/4"], "job_shared", "imot.bg")

        # Worker 2 blocked by shared circuit state
        assert results[0]["error"] == "circuit_open"
        assert results[0]["skipped"] is True

        # Verify scraper was never called (circuit blocked it)
        mock_scraper_ok.extract_listing.assert_not_called()


class TestRateLimiterSharing:
    """Test rate limiter enforcement across workers (when enabled)."""

    @pytest.fixture
    def redis_rate_limiter(self, fake_redis):
        """Create Redis-backed rate limiter with fake Redis."""
        from resilience.redis_rate_limiter import RedisRateLimiter

        # Use a low rate limit for testing (5 req/min)
        limiter = RedisRateLimiter(
            host="localhost",
            port=6379,
            db=0,
            rate_limits={"example.com": 5, "default": 10},
        )
        limiter.redis = fake_redis
        return limiter

    @patch.dict(os.environ, {"REDIS_RATE_LIMITER_ENABLED": "true"})
    @patch("scraping.async_fetcher.get_rate_limiter")
    @patch("scraping.tasks.get_redis_client")
    def test_rate_enforced_globally_across_workers(
        self, mock_redis, mock_get_limiter, fake_redis, redis_rate_limiter, celery_eager_mode
    ):
        """Rate limit should be enforced globally across all workers."""
        mock_redis.return_value = fake_redis
        mock_get_limiter.return_value = redis_rate_limiter

        domain = "example.com"

        # Worker 1: Make 3 requests (uses non-blocking acquire)
        with patch("time.time", return_value=100.0):
            for i in range(3):
                result = redis_rate_limiter.acquire(domain, blocking=False)
                assert result is True, f"Worker 1 request {i+1} should succeed"

        # Worker 2: Make 2 more requests (total 5, at limit)
        with patch("time.time", return_value=100.0):
            for i in range(2):
                result = redis_rate_limiter.acquire(domain, blocking=False)
                assert result is True, f"Worker 2 request {i+1} should succeed"

        # Worker 3: Next request should be blocked (exceeded limit)
        with patch("time.time", return_value=100.0):
            result = redis_rate_limiter.acquire(domain, blocking=False)
            assert result is False, "Worker 3 should be rate limited"

        # After time passes (tokens refill), requests allowed again
        # At 5 req/min, tokens refill at 5/60 = 0.083 tokens/sec
        # After 12 seconds, we get 1 token back
        with patch("time.time", return_value=112.0):  # 12 seconds later
            result = redis_rate_limiter.acquire(domain, blocking=False)
            assert result is True, "After refill period, request should succeed"


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    def test_handles_empty_search_results(
        self, mock_redis, mock_config, mock_get_scraper, mock_asyncio, fake_redis, celery_eager_mode
    ):
        """Should handle case when search returns no listing URLs."""
        mock_redis.return_value = fake_redis

        # Scraper returns empty list
        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = []
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        result = dispatch_site_scraping("imot.bg", ["http://search.url"])

        assert result["status"] == "NO_URLS"
        assert result["total_urls"] == 0

        # Should still mark as complete
        job_id = result["job_id"]
        assert fake_redis.get(ScrapingKeys.status(job_id)) == "COMPLETE"

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_handles_partial_chunk_failures(
        self, mock_redis, mock_save, fake_redis, celery_eager_mode
    ):
        """Should handle when some chunks succeed and others fail."""
        mock_redis.return_value = fake_redis

        # Simulate mixed results with None (failed task)
        chunk_results = [
            [{"title": "Success 1"}],
            None,  # Failed task
            [{"title": "Success 2"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results(chunk_results, "job_mixed", "imot.bg")

        # Should save successful results
        assert result["saved"] == 2
        assert result["errors"] == 0

        # Job should still complete
        assert fake_redis.get(ScrapingKeys.status("job_mixed")) == "COMPLETE"

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_handles_database_save_errors(
        self, mock_redis, mock_save, fake_redis, celery_eager_mode
    ):
        """Should handle database errors during aggregation."""
        mock_redis.return_value = fake_redis

        # Mock save to raise exception
        mock_save.side_effect = Exception("Database connection failed")

        chunk_results = [
            [{"title": "Listing 1", "url": "http://test.com"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results(chunk_results, "job_db_error", "imot.bg")

        # Should count as error
        assert result["saved"] == 0
        assert result["errors"] == 1

        # Job should still complete
        assert fake_redis.get(ScrapingKeys.status("job_db_error")) == "COMPLETE"
