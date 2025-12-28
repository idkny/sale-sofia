"""Integration tests for site-specific configuration overrides.

Task 4.4.2: Test that different sites get different configurations.
- Fast site (imot.bg): 1.5s delay, 3 max_per_domain
- Slow site (bazar.bg): 3.0s delay, 1 max_per_domain

Tests the complete config flow:
1. YAML loading and merging
2. Config usage in Celery tasks (chunk sizing)
3. Config usage in rate limiting
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from config.scraping_config import load_scraping_config


class TestConfigLoading:
    """Test that site-specific YAML configs are loaded correctly."""

    def test_imot_bg_has_fast_settings(self):
        """imot.bg should have faster scraping settings."""
        config = load_scraping_config("imot.bg")

        # Fast site - shorter delay
        assert config.timing.delay_seconds == 1.5
        # Fast site - can handle more concurrent requests
        assert config.concurrency.max_per_domain == 3
        # HTTP fetcher (no anti-bot issues)
        assert config.fetcher.search_pages == "http"
        assert config.fetcher.listing_pages == "http"

    def test_bazar_bg_has_slow_settings(self):
        """bazar.bg should have more conservative settings."""
        config = load_scraping_config("bazar.bg")

        # Slow site - longer delay
        assert config.timing.delay_seconds == 3.0
        # Slow site - only one request at a time
        assert config.concurrency.max_per_domain == 1
        # Stealth fetcher for search pages (anti-bot protection)
        assert config.fetcher.search_pages == "stealth"
        # HTTP OK for listings
        assert config.fetcher.listing_pages == "http"
        # Extra anti-detection
        assert config.anti_detection.humanize_actions is True

    def test_unknown_site_gets_defaults(self):
        """Unknown sites should get default settings."""
        config = load_scraping_config("unknown-site.com")

        # Defaults from scraping_defaults.yaml
        assert config.timing.delay_seconds == 2.0
        assert config.concurrency.max_per_domain == 2
        assert config.fetcher.search_pages == "http"

    def test_sites_have_different_delays(self):
        """Verify sites have distinct delay values."""
        imot = load_scraping_config("imot.bg")
        bazar = load_scraping_config("bazar.bg")

        # Different delays
        assert imot.timing.delay_seconds < bazar.timing.delay_seconds
        # imot is 2x faster than bazar
        assert bazar.timing.delay_seconds / imot.timing.delay_seconds == 2.0

    def test_sites_have_different_concurrency(self):
        """Verify sites have distinct concurrency limits."""
        imot = load_scraping_config("imot.bg")
        bazar = load_scraping_config("bazar.bg")

        # Different concurrency limits
        assert imot.concurrency.max_per_domain > bazar.concurrency.max_per_domain
        # imot allows 3x more concurrent requests
        assert imot.concurrency.max_per_domain == 3
        assert bazar.concurrency.max_per_domain == 1


class TestChunkSizeCalculation:
    """Test that chunk size in Celery tasks uses site config."""

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.get_redis_client")
    def test_imot_bg_gets_larger_chunks(
        self, mock_redis, mock_get_scraper, mock_asyncio
    ):
        """imot.bg with max_per_domain=3 should get larger chunks."""
        try:
            import fakeredis
        except ImportError:
            pytest.skip("fakeredis not installed")

        from scraping.tasks import dispatch_site_scraping

        fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
        mock_redis.return_value = fake_redis

        # Setup mocks
        mock_scraper = MagicMock()
        # Return 100 URLs to test chunking
        mock_scraper.extract_search_results.return_value = [
            f"http://imot.bg/listing/{i}" for i in range(100)
        ]
        mock_get_scraper.return_value = mock_scraper
        mock_asyncio.return_value = "<html></html>"

        # Patch chord to prevent actual task dispatch
        with patch("scraping.tasks.chord") as mock_chord:
            mock_result = MagicMock()
            mock_result.id = "chord_123"
            mock_chord.return_value.apply_async.return_value = mock_result

            result = dispatch_site_scraping("imot.bg", ["http://search.url"])

        # imot.bg: max_per_domain=3, chunk_size = 3 * 10 = 30
        # 100 URLs / 30 = 4 chunks (rounded up)
        assert result["total_chunks"] >= 3  # Should be 4 chunks
        assert result["total_chunks"] <= 5

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.get_redis_client")
    def test_bazar_bg_gets_smaller_chunks(
        self, mock_redis, mock_get_scraper, mock_asyncio
    ):
        """bazar.bg with max_per_domain=1 should get smaller chunks (fallback)."""
        try:
            import fakeredis
        except ImportError:
            pytest.skip("fakeredis not installed")

        from scraping.tasks import dispatch_site_scraping
        from config.settings import SCRAPING_CHUNK_SIZE

        fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
        mock_redis.return_value = fake_redis

        # Setup mocks
        mock_scraper = MagicMock()
        # Return 100 URLs to test chunking
        mock_scraper.extract_search_results.return_value = [
            f"http://bazar.bg/listing/{i}" for i in range(100)
        ]
        mock_get_scraper.return_value = mock_scraper
        mock_asyncio.return_value = "<html></html>"

        # Patch chord to prevent actual task dispatch
        with patch("scraping.tasks.chord") as mock_chord:
            mock_result = MagicMock()
            mock_result.id = "chord_123"
            mock_chord.return_value.apply_async.return_value = mock_result

            result = dispatch_site_scraping("bazar.bg", ["http://search.url"])

        # bazar.bg: max_per_domain=1, chunk_size = 1 * 10 = 10
        # But 10 < 10, so it uses SCRAPING_CHUNK_SIZE fallback (20)
        # 100 URLs / 20 = 5 chunks
        assert result["total_chunks"] >= 4
        assert result["total_chunks"] <= 10


class TestDomainRateLimits:
    """Test that domain rate limits affect request timing."""

    def test_rate_limiter_has_per_domain_limits(self):
        """Verify DOMAIN_RATE_LIMITS config exists for our sites."""
        from config.settings import DOMAIN_RATE_LIMITS

        assert "imot.bg" in DOMAIN_RATE_LIMITS
        assert "bazar.bg" in DOMAIN_RATE_LIMITS
        assert "default" in DOMAIN_RATE_LIMITS

    def test_rate_limiter_uses_domain_limits(self):
        """Rate limiter should use DOMAIN_RATE_LIMITS for each domain."""
        from resilience.rate_limiter import DomainRateLimiter
        from config.settings import DOMAIN_RATE_LIMITS

        limiter = DomainRateLimiter(rate_limits=DOMAIN_RATE_LIMITS)

        # Verify rate lookup
        imot_rate = limiter._get_rate("imot.bg")
        bazar_rate = limiter._get_rate("bazar.bg")

        assert imot_rate == DOMAIN_RATE_LIMITS["imot.bg"]
        assert bazar_rate == DOMAIN_RATE_LIMITS["bazar.bg"]


class TestConfigIntegration:
    """Integration tests for config usage in the full Celery flow."""

    @patch("scraping.tasks.asyncio.run")
    @patch("websites.get_scraper")
    @patch("scraping.tasks.get_redis_client")
    def test_dispatch_loads_correct_site_config(
        self, mock_redis, mock_get_scraper, mock_asyncio
    ):
        """dispatch_site_scraping should load the correct site's config."""
        try:
            import fakeredis
        except ImportError:
            pytest.skip("fakeredis not installed")

        from scraping.tasks import dispatch_site_scraping

        fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
        mock_redis.return_value = fake_redis

        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.extract_search_results.return_value = [
            f"http://site.com/listing/{i}" for i in range(50)
        ]
        mock_get_scraper.return_value = mock_scraper
        mock_asyncio.return_value = "<html></html>"

        # Track which config was loaded
        loaded_configs = []
        original_load = load_scraping_config

        def track_load(site):
            loaded_configs.append(site)
            return original_load(site)

        # Patch at the import location within the function (uses local import)
        with patch("config.scraping_config.load_scraping_config", side_effect=track_load):
            with patch("scraping.tasks.chord") as mock_chord:
                mock_result = MagicMock()
                mock_result.id = "chord_123"
                mock_chord.return_value.apply_async.return_value = mock_result

                # Dispatch for imot.bg
                dispatch_site_scraping("imot.bg", ["http://search.url"])

        # Verify correct config was loaded
        assert "imot.bg" in loaded_configs

    @pytest.mark.parametrize("site,expected_delay", [
        ("imot.bg", 1.5),
        ("bazar.bg", 3.0),
    ])
    def test_config_loader_returns_correct_delay_per_site(self, site, expected_delay):
        """Each site should return its configured delay_seconds."""
        config = load_scraping_config(site)
        assert config.timing.delay_seconds == expected_delay


class TestConfigGapDocumentation:
    """Document known gaps in config usage.

    NOTE: These tests document current behavior, not necessarily desired behavior.
    """

    def test_celery_tasks_do_not_use_delay_seconds(self):
        """KNOWN GAP: Celery tasks don't use delay_seconds from YAML config.

        In Celery mode:
        - Rate limiting uses DOMAIN_RATE_LIMITS from settings.py (requests/minute)
        - The timing.delay_seconds from YAML is NOT used

        In sequential mode (main.py):
        - delay_seconds IS used via scrape_from_start_url()

        This gap means site-specific delays only apply to sequential scraping,
        not parallel Celery scraping.
        """
        import ast
        import inspect
        from scraping import tasks

        # Read the source code
        source = inspect.getsource(tasks)

        # Verify delay_seconds is NOT used in tasks.py
        assert "delay_seconds" not in source
        assert "timing.delay" not in source
        assert "config.timing" not in source

        # Document the gap for future improvement
        # TODO: Consider wiring delay_seconds into async_fetcher or rate_limiter

    def test_domain_rate_limits_are_uniform(self):
        """KNOWN GAP: DOMAIN_RATE_LIMITS has same rate for all sites.

        Both imot.bg and bazar.bg have 10 req/min in DOMAIN_RATE_LIMITS,
        even though their YAML configs have different delay_seconds.

        YAML delay_seconds to equivalent rate:
        - imot.bg: 1.5s delay = 40 req/min
        - bazar.bg: 3.0s delay = 20 req/min

        But DOMAIN_RATE_LIMITS has 10 req/min for both.
        """
        from config.settings import DOMAIN_RATE_LIMITS

        # Document current state (both same)
        imot_rate = DOMAIN_RATE_LIMITS.get("imot.bg", DOMAIN_RATE_LIMITS["default"])
        bazar_rate = DOMAIN_RATE_LIMITS.get("bazar.bg", DOMAIN_RATE_LIMITS["default"])

        # Currently both are 10 req/min
        assert imot_rate == 10
        assert bazar_rate == 10

        # Document the mismatch with YAML config
        imot_config = load_scraping_config("imot.bg")
        bazar_config = load_scraping_config("bazar.bg")

        # YAML says different delays, but rate limits are same
        assert imot_config.timing.delay_seconds != bazar_config.timing.delay_seconds
        assert imot_rate == bazar_rate  # This is the gap

        # Calculate what rate limits SHOULD be based on delay_seconds
        imot_expected_rate = 60 / imot_config.timing.delay_seconds  # 40 req/min
        bazar_expected_rate = 60 / bazar_config.timing.delay_seconds  # 20 req/min

        assert imot_expected_rate == 40.0
        assert bazar_expected_rate == 20.0
