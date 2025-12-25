"""
Base scraper class for all site-specific scrapers.

All site scrapers should inherit from BaseSiteScraper and implement:
- extract_listing(): Extract data from a single listing page
- extract_search_results(): Extract listing URLs from search results
- build_search_url(): Build search URL with filters
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ListingData:
    """
    Standardized listing data structure across all sites.

    All scrapers should return this dataclass to ensure consistent data format.
    """

    # Required fields
    external_id: str  # Site's listing ID
    url: str  # Full listing URL
    source_site: str  # e.g., "imot.bg"

    # Basic info
    title: Optional[str] = None
    description: Optional[str] = None

    # Price (EUR only - Bulgaria switching to EUR in 2025)
    price_eur: Optional[float] = None
    price_per_sqm_eur: Optional[float] = None

    # Size
    sqm_total: Optional[float] = None  # Total area including shared spaces
    sqm_net: Optional[float] = None  # Net usable area

    # Layout
    rooms_count: Optional[int] = None
    bathrooms_count: Optional[int] = None

    # Floor
    floor_number: Optional[int] = None
    floor_total: Optional[int] = None  # Total floors in building
    has_elevator: Optional[bool] = None

    # Building
    building_type: Optional[str] = None  # brick/panel/new_construction
    construction_year: Optional[int] = None
    act_status: Optional[str] = None  # act14/act15/act16/old_building

    # Location
    district: Optional[str] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    metro_station: Optional[str] = None
    metro_distance_m: Optional[int] = None

    # Features
    orientation: Optional[str] = None  # E/S/W/N combinations
    has_balcony: Optional[bool] = None
    has_garden: Optional[bool] = None
    has_parking: Optional[bool] = None
    has_storage: Optional[bool] = None
    heating_type: Optional[str] = None
    condition: Optional[str] = None  # ready/renovation/bare_walls

    # Media
    image_urls: List[str] = field(default_factory=list)
    main_image_url: Optional[str] = None

    # Contact
    agency: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None

    # Metadata
    listing_date: Optional[datetime] = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    features: List[str] = field(default_factory=list)  # Raw features list

    # For deduplication
    fingerprint: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BaseSiteScraper(ABC):
    """
    Abstract base class for all site-specific scrapers.

    Subclasses must implement:
    - extract_listing(): Parse a single listing page
    - extract_search_results(): Get listing URLs from search page
    - build_search_url(): Construct search URL with filters
    """

    def __init__(self):
        self.site_name: str = ""
        self.base_url: str = ""

    @abstractmethod
    async def extract_listing(self, html: str, url: str) -> Optional[ListingData]:
        """
        Extract all listing data from a single property page.

        Args:
            html: Page HTML content
            url: Page URL

        Returns:
            ListingData object or None if extraction failed
        """
        pass

    @abstractmethod
    async def extract_search_results(self, html: str) -> List[str]:
        """
        Extract listing URLs from a search results page.

        Args:
            html: Search results page HTML

        Returns:
            List of listing URLs
        """
        pass

    # --- Helper methods for parsing ---

    def _parse_price(self, text: str) -> Optional[float]:
        """
        Parse price string to EUR value.
        Bulgaria is switching to EUR in 2025, so we only handle EUR.

        Args:
            text: Price text (e.g., "150 000 EUR" or "150000€")

        Returns:
            Price in EUR or None
        """
        import re

        if not text:
            return None

        # Remove spaces and non-breaking spaces
        text = text.replace(" ", "").replace("\xa0", "")

        # Match EUR amounts
        eur_match = re.search(r"([\d,]+)(?:EUR|€)", text, re.IGNORECASE)
        if eur_match:
            return float(eur_match.group(1).replace(",", ""))

        # Try to extract just a number (fallback)
        num_match = re.search(r"([\d,]+)", text)
        if num_match:
            return float(num_match.group(1).replace(",", ""))

        return None

    def _parse_sqm(self, text: str) -> Optional[float]:
        """
        Parse square meters from various formats.

        Args:
            text: Size text (e.g., "115 кв.м" or "115 m²")

        Returns:
            Square meters as float or None
        """
        import re

        if not text:
            return None

        match = re.search(r"([\d.,]+)\s*(?:кв\.?\s*м|m²|sqm)", text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", "."))

        # Try just number
        match = re.search(r"([\d.,]+)", text)
        if match:
            return float(match.group(1).replace(",", "."))

        return None

    def _parse_floor(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """
        Parse floor string to floor number and total floors.

        Args:
            text: Floor text (e.g., "3 от 6" or "3/6")

        Returns:
            Tuple of (floor_number, floor_total)
        """
        import re

        if not text:
            return None, None

        match = re.search(r"(\d+)\s*(?:от|/|из)\s*(\d+)", text)
        if match:
            return int(match.group(1)), int(match.group(2))

        # Just floor number
        match = re.search(r"(\d+)", text)
        if match:
            return int(match.group(1)), None

        return None, None

    def _parse_rooms(self, text: str) -> Optional[int]:
        """
        Parse room count from Bulgarian text.

        Args:
            text: Room text (e.g., "тристаен" or "3-стаен")

        Returns:
            Number of rooms or None
        """
        import re

        if not text:
            return None

        text_lower = text.lower()

        # Bulgarian word mappings
        mappings = {
            "едностаен": 1,
            "двустаен": 2,
            "тристаен": 3,
            "четиристаен": 4,
            "многостаен": 5,
            "мезонет": 3,  # Assume 3+ for maisonette
        }

        for word, count in mappings.items():
            if word in text_lower:
                return count

        # Try numeric pattern: "3-стаен" or "3 стаен"
        match = re.search(r"(\d+)\s*[-]?\s*ста", text_lower)
        if match:
            return int(match.group(1))

        return None

    def _parse_building_type(self, text: str) -> Optional[str]:
        """
        Parse building type from Bulgarian text.

        Args:
            text: Building text (e.g., "панел" or "тухла")

        Returns:
            Normalized building type: brick/panel/new_construction or None
        """
        if not text:
            return None

        text_lower = text.lower()

        if any(w in text_lower for w in ["панел", "епк", "пк"]):
            return "panel"
        elif any(w in text_lower for w in ["тухла", "гредоред"]):
            return "brick"
        elif any(w in text_lower for w in ["ново строителство", "ново"]):
            return "new_construction"

        return None
