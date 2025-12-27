"""
Unit tests for config/scraping_config.py
"""

import pytest

from config.scraping_config import (
    AntiDetectionConfig,
    ConcurrencyConfig,
    FetcherConfig,
    RetryConfig,
    ScrapingConfig,
    TimingConfig,
    load_scraping_config,
    _normalize_site_name,
)


class TestLoadDefaults:
    """Test loading config with no site override (unknown site)."""

    def test_load_defaults_only(self):
        """Config loads correctly when no site override exists."""
        config = load_scraping_config("unknown-site.com")

        # Should return default values
        assert config.timing.delay_seconds == 2.0
        assert config.concurrency.max_per_domain == 2
        assert config.concurrency.max_global == 16
        assert config.retry.max_attempts == 3
        assert config.fetcher.search_pages == "http"
        assert config.fetcher.listing_pages == "http"
        assert config.anti_detection.rotate_user_agent is True
        assert config.anti_detection.humanize_actions is False


class TestSiteOverride:
    """Test site-specific overrides merge with defaults."""

    def test_site_override_merges(self):
        """Site override merges with defaults."""
        config = load_scraping_config("imot.bg")

        # Override values
        assert config.timing.delay_seconds == 1.5
        assert config.concurrency.max_per_domain == 3

        # Default values (not overridden)
        assert config.retry.max_attempts == 3
        assert config.timing.randomize_delay is True
        assert config.timeouts.request_seconds == 60


class TestDeepMerge:
    """Test nested dict merging."""

    def test_deep_merge_nested(self):
        """Nested dicts merge correctly."""
        config = load_scraping_config("bazar.bg")

        # Override values in fetcher
        assert config.fetcher.search_pages == "stealth"
        assert config.fetcher.listing_pages == "http"

        # Override values in timing
        assert config.timing.delay_seconds == 3.0

        # Default values still present
        assert config.timing.randomize_delay is True
        assert config.timing.random_delay_min == 0.5


class TestNormalizeSiteName:
    """Test site name normalization."""

    def test_normalize_site_name(self):
        """Site names convert to filenames."""
        assert _normalize_site_name("imot.bg") == "imot_bg"
        assert _normalize_site_name("my-site.com") == "my_site_com"
        assert _normalize_site_name("test.example-site.com") == "test_example_site_com"
        assert _normalize_site_name("simple") == "simple"


class TestDataclassTypes:
    """Test config returns proper dataclass types."""

    def test_dataclass_types(self):
        """Config returns proper dataclass types."""
        config = load_scraping_config("imot.bg")

        assert isinstance(config, ScrapingConfig)
        assert isinstance(config.timing, TimingConfig)
        assert isinstance(config.concurrency, ConcurrencyConfig)
        assert isinstance(config.retry, RetryConfig)
        assert isinstance(config.fetcher, FetcherConfig)
        assert isinstance(config.anti_detection, AntiDetectionConfig)


class TestBazarAntiDetection:
    """Test bazar.bg specific anti-detection settings."""

    def test_bazar_anti_detection(self):
        """bazar.bg has anti-detection enabled."""
        config = load_scraping_config("bazar.bg")

        # Anti-detection settings
        assert config.anti_detection.humanize_actions is True
        assert config.anti_detection.rotate_user_agent is True

        # Timing and concurrency for anti-detection
        assert config.timing.delay_seconds == 3.0
        assert config.concurrency.max_per_domain == 1


class TestSiteAttribute:
    """Test that site name is stored in config."""

    def test_site_name_stored(self):
        """Site name is stored in config object."""
        config = load_scraping_config("imot.bg")
        assert config.site == "imot.bg"

        config2 = load_scraping_config("bazar.bg")
        assert config2.site == "bazar.bg"
