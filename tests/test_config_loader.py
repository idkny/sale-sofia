"""
Unit tests for websites.generic.config_loader module.

Tests:
- get_config_path: Convert site names to config file paths
- validate_config: Validate raw config dictionaries
- load_config: Load and parse YAML config files
"""

import pytest
import yaml
from pathlib import Path

from websites.generic.config_loader import (
    GenericScraperConfig,
    SiteInfo,
    UrlPatterns,
    PaginationConfig,
    ListingPageConfig,
    DetailPageConfig,
    ExtractionConfig,
    TimingConfig,
    QuirksConfig,
    get_config_path,
    validate_config,
    load_config,
)


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_simple_domain(self):
        result = get_config_path("olx.bg")
        assert result.name == "olx_bg.yaml"
        assert "config/sites" in str(result)

    def test_domain_with_subdomain(self):
        result = get_config_path("homes.bg")
        assert result.name == "homes_bg.yaml"

    def test_domain_with_hyphen(self):
        result = get_config_path("imot-bg.com")
        assert result.name == "imot_bg_com.yaml"

    def test_complex_domain(self):
        result = get_config_path("estate.imoti.net")
        assert result.name == "estate_imoti_net.yaml"

    def test_returns_path_object(self):
        result = get_config_path("test.bg")
        assert isinstance(result, Path)


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config_returns_empty_list(self):
        config = {
            "site": {
                "name": "Test Site",
                "domain": "test.bg"
            },
            "urls": {
                "listing_pattern": "/ads/",
                "id_pattern": r"/ad/(\d+)"
            },
            "listing_page": {
                "container": ".card",
                "link": "a.card-link"
            },
            "detail_page": {
                "selectors": {
                    "title": ["h1.title", "h1"],
                    "price": [".price", ".cost"]
                }
            }
        }
        errors = validate_config(config)
        assert errors == []

    def test_missing_site_section(self):
        config = {
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "Missing required section: site" in errors

    def test_missing_urls_section(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "Missing required section: urls" in errors

    def test_missing_listing_page_section(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "Missing required section: listing_page" in errors

    def test_missing_detail_page_section(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"}
        }
        errors = validate_config(config)
        assert "Missing required section: detail_page" in errors

    def test_missing_site_name(self):
        config = {
            "site": {"domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "site.name is required" in errors

    def test_missing_site_domain(self):
        config = {
            "site": {"name": "Test Site"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "site.domain is required" in errors

    def test_missing_urls_listing_pattern(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "urls.listing_pattern is required" in errors

    def test_missing_urls_id_pattern(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "urls.id_pattern is required" in errors

    def test_missing_listing_page_container(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"link": "a"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "listing_page.container is required" in errors

    def test_missing_listing_page_link(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card"},
            "detail_page": {"selectors": {"title": ["h1"]}}
        }
        errors = validate_config(config)
        assert "listing_page.link is required" in errors

    def test_missing_detail_page_selectors(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {}
        }
        errors = validate_config(config)
        assert "detail_page.selectors is required" in errors

    def test_selectors_not_dict(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": ["h1", "h2"]}
        }
        errors = validate_config(config)
        assert "detail_page.selectors must be a dictionary" in errors

    def test_selector_not_list(self):
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {
                "selectors": {
                    "title": "h1.title"  # Should be a list
                }
            }
        }
        errors = validate_config(config)
        assert any("title" in err and "must be a list" in err for err in errors)

    def test_single_selector_warning_not_error(self, caplog):
        """Single selector should warn but not error."""
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {
                "selectors": {
                    "title": ["h1"]  # Only one selector - should warn
                }
            }
        }
        errors = validate_config(config)
        # Should not produce errors, only warning in logs
        assert errors == []

    def test_multiple_errors_returned(self):
        config = {
            "site": {},  # Missing name and domain
            "urls": {},  # Missing listing_pattern and id_pattern
            "listing_page": {},  # Missing container and link
            "detail_page": {}  # Missing selectors
        }
        errors = validate_config(config)
        assert len(errors) >= 6  # Multiple validation failures


class TestLoadConfig:
    """Tests for load_config function."""

    @pytest.fixture
    def valid_config_yaml(self, tmp_path):
        """Create a valid config YAML file."""
        config = {
            "site": {
                "name": "Test Site",
                "domain": "test.bg",
                "encoding": "utf-8"
            },
            "urls": {
                "listing_pattern": "/ads/real-estate/",
                "id_pattern": r"/ad/(\d+)"
            },
            "pagination": {
                "type": "numbered",
                "param": "page",
                "start": 1,
                "max_pages": 100
            },
            "listing_page": {
                "container": ".listing-card",
                "link": "a.card-link",
                "quick_fields": {
                    "preview_price": ".price-badge"
                }
            },
            "detail_page": {
                "selectors": {
                    "title": ["h1.title", "h1"],
                    "price": [".price-main", ".price"],
                    "area": [".area-value", ".features .area"]
                },
                "field_types": {
                    "price": "currency_bgn_eur",
                    "area": "number"
                }
            },
            "extraction": {
                "llm_fallback": True,
                "llm_model": "gpt-4",
                "clean_whitespace": True,
                "decode_html_entities": True
            },
            "timing": {
                "delay_seconds": 3.0,
                "max_per_domain": 3
            },
            "quirks": {
                "requires_js": True,
                "has_lazy_images": True,
                "encoding_fallback": "windows-1251"
            }
        }
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(yaml.dump(config, allow_unicode=True))
        return config_file

    @pytest.fixture
    def minimal_config_yaml(self, tmp_path):
        """Create a minimal valid config with only required fields."""
        config = {
            "site": {
                "name": "Minimal Site",
                "domain": "minimal.bg"
            },
            "urls": {
                "listing_pattern": "/listings/",
                "id_pattern": r"/listing/(\d+)"
            },
            "listing_page": {
                "container": ".card",
                "link": "a"
            },
            "detail_page": {
                "selectors": {
                    "title": ["h1", ".title"]
                }
            }
        }
        config_file = tmp_path / "minimal_config.yaml"
        config_file.write_text(yaml.dump(config))
        return config_file

    def test_load_valid_config_returns_dataclass(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result, GenericScraperConfig)

    def test_file_not_found_raises_error(self, tmp_path):
        missing_file = tmp_path / "missing.yaml"
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(missing_file)
        assert "Config file not found" in str(exc_info.value)

    def test_empty_file_raises_error(self, tmp_path):
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")
        with pytest.raises(ValueError) as exc_info:
            load_config(empty_file)
        assert "Config file is empty" in str(exc_info.value)

    def test_invalid_config_raises_error(self, tmp_path):
        invalid_file = tmp_path / "invalid.yaml"
        invalid_config = {"site": {"name": "Test"}}  # Missing required fields
        invalid_file.write_text(yaml.dump(invalid_config))

        with pytest.raises(ValueError) as exc_info:
            load_config(invalid_file)
        assert "Invalid config" in str(exc_info.value)

    def test_site_info_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.site, SiteInfo)
        assert result.site.name == "Test Site"
        assert result.site.domain == "test.bg"
        assert result.site.encoding == "utf-8"

    def test_url_patterns_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.urls, UrlPatterns)
        assert result.urls.listing_pattern == "/ads/real-estate/"
        assert result.urls.id_pattern == r"/ad/(\d+)"

    def test_pagination_config_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.pagination, PaginationConfig)
        assert result.pagination.type == "numbered"
        assert result.pagination.param == "page"
        assert result.pagination.start == 1
        assert result.pagination.max_pages == 100

    def test_listing_page_config_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.listing_page, ListingPageConfig)
        assert result.listing_page.container == ".listing-card"
        assert result.listing_page.link == "a.card-link"
        assert result.listing_page.quick_fields == {"preview_price": ".price-badge"}

    def test_detail_page_config_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.detail_page, DetailPageConfig)
        assert "title" in result.detail_page.selectors
        assert result.detail_page.selectors["title"] == ["h1.title", "h1"]
        assert result.detail_page.field_types["price"] == "currency_bgn_eur"

    def test_extraction_config_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.extraction, ExtractionConfig)
        assert result.extraction.llm_fallback is True
        assert result.extraction.llm_model == "gpt-4"
        assert result.extraction.clean_whitespace is True
        assert result.extraction.decode_html_entities is True

    def test_timing_config_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.timing, TimingConfig)
        assert result.timing.delay_seconds == 3.0
        assert result.timing.max_per_domain == 3

    def test_quirks_config_populated_correctly(self, valid_config_yaml):
        result = load_config(valid_config_yaml)
        assert isinstance(result.quirks, QuirksConfig)
        assert result.quirks.requires_js is True
        assert result.quirks.has_lazy_images is True
        assert result.quirks.encoding_fallback == "windows-1251"

    def test_default_values_used_when_optional_fields_missing(self, minimal_config_yaml):
        result = load_config(minimal_config_yaml)

        # Site encoding default
        assert result.site.encoding == "utf-8"

        # Pagination defaults
        assert result.pagination.type == "numbered"
        assert result.pagination.param == "page"
        assert result.pagination.start == 1
        assert result.pagination.max_pages == 50

        # Listing page defaults
        assert result.listing_page.quick_fields == {}

        # Detail page defaults
        assert result.detail_page.field_types == {}

        # Extraction defaults
        assert result.extraction.llm_fallback is False
        assert result.extraction.llm_model is None
        assert result.extraction.clean_whitespace is True
        assert result.extraction.decode_html_entities is True

        # Timing defaults
        assert result.timing.delay_seconds == 2.0
        assert result.timing.max_per_domain == 2

        # Quirks defaults
        assert result.quirks.requires_js is False
        assert result.quirks.has_lazy_images is False
        assert result.quirks.encoding_fallback == "windows-1251"

    def test_load_config_with_string_path(self, valid_config_yaml):
        """Test that load_config accepts string paths."""
        result = load_config(str(valid_config_yaml))
        assert isinstance(result, GenericScraperConfig)

    def test_load_config_with_path_object(self, valid_config_yaml):
        """Test that load_config accepts Path objects."""
        result = load_config(valid_config_yaml)
        assert isinstance(result, GenericScraperConfig)

    def test_malformed_yaml_raises_error(self, tmp_path):
        """Test that malformed YAML raises an appropriate error."""
        malformed_file = tmp_path / "malformed.yaml"
        malformed_file.write_text("site:\n  name: Test\n  invalid yaml: [unclosed bracket")

        with pytest.raises(yaml.YAMLError):
            load_config(malformed_file)

    def test_partial_optional_sections(self, tmp_path):
        """Test config with some optional fields specified."""
        config = {
            "site": {"name": "Test", "domain": "test.bg"},
            "urls": {"listing_pattern": "/ads/", "id_pattern": r"/ad/(\d+)"},
            "listing_page": {"container": ".card", "link": "a"},
            "detail_page": {"selectors": {"title": ["h1", ".title"]}},
            "timing": {"delay_seconds": 5.0}  # Only partial timing config
        }
        config_file = tmp_path / "partial.yaml"
        config_file.write_text(yaml.dump(config))

        result = load_config(config_file)
        assert result.timing.delay_seconds == 5.0
        assert result.timing.max_per_domain == 2  # Default value


class TestDataclassDefaults:
    """Test that dataclass default values are correctly defined."""

    def test_site_info_defaults(self):
        site = SiteInfo(name="Test", domain="test.bg")
        assert site.encoding == "utf-8"

    def test_pagination_config_defaults(self):
        pagination = PaginationConfig()
        assert pagination.type == "numbered"
        assert pagination.param == "page"
        assert pagination.start == 1
        assert pagination.next_selector is None
        assert pagination.load_more_selector is None
        assert pagination.max_pages == 50

    def test_listing_page_config_defaults(self):
        listing = ListingPageConfig(container=".card", link="a")
        assert listing.quick_fields == {}

    def test_detail_page_config_defaults(self):
        detail = DetailPageConfig(selectors={"title": ["h1"]})
        assert detail.field_types == {}

    def test_extraction_config_defaults(self):
        extraction = ExtractionConfig()
        assert extraction.llm_fallback is False
        assert extraction.llm_model is None
        assert extraction.clean_whitespace is True
        assert extraction.decode_html_entities is True

    def test_timing_config_defaults(self):
        timing = TimingConfig()
        assert timing.delay_seconds == 2.0
        assert timing.max_per_domain == 2

    def test_quirks_config_defaults(self):
        quirks = QuirksConfig()
        assert quirks.requires_js is False
        assert quirks.has_lazy_images is False
        assert quirks.encoding_fallback == "windows-1251"


class TestIntegration:
    """Integration tests with realistic config scenarios."""

    def test_real_estate_site_config(self, tmp_path):
        """Test a realistic real estate site configuration."""
        config = {
            "site": {
                "name": "Imot.bg",
                "domain": "www.imot.bg",
                "encoding": "windows-1251"
            },
            "urls": {
                "listing_pattern": r"/pcgi/imot\.cgi",
                "id_pattern": r"adv=(\d+)"
            },
            "pagination": {
                "type": "numbered",
                "param": "f1",
                "start": 1,
                "max_pages": 200
            },
            "listing_page": {
                "container": "table.tableResults a",
                "link": "a",
                "quick_fields": {
                    "title": "b",
                    "price": "span.price"
                }
            },
            "detail_page": {
                "selectors": {
                    "title": ["h1", ".ad-title"],
                    "price": [".price", ".price-box .value"],
                    "area": [".area", ".size"],
                    "floor": [".floor-info", ".etaj"],
                    "description": [".description", ".ad-text"],
                    "images": [".gallery img", ".photos img"]
                },
                "field_types": {
                    "price": "currency_bgn_eur",
                    "area": "number",
                    "floor": "floor_pattern"
                }
            },
            "extraction": {
                "llm_fallback": False,
                "clean_whitespace": True,
                "decode_html_entities": True
            },
            "timing": {
                "delay_seconds": 2.5,
                "max_per_domain": 2
            },
            "quirks": {
                "requires_js": False,
                "has_lazy_images": True,
                "encoding_fallback": "windows-1251"
            }
        }

        config_file = tmp_path / "imot_bg.yaml"
        config_file.write_text(yaml.dump(config, allow_unicode=True))

        result = load_config(config_file)

        assert result.site.name == "Imot.bg"
        assert result.site.encoding == "windows-1251"
        assert result.pagination.max_pages == 200
        assert "title" in result.listing_page.quick_fields
        assert len(result.detail_page.selectors["title"]) == 2
        assert result.timing.delay_seconds == 2.5
        assert result.quirks.has_lazy_images is True
