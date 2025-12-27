"""
Config loader for start URLs and scraping configuration.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union

import yaml
from loguru import logger

from config.settings import DEFAULT_SCRAPE_DELAY


@dataclass
class SiteConfig:
    """Per-site scraping configuration."""
    limit: int = 100                    # Max listings per start URL
    delay: float = DEFAULT_SCRAPE_DELAY # Seconds between requests
    timeout: int = 30                   # Page load timeout


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
    Load per-site configuration from config/start_urls.yaml.

    Args:
        site: Site name (e.g., "imot.bg")

    Returns:
        SiteConfig with site-specific settings, or defaults if not configured.
    """
    config_path = Path(__file__).parent / "start_urls.yaml"

    if not config_path.exists():
        logger.warning(f"Start URLs config not found: {config_path}, using defaults")
        return SiteConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config or site not in config:
        logger.warning(f"No config found for {site}, using defaults")
        return SiteConfig()

    site_data = config[site]

    # New format: dict with 'config' key
    if isinstance(site_data, dict) and "config" in site_data:
        cfg = site_data["config"]
        return SiteConfig(
            limit=cfg.get("limit", 100),
            delay=cfg.get("delay", 6.0),
            timeout=cfg.get("timeout", 30),
        )

    # Old format or no config section: use defaults
    logger.info(f"Using default config for {site}")
    return SiteConfig()


def get_implemented_sites() -> List[str]:
    """
    Get list of sites that have start URLs configured.

    Returns:
        List of site names with configured URLs.
    """
    return list(get_start_urls().keys())
