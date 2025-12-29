"""
Generic config-driven scraper framework.

This module provides a configuration-driven approach to building scrapers,
allowing new sites to be added via YAML config files instead of custom code.

Components:
    - ConfigScraper: Generic scraper that uses YAML configs for extraction
    - config_loader: Load and validate site YAML configurations
    - selector_chain: Fallback extraction engine with multiple selector types

Usage:
    from websites.generic import ConfigScraper, load_config

    config = load_config("sites/example.yaml")
    scraper = ConfigScraper(config)
    listing = await scraper.extract_listing(html, url)
"""

# Imports
from .config_scraper import ConfigScraper
from .config_loader import load_config, validate_config
from .selector_chain import extract_field

__all__ = [
    "ConfigScraper",
    "load_config",
    "validate_config",
    "extract_field",
]
