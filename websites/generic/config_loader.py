"""
Configuration loader for generic config-driven scrapers.

Usage:
    from websites.generic.config_loader import load_config, validate_config

    config = load_config("config/sites/olx_bg.yaml")
    print(config.site.name)  # "OLX.bg"
    print(config.pagination.type)  # "numbered"
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from loguru import logger


@dataclass
class SiteInfo:
    """Basic site identification."""

    name: str
    domain: str
    encoding: str = "utf-8"


@dataclass
class UrlPatterns:
    """URL matching patterns for the site."""

    listing_pattern: str  # Regex to identify listing URLs
    id_pattern: str  # Regex to extract listing ID


@dataclass
class PaginationConfig:
    """Pagination behavior configuration."""

    type: str = "numbered"  # numbered, next_link, load_more, infinite_scroll
    param: str = "page"
    start: int = 1
    next_selector: Optional[str] = None
    load_more_selector: Optional[str] = None
    max_pages: int = 50


@dataclass
class ListingPageConfig:
    """Configuration for listing/search result pages."""

    container: str  # CSS selector for listing cards
    link: str  # CSS selector for link to detail page
    quick_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class DetailPageConfig:
    """Configuration for detail/listing pages."""

    selectors: Dict[str, List[str]]  # field -> [selector fallback chain]
    field_types: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractionConfig:
    """Extraction behavior settings."""

    llm_fallback: bool = False
    llm_model: Optional[str] = None
    clean_whitespace: bool = True
    decode_html_entities: bool = True


@dataclass
class TimingConfig:
    """Request timing and rate limiting."""

    delay_seconds: float = 2.0
    max_per_domain: int = 2


@dataclass
class QuirksConfig:
    """Site-specific quirks and workarounds."""

    requires_js: bool = False
    has_lazy_images: bool = False
    encoding_fallback: str = "windows-1251"


@dataclass
class GenericScraperConfig:
    """Complete configuration for a generic scraper."""

    site: SiteInfo
    urls: UrlPatterns
    pagination: PaginationConfig
    listing_page: ListingPageConfig
    detail_page: DetailPageConfig
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    quirks: QuirksConfig = field(default_factory=QuirksConfig)


def _normalize_site_name(site: str) -> str:
    """Convert site name to filename format: olx.bg -> olx_bg"""
    return site.replace(".", "_").replace("-", "_")


def get_config_path(site_name: str) -> Path:
    """
    Convert site name to config path.

    Args:
        site_name: Domain-style name (e.g., "olx.bg")

    Returns:
        Path to config file (e.g., config/sites/olx_bg.yaml)
    """
    config_dir = Path(__file__).parent.parent.parent / "config" / "sites"
    filename = _normalize_site_name(site_name) + ".yaml"
    return config_dir / filename


def validate_config(config: dict) -> List[str]:
    """
    Validate raw config dict before parsing.

    Args:
        config: Raw config dictionary from YAML

    Returns:
        List of error messages (empty if valid).

    Checks:
        - Required sections: site, urls, listing_page, detail_page
        - site must have name and domain
        - detail_page.selectors must exist and each field must be a list
        - Each selector list should have at least 2 fallbacks (warning, not error)
    """
    errors: List[str] = []

    # Check required top-level sections
    required_sections = ["site", "urls", "listing_page", "detail_page"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")

    # Stop early if structure is invalid
    if errors:
        return errors

    # Validate site section
    site = config.get("site", {})
    if not site.get("name"):
        errors.append("site.name is required")
    if not site.get("domain"):
        errors.append("site.domain is required")

    # Validate urls section
    urls = config.get("urls", {})
    if not urls.get("listing_pattern"):
        errors.append("urls.listing_pattern is required")
    if not urls.get("id_pattern"):
        errors.append("urls.id_pattern is required")

    # Validate listing_page section
    listing_page = config.get("listing_page", {})
    if not listing_page.get("container"):
        errors.append("listing_page.container is required")
    if not listing_page.get("link"):
        errors.append("listing_page.link is required")

    # Validate detail_page section
    detail_page = config.get("detail_page", {})
    selectors = detail_page.get("selectors")

    if not selectors:
        errors.append("detail_page.selectors is required")
    elif not isinstance(selectors, dict):
        errors.append("detail_page.selectors must be a dictionary")
    else:
        for field_name, selector_list in selectors.items():
            if not isinstance(selector_list, list):
                errors.append(
                    f"detail_page.selectors.{field_name} must be a list of fallback selectors"
                )
            elif len(selector_list) < 2:
                # Warning, not error
                logger.warning(
                    f"detail_page.selectors.{field_name} has only {len(selector_list)} "
                    f"selector(s); recommend at least 2 fallbacks for robustness"
                )

    return errors


def load_config(config_path: Union[str, Path]) -> GenericScraperConfig:
    """
    Load YAML config and return structured dataclass.

    Args:
        config_path: Path to YAML config file

    Returns:
        GenericScraperConfig dataclass with all settings

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    logger.debug(f"Loading config from {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    if not raw_config:
        raise ValueError(f"Config file is empty: {path}")

    # Validate before parsing
    errors = validate_config(raw_config)
    if errors:
        error_msg = f"Invalid config {path}:\n  - " + "\n  - ".join(errors)
        raise ValueError(error_msg)

    # Build dataclass from validated config
    site = SiteInfo(
        name=raw_config["site"]["name"],
        domain=raw_config["site"]["domain"],
        encoding=raw_config["site"].get("encoding", "utf-8"),
    )

    urls = UrlPatterns(
        listing_pattern=raw_config["urls"]["listing_pattern"],
        id_pattern=raw_config["urls"]["id_pattern"],
    )

    # Pagination (optional with defaults)
    pagination_data = raw_config.get("pagination", {})
    pagination = PaginationConfig(
        type=pagination_data.get("type", "numbered"),
        param=pagination_data.get("param", "page"),
        start=pagination_data.get("start", 1),
        next_selector=pagination_data.get("next_selector"),
        load_more_selector=pagination_data.get("load_more_selector"),
        max_pages=pagination_data.get("max_pages", 50),
    )

    # Listing page
    listing_page_data = raw_config["listing_page"]
    listing_page = ListingPageConfig(
        container=listing_page_data["container"],
        link=listing_page_data["link"],
        quick_fields=listing_page_data.get("quick_fields", {}),
    )

    # Detail page
    detail_page_data = raw_config["detail_page"]
    detail_page = DetailPageConfig(
        selectors=detail_page_data["selectors"],
        field_types=detail_page_data.get("field_types", {}),
    )

    # Extraction (optional with defaults)
    extraction_data = raw_config.get("extraction", {})
    extraction = ExtractionConfig(
        llm_fallback=extraction_data.get("llm_fallback", False),
        llm_model=extraction_data.get("llm_model"),
        clean_whitespace=extraction_data.get("clean_whitespace", True),
        decode_html_entities=extraction_data.get("decode_html_entities", True),
    )

    # Timing (optional with defaults)
    timing_data = raw_config.get("timing", {})
    timing = TimingConfig(
        delay_seconds=timing_data.get("delay_seconds", 2.0),
        max_per_domain=timing_data.get("max_per_domain", 2),
    )

    # Quirks (optional with defaults)
    quirks_data = raw_config.get("quirks", {})
    quirks = QuirksConfig(
        requires_js=quirks_data.get("requires_js", False),
        has_lazy_images=quirks_data.get("has_lazy_images", False),
        encoding_fallback=quirks_data.get("encoding_fallback", "windows-1251"),
    )

    logger.info(f"Loaded config for {site.name} ({site.domain})")

    return GenericScraperConfig(
        site=site,
        urls=urls,
        pagination=pagination,
        listing_page=listing_page,
        detail_page=detail_page,
        extraction=extraction,
        timing=timing,
        quirks=quirks,
    )
