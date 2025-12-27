"""
Config loader for start URLs and crawl limits.

Scraping behavior settings (delay, timeout, etc.) are in:
- config/scraping_defaults.yaml (global defaults)
- config/sites/<site>.yaml (per-site overrides)

Use load_scraping_config() from config.scraping_config for those.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml
from loguru import logger


@dataclass
class SiteConfig:
    """Per-crawl configuration (from start_urls.yaml)."""
    limit: int = 100  # Max listings per start URL


def get_start_urls() -> Dict[str, List[str]]:
    """
    Load start URLs from config/start_urls.yaml.

    Supports both old format (list of URLs) and new format (dict with config + urls).
    Backward compatible with existing configs.

    Returns:
        Dictionary mapping site names to lists of start URLs.
        Example: {"imot.bg": ["https://...", "https://..."]}
    """
    config_path = Path(__file__).parent / "start_urls.yaml"

    if not config_path.exists():
        logger.error(f"Start URLs config not found: {config_path}")
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        logger.warning("Start URLs config is empty")
        return {}

    # Filter out commented sites (None values) and handle both formats
    result = {}
    for site, data in config.items():
        if not data:  # Skip None/empty
            continue

        # New format: dict with 'config' and 'urls' keys
        if isinstance(data, dict) and "urls" in data:
            urls = data["urls"]
            if urls:
                result[site] = urls
                logger.info(f"Loaded {len(urls)} start URLs for {site}")
        # Old format: direct list of URLs
        elif isinstance(data, list):
            result[site] = data
            logger.info(f"Loaded {len(data)} start URLs for {site}")

    return result


def get_site_config(site: str) -> SiteConfig:
    """
    Load per-crawl limit from config/start_urls.yaml.

    For scraping behavior (delay, timeout), use load_scraping_config() instead.

    Args:
        site: Site name (e.g., "imot.bg")

    Returns:
        SiteConfig with limit setting.
    """
    config_path = Path(__file__).parent / "start_urls.yaml"

    if not config_path.exists():
        return SiteConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config or site not in config:
        return SiteConfig()

    site_data = config[site]

    # Format: dict with 'config' key containing 'limit'
    if isinstance(site_data, dict) and "config" in site_data:
        cfg = site_data["config"]
        return SiteConfig(limit=cfg.get("limit", 100))

    return SiteConfig()


def get_implemented_sites() -> List[str]:
    """
    Get list of sites that have start URLs configured.

    Returns:
        List of site names with configured URLs.
    """
    return list(get_start_urls().keys())
