"""
Scraping configuration loader with merge logic.

Usage:
    from config.scraping_config import load_scraping_config

    config = load_scraping_config("imot.bg")
    print(config.timing.delay_seconds)  # 1.5 (site override)
    print(config.retry.max_attempts)    # 3 (from defaults)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class ConcurrencyConfig:
    max_global: int = 16
    max_per_domain: int = 2


@dataclass
class TimingConfig:
    delay_seconds: float = 2.0
    randomize_delay: bool = True
    random_delay_min: float = 0.5
    random_delay_max: float = 1.5


@dataclass
class TimeoutConfig:
    request_seconds: int = 60
    page_load_seconds: int = 30
    navigation_seconds: int = 30


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 300.0
    backoff_multiplier: float = 2.0
    http_codes: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504, 522, 524]
    )


@dataclass
class FetcherConfig:
    search_pages: str = "http"    # http | browser | stealth
    listing_pages: str = "http"


@dataclass
class AntiDetectionConfig:
    rotate_user_agent: bool = True
    block_webrtc: bool = False
    humanize_actions: bool = False


@dataclass
class BehaviorConfig:
    respect_robots_txt: bool = True
    follow_crawl_delay: bool = True
    cookies_enabled: bool = True


@dataclass
class ScrapingConfig:
    """Complete scraping configuration for a site."""
    site: str
    concurrency: ConcurrencyConfig = field(default_factory=ConcurrencyConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    fetcher: FetcherConfig = field(default_factory=FetcherConfig)
    anti_detection: AntiDetectionConfig = field(default_factory=AntiDetectionConfig)
    behavior: BehaviorConfig = field(default_factory=BehaviorConfig)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _normalize_site_name(site: str) -> str:
    """Convert site name to filename format: imot.bg -> imot_bg"""
    return site.replace(".", "_").replace("-", "_")


def load_scraping_config(site: str) -> ScrapingConfig:
    """
    Load scraping configuration with merge logic.

    Merge order: defaults <- site overrides

    Args:
        site: Site name (e.g., "imot.bg")

    Returns:
        ScrapingConfig with merged settings
    """
    config_dir = Path(__file__).parent

    # Load defaults
    defaults_path = config_dir / "scraping_defaults.yaml"
    if defaults_path.exists():
        with open(defaults_path, "r") as f:
            defaults = yaml.safe_load(f) or {}
    else:
        defaults = {}

    # Load site overrides
    site_filename = _normalize_site_name(site) + ".yaml"
    site_path = config_dir / "sites" / site_filename
    if site_path.exists():
        with open(site_path, "r") as f:
            site_config = yaml.safe_load(f) or {}
    else:
        site_config = {}

    # Merge: defaults <- site
    merged = _deep_merge(defaults, site_config)

    # Build dataclass
    return ScrapingConfig(
        site=site,
        concurrency=ConcurrencyConfig(**merged.get("concurrency", {})),
        timing=TimingConfig(**merged.get("timing", {})),
        timeouts=TimeoutConfig(**merged.get("timeouts", {})),
        retry=RetryConfig(**merged.get("retry", {})),
        fetcher=FetcherConfig(**merged.get("fetcher", {})),
        anti_detection=AntiDetectionConfig(**merged.get("anti_detection", {})),
        behavior=BehaviorConfig(**merged.get("behavior", {})),
    )
