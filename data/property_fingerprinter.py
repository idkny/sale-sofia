"""
Property fingerprinting for cross-site duplicate detection.

Generates consistent fingerprints from property characteristics (neighborhood, sqm,
rooms, floor, building type) to identify when the same property appears on multiple
listing sites (imot.bg, bazar.bg).

Part of Spec 106B: Cross-Site Duplicate Detection & Merging.
"""

import hashlib
import re
from typing import List, Union

from data.data_store_main import get_sources_by_fingerprint
from websites.base_scraper import ListingData

# sqlite3.Row type for return annotations
try:
    from sqlite3 import Row
except ImportError:
    Row = object


class PropertyFingerprinter:
    """Generate fingerprints for cross-site property matching."""

    # Common neighborhood prefixes to remove during normalization
    NEIGHBORHOOD_PREFIXES = [
        "кв.",
        "кв ",
        "ж.к.",
        "ж.к ",
        "жк.",
        "жк ",
        "ул.",
        "ул ",
        "бул.",
        "бул ",
        "с.",
        "с ",
        "м.",
        "м ",
    ]

    def compute(self, listing: Union[ListingData, dict]) -> str:
        """
        Generate fingerprint from listing data.

        Args:
            listing: ListingData object or dict with listing fields

        Returns:
            16-character hex fingerprint
        """
        # Extract fields, handling both ListingData objects and dicts
        neighborhood = self._get_field(listing, "neighborhood")
        sqm_total = self._get_field(listing, "sqm_total")
        rooms_count = self._get_field(listing, "rooms_count")
        floor_number = self._get_field(listing, "floor_number")
        building_type = self._get_field(listing, "building_type")

        # Build fingerprint components
        components = [
            self.normalize_neighborhood(neighborhood) if neighborhood else "",
            str(round(sqm_total)) if sqm_total else "",
            str(rooms_count) if rooms_count else "",
            str(floor_number) if floor_number else "",
            self._normalize_text(building_type) if building_type else "",
        ]

        # Join with delimiter and hash
        fingerprint_input = "|".join(components)
        hash_hex = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()

        return hash_hex[:16]

    def normalize_neighborhood(self, name: str) -> str:
        """
        Normalize neighborhood names across sites.

        - Lowercase
        - Strip whitespace
        - Remove common prefixes like "kv.", "zh.k."

        Args:
            name: Raw neighborhood name

        Returns:
            Normalized name
        """
        if not name:
            return ""

        # Lowercase and strip
        normalized = name.lower().strip()

        # Remove common prefixes
        for prefix in self.NEIGHBORHOOD_PREFIXES:
            if normalized.startswith(prefix.lower()):
                normalized = normalized[len(prefix) :].strip()
                break

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized

    def find_matches(self, fingerprint: str) -> List[Row]:
        """
        Find existing listings with same fingerprint.

        Args:
            fingerprint: Property fingerprint

        Returns:
            List of matching rows from listing_sources table
        """
        return get_sources_by_fingerprint(fingerprint)

    def _get_field(self, listing: Union[ListingData, dict], field: str):
        """
        Get field value from either ListingData or dict.

        Args:
            listing: ListingData object or dict
            field: Field name

        Returns:
            Field value or None
        """
        if isinstance(listing, dict):
            return listing.get(field)
        return getattr(listing, field, None)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent hashing.

        - Lowercase
        - Strip whitespace
        - Collapse multiple spaces

        Args:
            text: Raw text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        normalized = text.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized
