"""Unit tests for scraping.tasks module."""
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch, call, Mock

import pytest

from scraping.tasks import (
    get_redis_client,
    dispatch_site_scraping,
    scrape_chunk,
    aggregate_results,
    scrape_all_sites,
    PROGRESS_KEY_TTL,
)
from scraping.redis_keys import ScrapingKeys


class TestGetRedisClient:
    """Tests for get_redis_client() singleton."""

    @patch("scraping.tasks.redis.Redis")
    def test_returns_redis_instance(self, mock_redis_class):
        """Should create and return Redis client instance."""
        # Reset singleton
        import scraping.tasks
        scraping.tasks._redis_client = None

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        result = get_redis_client()

        assert result is mock_client
        mock_redis_class.assert_called_once_with(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True,
        )

    @patch("scraping.tasks.redis.Redis")
    def test_reuses_singleton(self, mock_redis_class):
        """Should reuse existing Redis client."""
        # Reset singleton
        import scraping.tasks
        scraping.tasks._redis_client = None

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        result1 = get_redis_client()
        result2 = get_redis_client()

        assert result1 is result2
        assert mock_redis_class.call_count == 1

    @patch.dict(os.environ, {"REDIS_HOST": "custom-host", "REDIS_PORT": "7777", "REDIS_BROKER_DB": "5"})
    @patch("scraping.tasks.redis.Redis")
    def test_uses_environment_variables(self, mock_redis_class):
        """Should use environment variables for Redis config."""
        # Reset singleton
        import scraping.tasks
        scraping.tasks._redis_client = None

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        get_redis_client()

        mock_redis_class.assert_called_once_with(
            host="custom-host",
            port=7777,
            db=5,
            decode_responses=True,
        )


class TestDispatchSiteScraping:
    """Tests for dispatch_site_scraping() task."""

    @patch("scraping.tasks.chord")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.uuid.uuid4")
    @patch("scraping.tasks.asyncio.run")
    def test_creates_job_with_site_name(
        self, mock_asyncio, mock_uuid, mock_redis, mock_config, mock_get_scraper, mock_chord
    ):
        """Should create job_id with site name and uuid."""
        mock_uuid.return_value.hex = "abcd1234abcd1234"
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = ["url1", "url2"]
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        mock_workflow = MagicMock()
        mock_workflow_result = MagicMock(id="chord_123")
        mock_workflow.apply_async.return_value = mock_workflow_result
        mock_chord.return_value = mock_workflow

        # Create a mock task with 's' method
        mock_task = MagicMock()
        with patch("scraping.tasks.scrape_chunk", mock_task):
            with patch("scraping.tasks.aggregate_results", MagicMock()):
                result = dispatch_site_scraping("imot.bg", ["start_url"])

        assert result["job_id"] == "scrape_imot.bg_abcd1234"
        assert "chord_id" in result
        assert result["total_urls"] == 2

    @patch("scraping.tasks.chord")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.uuid.uuid4")
    @patch("scraping.tasks.time.time")
    @patch("scraping.tasks.asyncio.run")
    def test_sets_redis_keys_on_start(
        self, mock_asyncio, mock_time, mock_uuid, mock_redis, mock_config, mock_get_scraper, mock_chord
    ):
        """Should set initial Redis keys for job tracking."""
        mock_time.return_value = 1234567890
        mock_uuid.return_value.hex = "abcd1234"
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = ["url1"]
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        mock_workflow = MagicMock()
        mock_workflow_result = MagicMock(id="chord_123")
        mock_workflow.apply_async.return_value = mock_workflow_result
        mock_chord.return_value = mock_workflow

        mock_task = MagicMock()
        with patch("scraping.tasks.scrape_chunk", mock_task):
            with patch("scraping.tasks.aggregate_results", MagicMock()):
                dispatch_site_scraping("imot.bg", ["start_url"])

        job_id = "scrape_imot.bg_abcd1234"

        # Check initial COLLECTING status
        assert call(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "COLLECTING") in mock_redis_client.setex.call_args_list
        assert call(ScrapingKeys.started_at(job_id), PROGRESS_KEY_TTL, 1234567890) in mock_redis_client.setex.call_args_list

        # Check DISPATCHED status after collecting URLs
        assert call(ScrapingKeys.status(job_id), PROGRESS_KEY_TTL, "DISPATCHED") in mock_redis_client.setex.call_args_list
        assert call(ScrapingKeys.total_urls(job_id), PROGRESS_KEY_TTL, 1) in mock_redis_client.setex.call_args_list

    @patch("websites.get_scraper")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.uuid.uuid4")
    def test_handles_scraper_not_found(self, mock_uuid, mock_redis, mock_get_scraper):
        """Should return error when scraper not found."""
        mock_uuid.return_value.hex = "abcd1234"
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        mock_get_scraper.return_value = None

        result = dispatch_site_scraping("unknown_site", ["start_url"])

        assert result["job_id"] == "scrape_unknown_site_abcd1234"
        assert "error" in result
        assert "No scraper for site" in result["error"]
        mock_redis_client.setex.assert_any_call(
            ScrapingKeys.status("scrape_unknown_site_abcd1234"),
            PROGRESS_KEY_TTL,
            "FAILED"
        )

    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.uuid.uuid4")
    @patch("scraping.tasks.asyncio.run")
    def test_handles_no_urls_collected(
        self, mock_asyncio, mock_uuid, mock_redis, mock_config, mock_get_scraper
    ):
        """Should handle case when no URLs are collected."""
        mock_uuid.return_value.hex = "abcd1234"
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = []
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        result = dispatch_site_scraping("imot.bg", ["start_url"])

        assert result["status"] == "NO_URLS"
        assert result["total_urls"] == 0
        mock_redis_client.setex.assert_any_call(
            ScrapingKeys.status("scrape_imot.bg_abcd1234"),
            PROGRESS_KEY_TTL,
            "COMPLETE"
        )
        mock_redis_client.setex.assert_any_call(
            ScrapingKeys.result_count("scrape_imot.bg_abcd1234"),
            PROGRESS_KEY_TTL,
            0
        )

    @patch("scraping.tasks.chord")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.uuid.uuid4")
    @patch("scraping.tasks.asyncio.run")
    def test_chunks_urls_correctly(
        self, mock_asyncio, mock_uuid, mock_redis, mock_config, mock_get_scraper, mock_chord
    ):
        """Should chunk URLs based on config."""
        mock_uuid.return_value.hex = "abcd1234"
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        # Generate 50 URLs
        urls = [f"url{i}" for i in range(50)]
        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = urls
        mock_get_scraper.return_value = mock_scraper

        # max_per_domain=2, so chunk_size = 2*10 = 20
        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        mock_workflow = MagicMock()
        mock_workflow_result = MagicMock(id="chord_123")
        mock_workflow.apply_async.return_value = mock_workflow_result
        mock_chord.return_value = mock_workflow

        mock_task = MagicMock()
        with patch("scraping.tasks.scrape_chunk", mock_task):
            with patch("scraping.tasks.aggregate_results", MagicMock()):
                result = dispatch_site_scraping("imot.bg", ["start_url"])

        # 50 URLs / 20 per chunk = 3 chunks
        assert result["total_chunks"] == 3
        mock_redis_client.setex.assert_any_call(
            ScrapingKeys.total_chunks("scrape_imot.bg_abcd1234"),
            PROGRESS_KEY_TTL,
            3
        )

    @patch("scraping.tasks.group")
    @patch("scraping.tasks.chord")
    @patch("websites.get_scraper")
    @patch("config.scraping_config.load_scraping_config")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.uuid.uuid4")
    @patch("scraping.tasks.asyncio.run")
    def test_calls_chord_with_workers_and_callback(
        self, mock_asyncio, mock_uuid, mock_redis, mock_config, mock_get_scraper, mock_chord, mock_group
    ):
        """Should create chord with worker tasks and callback."""
        mock_uuid.return_value.hex = "abcd1234"
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = ["url1", "url2"]
        mock_get_scraper.return_value = mock_scraper

        mock_config.return_value = MagicMock(concurrency=MagicMock(max_per_domain=2))
        mock_asyncio.return_value = "<html></html>"

        mock_workers = MagicMock()
        mock_group.return_value = mock_workers

        mock_workflow = MagicMock()
        mock_workflow_result = MagicMock(id="chord_123")
        mock_workflow.apply_async.return_value = mock_workflow_result
        mock_chord.return_value = mock_workflow

        mock_scrape_task = MagicMock()
        mock_aggregate_task = MagicMock()
        mock_callback = MagicMock()
        mock_aggregate_task.s.return_value = mock_callback

        with patch("scraping.tasks.scrape_chunk", mock_scrape_task):
            with patch("scraping.tasks.aggregate_results", mock_aggregate_task):
                dispatch_site_scraping("imot.bg", ["start_url"])

        # Verify chord was called with workers and callback
        mock_chord.assert_called_once_with(mock_workers, mock_callback)
        mock_workflow.apply_async.assert_called_once()


class TestScrapeChunk:
    """Tests for scrape_chunk() worker task."""

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    def test_skips_urls_when_circuit_breaker_open(
        self, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should skip URLs when circuit breaker is open."""
        mock_scraper = MagicMock()
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = False
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        urls = ["http://example.com/1", "http://example.com/2"]
        results = scrape_chunk(urls, "job_123", "imot.bg")

        assert len(results) == 2
        assert all(r["error"] == "circuit_open" for r in results)
        assert all(r["skipped"] is True for r in results)

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.asyncio.run")
    def test_calls_fetch_page_for_each_url(
        self, mock_asyncio, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should call fetch_page for each URL."""
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = True
        mock_get_cb.return_value = mock_cb

        mock_asyncio.return_value = "<html></html>"

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        urls = ["http://example.com/1", "http://example.com/2"]
        scrape_chunk(urls, "job_123", "imot.bg")

        assert mock_asyncio.call_count == 2

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.asyncio.run")
    def test_calls_scraper_extract_listing(
        self, mock_asyncio, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should call scraper.extract_listing for each fetched page."""
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = True
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        url = "http://example.com/1"
        mock_asyncio.return_value = "<html>content</html>"

        scrape_chunk([url], "job_123", "imot.bg")

        mock_scraper.extract_listing.assert_called_once_with("<html>content</html>", url)

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.asyncio.run")
    def test_converts_listing_data_to_dict(
        self, mock_asyncio, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should convert ListingData to dict."""
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        listing_dict = {"title": "Test Listing", "price": 1000}
        mock_listing.to_dict.return_value = listing_dict
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = True
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_asyncio.return_value = "<html></html>"
        results = scrape_chunk(["http://example.com/1"], "job_123", "imot.bg")

        assert results[0] == listing_dict

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.asyncio.run")
    def test_records_success_on_circuit_breaker(
        self, mock_asyncio, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should record success on circuit breaker for successful extractions."""
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = True
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_asyncio.return_value = "<html></html>"
        scrape_chunk(["http://example.com/1"], "job_123", "imot.bg")

        mock_cb.record_success.assert_called_once_with("example.com")

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.asyncio.run")
    def test_records_failure_on_circuit_breaker(
        self, mock_asyncio, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should record failure on circuit breaker for exceptions."""
        mock_scraper = MagicMock()
        mock_scraper.extract_listing.side_effect = ValueError("Parse error")
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = True
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_asyncio.return_value = "<html></html>"
        results = scrape_chunk(["http://example.com/1"], "job_123", "imot.bg")

        mock_cb.record_failure.assert_called_once_with("example.com", "ValueError")
        assert results[0]["error"] == "Parse error"

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.asyncio.run")
    def test_updates_redis_progress(
        self, mock_asyncio, mock_get_scraper, mock_get_cb, mock_redis
    ):
        """Should update Redis progress after processing chunk."""
        mock_scraper = MagicMock()
        mock_listing = MagicMock()
        mock_listing.to_dict.return_value = {"title": "Test"}
        mock_scraper.extract_listing.return_value = mock_listing
        mock_get_scraper.return_value = mock_scraper

        mock_cb = MagicMock()
        mock_cb.can_request.return_value = True
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_asyncio.return_value = "<html></html>"
        scrape_chunk(["http://example.com/1"], "job_123", "imot.bg")

        mock_redis_client.incr.assert_called_once_with(
            ScrapingKeys.completed_chunks("job_123")
        )
        mock_redis_client.setex.assert_called_once_with(
            ScrapingKeys.status("job_123"),
            PROGRESS_KEY_TTL,
            "PROCESSING"
        )

    @patch("scraping.tasks.get_redis_client")
    @patch("resilience.get_circuit_breaker")
    @patch("websites.get_scraper")
    def test_handles_no_scraper(self, mock_get_scraper, mock_get_cb, mock_redis):
        """Should handle case when scraper is not found."""
        mock_get_scraper.return_value = None

        mock_cb = MagicMock()
        mock_get_cb.return_value = mock_cb

        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        urls = ["http://example.com/1", "http://example.com/2"]
        results = scrape_chunk(urls, "job_123", "unknown_site")

        assert len(results) == 2
        assert all(r["error"] == "no_scraper" for r in results)
        assert all(r["skipped"] is True for r in results)


class TestAggregateResults:
    """Tests for aggregate_results() callback task."""

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_flattens_chunk_results(self, mock_redis, mock_save):
        """Should flatten results from multiple chunks."""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        chunk_results = [
            [{"title": "Listing 1"}, {"title": "Listing 2"}],
            [{"title": "Listing 3"}],
            [{"url": "error_url", "error": "failed"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            aggregate_results(chunk_results, "job_123", "imot.bg")

        # Should save 3 successful listings
        assert mock_save.call_count == 3

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.time.time")
    def test_separates_successes_from_errors(self, mock_time, mock_redis, mock_save):
        """Should separate successful listings from errors."""
        mock_time.return_value = 1234567890
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        chunk_results = [
            [{"title": "Success 1"}, {"url": "url1", "error": "failed"}],
            [{"title": "Success 2"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results(chunk_results, "job_123", "imot.bg")

        assert result["saved"] == 2
        assert result["errors"] == 1

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_calls_save_listing_for_each_success(self, mock_redis, mock_save):
        """Should call save_listing for each successful listing."""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        chunk_results = [
            [{"title": "Listing 1", "price": 1000}],
            [{"title": "Listing 2", "price": 2000}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_instance = MagicMock()
            mock_listing_class.return_value = mock_listing_instance
            aggregate_results(chunk_results, "job_123", "imot.bg")

        assert mock_save.call_count == 2
        assert mock_listing_class.call_count == 2

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    @patch("scraping.tasks.time.time")
    def test_sets_final_redis_keys(self, mock_time, mock_redis, mock_save):
        """Should set final Redis keys with completion status."""
        mock_time.return_value = 1234567890
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        chunk_results = [
            [{"title": "Listing 1"}],
            [{"url": "url1", "error": "failed"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            aggregate_results(chunk_results, "job_123", "imot.bg")

        # Check Redis calls
        assert call(ScrapingKeys.status("job_123"), PROGRESS_KEY_TTL, "AGGREGATING") in mock_redis_client.setex.call_args_list
        assert call(ScrapingKeys.status("job_123"), PROGRESS_KEY_TTL, "COMPLETE") in mock_redis_client.setex.call_args_list
        assert call(ScrapingKeys.completed_at("job_123"), PROGRESS_KEY_TTL, 1234567890) in mock_redis_client.setex.call_args_list
        assert call(ScrapingKeys.result_count("job_123"), PROGRESS_KEY_TTL, 1) in mock_redis_client.setex.call_args_list
        assert call(ScrapingKeys.error_count("job_123"), PROGRESS_KEY_TTL, 1) in mock_redis_client.setex.call_args_list

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_handles_db_errors(self, mock_redis, mock_save):
        """Should handle database save errors gracefully."""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        mock_save.side_effect = Exception("DB error")

        chunk_results = [
            [{"title": "Listing 1", "url": "url1"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results(chunk_results, "job_123", "imot.bg")

        # Should have 0 saved, 1 error
        assert result["saved"] == 0
        assert result["errors"] == 1

    @patch("data.data_store_main.save_listing")
    @patch("scraping.tasks.get_redis_client")
    def test_handles_none_chunks(self, mock_redis, mock_save):
        """Should handle None chunks from failed tasks."""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        chunk_results = [
            [{"title": "Listing 1"}],
            None,  # Failed task
            [{"title": "Listing 2"}],
        ]

        with patch("websites.ListingData") as mock_listing_class:
            mock_listing_class.return_value = MagicMock()
            result = aggregate_results(chunk_results, "job_123", "imot.bg")

        assert result["saved"] == 2


class TestScrapeAllSites:
    """Tests for scrape_all_sites() task."""

    @patch("scraping.tasks.group")
    def test_creates_group_of_dispatch_tasks(self, mock_group):
        """Should create group of dispatch tasks for each site."""
        mock_result = MagicMock(id="group_456")
        mock_group_instance = MagicMock()
        mock_group_instance.apply_async.return_value = mock_result
        mock_group.return_value = mock_group_instance

        sites_config = {
            "imot.bg": ["url1", "url2"],
            "bazar.bg": ["url3"],
        }

        with patch("scraping.tasks.dispatch_site_scraping") as mock_dispatch:
            result = scrape_all_sites(sites_config)

        assert result["group_id"] == "group_456"
        assert set(result["sites"]) == {"imot.bg", "bazar.bg"}

    @patch("scraping.tasks.group")
    def test_returns_group_id_and_sites_list(self, mock_group):
        """Should return group_id and sites list."""
        mock_result = MagicMock(id="group_789")
        mock_group_instance = MagicMock()
        mock_group_instance.apply_async.return_value = mock_result
        mock_group.return_value = mock_group_instance

        sites_config = {
            "imot.bg": ["url1"],
        }

        with patch("scraping.tasks.dispatch_site_scraping"):
            result = scrape_all_sites(sites_config)

        assert "group_id" in result
        assert "sites" in result
        assert isinstance(result["sites"], list)
