"""
Generic config-driven scraper that uses YAML configuration for extraction.

This scraper allows new sites to be added with just a YAML config file,
without writing any Python code for field extraction.

Usage:
    from websites.generic.config_scraper import ConfigScraper

    scraper = ConfigScraper("config/sites/olx_bg.yaml")
    listing = scraper.extract_listing(html, url)
    urls = scraper.extract_search_results(search_html)
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

from loguru import logger

from websites.base_scraper import BaseSiteScraper, ListingData
from websites.generic.config_loader import GenericScraperConfig, load_config
from websites.generic.selector_chain import extract_field
from websites.scrapling_base import ScraplingMixin


class ConfigScraper(ScraplingMixin, BaseSiteScraper):
    """
    Generic scraper that uses YAML configuration instead of hardcoded selectors.

    Attributes:
        config: Loaded GenericScraperConfig from YAML
        site_name: Site identifier (e.g., "olx.bg")
        base_url: Base URL for the site (e.g., "https://www.olx.bg")
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Initialize the scraper with a YAML config file.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        # Load config first to get site_name for ScraplingMixin
        self.config: GenericScraperConfig = load_config(config_path)

        # Set site info before calling super().__init__
        self.site_name = self.config.site.name
        self.base_url = f"https://{self.config.site.domain}"

        # Initialize both parent classes
        super().__init__()

        logger.debug(f"Initialized ConfigScraper for {self.site_name}")

    def extract_listing(self, html: str, url: str) -> Optional[ListingData]:
        """
        Extract listing data from a detail page using config-defined selectors.

        Args:
            html: Raw HTML content of the listing page
            url: Full URL of the listing page

        Returns:
            ListingData object or None if extraction failed
        """
        # Parse HTML
        page = self.parse(html, url)

        # Extract external ID from URL
        external_id = self._extract_id(url)
        if not external_id:
            logger.warning(f"Could not extract ID from URL: {url}")
            return None

        # Extract fields using config selectors
        extracted = {}
        selectors = self.config.detail_page.selectors
        field_types = self.config.detail_page.field_types

        for field_name, selector_chain in selectors.items():
            field_type = field_types.get(field_name, "text")
            value = extract_field(page, selector_chain, field_type)
            if value is not None:
                extracted[field_name] = value

        logger.debug(f"Extracted {len(extracted)} fields for {external_id}")

        # Parse floor if present
        floor_number, floor_total = None, None
        if "floor" in extracted:
            floor_number, floor_total = self._parse_floor_string(str(extracted["floor"]))

        # Build ListingData
        listing = ListingData(
            external_id=external_id,
            url=url,
            source_site=self.site_name,
            title=extracted.get("title"),
            description=extracted.get("description"),
            price_eur=extracted.get("price"),
            sqm_total=extracted.get("sqm"),
            rooms_count=self._to_int(extracted.get("rooms")),
            floor_number=floor_number,
            floor_total=floor_total,
            building_type=extracted.get("building_type"),
            district=extracted.get("district"),
            neighborhood=extracted.get("neighborhood"),
            address=extracted.get("address"),
            image_urls=extracted.get("images", []),
            agency=extracted.get("agency"),
            agent_phone=extracted.get("phone"),
            features=extracted.get("features", []),
        )

        logger.debug(f"Created ListingData for {external_id}")
        return listing

    def extract_search_results(self, html: str) -> List[str]:
        """
        Extract listing URLs from a search results page.

        Args:
            html: Raw HTML content of the search results page

        Returns:
            List of listing URLs
        """
        page = self.parse(html)
        urls = []

        container_selector = self.config.listing_page.container
        link_selector = self.config.listing_page.link
        listing_pattern = self.config.urls.listing_pattern

        # Find all listing cards
        cards = page.css(container_selector)
        logger.debug(f"Found {len(cards)} listing cards with selector: {container_selector}")

        for card in cards:
            # Find link within card
            link = card.css_first(link_selector)
            if not link:
                continue

            href = self.get_attr(link, "href")
            if not href:
                continue

            # Normalize URL
            full_url = self._normalize_url(href)

            # Filter by listing pattern
            if listing_pattern and not re.search(listing_pattern, full_url):
                continue

            if full_url not in urls:
                urls.append(full_url)

        logger.debug(f"Extracted {len(urls)} listing URLs from search results")
        return urls

    def _extract_id(self, url: str) -> Optional[str]:
        """
        Extract listing ID from URL using config pattern.

        Args:
            url: Full listing URL

        Returns:
            Extracted ID or None if pattern doesn't match
        """
        pattern = self.config.urls.id_pattern
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    def _normalize_url(self, href: str) -> str:
        """
        Convert relative URL to absolute.

        Args:
            href: Possibly relative URL

        Returns:
            Absolute URL
        """
        if href.startswith("http://") or href.startswith("https://"):
            return href
        elif href.startswith("//"):
            return f"https:{href}"
        elif href.startswith("/"):
            return f"{self.base_url}{href}"
        else:
            return f"{self.base_url}/{href}"

    def _parse_floor_string(self, floor_str: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Parse floor string to (floor_number, floor_total).

        Handles formats: "3/6", "3", "0" (ground), "-1" (basement)

        Args:
            floor_str: Floor string from selector_chain

        Returns:
            Tuple of (floor_number, floor_total)
        """
        if not floor_str:
            return None, None

        # Handle "X/Y" format
        if "/" in floor_str:
            parts = floor_str.split("/")
            try:
                floor_num = int(parts[0])
                floor_total = int(parts[1]) if len(parts) > 1 else None
                return floor_num, floor_total
            except ValueError:
                pass

        # Handle single number
        try:
            return int(floor_str), None
        except ValueError:
            return None, None

    @staticmethod
    def _to_int(value) -> Optional[int]:
        """
        Convert value to int safely.

        Args:
            value: Value to convert (int, float, or None)

        Returns:
            Integer value or None
        """
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
