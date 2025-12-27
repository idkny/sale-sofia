# data/property_merger.py
"""
Merge data from multiple listing sources for cross-site deduplication.
"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class PropertyMerger:
    """Merge data from multiple listing sources."""

    # Field weights for data quality scoring
    QUALITY_WEIGHTS = {
        "price_eur": 0.2,
        "sqm_total": 0.15,
        "rooms_count": 0.1,
        "floor_number": 0.1,
        "neighborhood": 0.1,
        "description": 0.1,
        "has_elevator": 0.05,
        "building_type": 0.05,
        "image_urls": 0.1,
    }
    # Remaining weight for other fields
    OTHER_FIELDS_WEIGHT = 0.05

    # Fields by type for merge strategy
    NUMERIC_FIELDS = {
        "price_eur",
        "price_per_sqm_eur",
        "sqm_total",
        "sqm_net",
        "rooms_count",
        "bathrooms_count",
        "floor_number",
        "floor_total",
        "construction_year",
        "metro_distance_m",
    }

    BOOLEAN_FIELDS = {
        "has_elevator",
        "has_balcony",
        "has_garden",
        "has_parking",
        "has_storage",
        "is_active",
    }

    TEXT_FIELDS = {
        "title",
        "description",
        "building_type",
        "act_status",
        "district",
        "neighborhood",
        "address",
        "metro_station",
        "orientation",
        "heating_type",
        "condition",
        "main_image_url",
        "image_urls",
        "agency",
        "agent_phone",
    }

    # Fields to exclude from merging (identifiers, metadata)
    EXCLUDE_FIELDS = {
        "id",
        "external_id",
        "url",
        "source_site",
        "scraped_at",
        "updated_at",
        "listing_date",
    }

    def _to_dict(self, row: Any) -> dict:
        """Convert sqlite3.Row or dict to dict."""
        if isinstance(row, sqlite3.Row):
            return dict(row)
        if isinstance(row, dict):
            return row
        # Try dict() conversion for other Row-like objects
        return dict(row)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _get_recency(self, listing: dict) -> datetime:
        """Get the most recent timestamp from a listing."""
        updated = self._parse_datetime(listing.get("updated_at"))
        scraped = self._parse_datetime(listing.get("scraped_at"))

        if updated and scraped:
            return max(updated, scraped)
        return updated or scraped or datetime.min

    def _is_non_null(self, value: Any) -> bool:
        """Check if value is non-null/non-empty."""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True

    def merge(self, listings: List[dict]) -> Dict[str, Any]:
        """
        Merge multiple listings into best-available data.

        Strategy:
        - For each field, pick non-null value
        - If multiple non-null values:
          - Numeric: use most recent (by scraped_at/updated_at)
          - Text: use longest (more detail)
          - Boolean: use True if any True (optimistic)
        - Track which source provided each field

        Args:
            listings: List of listing dicts (from sqlite3.Row or ListingData.to_dict())

        Returns:
            Dict with merged data + "_sources" field tracking field origins
        """
        if not listings:
            return {"_sources": {}}

        # Convert all to dicts
        listings_dicts = [self._to_dict(lst) for lst in listings]

        if len(listings_dicts) == 1:
            result = listings_dicts[0].copy()
            source = result.get("source_site", "unknown")
            result["_sources"] = {
                k: source for k in result.keys() if k not in self.EXCLUDE_FIELDS
            }
            return result

        # Sort by recency for numeric field preference
        listings_by_recency = sorted(
            listings_dicts, key=lambda x: self._get_recency(x), reverse=True
        )

        # Collect all fields
        all_fields = set()
        for lst in listings_dicts:
            all_fields.update(lst.keys())

        # Remove excluded fields from merging
        merge_fields = all_fields - self.EXCLUDE_FIELDS

        result: Dict[str, Any] = {}
        sources: Dict[str, str] = {}

        for field in merge_fields:
            # Collect non-null values with their sources
            values_with_sources = []
            for lst in listings_dicts:
                val = lst.get(field)
                if self._is_non_null(val):
                    values_with_sources.append((val, lst.get("source_site", "unknown")))

            if not values_with_sources:
                result[field] = None
                continue

            if len(values_with_sources) == 1:
                result[field] = values_with_sources[0][0]
                sources[field] = values_with_sources[0][1]
                continue

            # Multiple non-null values - apply merge strategy
            if field in self.NUMERIC_FIELDS:
                # Use most recent (first in recency-sorted list)
                for lst in listings_by_recency:
                    val = lst.get(field)
                    if self._is_non_null(val):
                        result[field] = val
                        sources[field] = lst.get("source_site", "unknown")
                        break

            elif field in self.BOOLEAN_FIELDS:
                # Optimistic: True if any True (handle SQLite 1/0 as bool)
                has_true = any(bool(v[0]) for v in values_with_sources)
                result[field] = has_true
                # Source is the one that provided True, or first if all False
                for val, src in values_with_sources:
                    if bool(val):
                        sources[field] = src
                        break
                else:
                    sources[field] = values_with_sources[0][1]

            elif field in self.TEXT_FIELDS:
                # Use longest value (more detail)
                longest_val = ""
                longest_src = ""
                for val, src in values_with_sources:
                    str_val = str(val) if val is not None else ""
                    if len(str_val) > len(longest_val):
                        longest_val = str_val
                        longest_src = src
                result[field] = longest_val if longest_val else None
                sources[field] = longest_src

            else:
                # Unknown field type - use most recent
                for lst in listings_by_recency:
                    val = lst.get(field)
                    if self._is_non_null(val):
                        result[field] = val
                        sources[field] = lst.get("source_site", "unknown")
                        break

        result["_sources"] = sources
        return result

    def get_price_discrepancy(self, listings: List[dict]) -> Optional[Dict[str, Any]]:
        """
        Calculate price difference across sources.

        Args:
            listings: List of listing dicts with price_eur field

        Returns:
            Dict with:
            - min_price: float
            - max_price: float
            - discrepancy: float (max - min)
            - discrepancy_pct: float ((max - min) / min * 100)
            - by_site: Dict[str, float] (site -> price)

            Or None if <2 listings have prices
        """
        # Convert and extract prices
        prices_by_site: Dict[str, float] = {}

        for lst in listings:
            lst_dict = self._to_dict(lst)
            price = lst_dict.get("price_eur")
            site = lst_dict.get("source_site", "unknown")

            if price is not None and price > 0:
                prices_by_site[site] = float(price)

        if len(prices_by_site) < 2:
            return None

        prices = list(prices_by_site.values())
        min_price = min(prices)
        max_price = max(prices)
        discrepancy = max_price - min_price

        # Avoid division by zero
        if min_price > 0:
            discrepancy_pct = (discrepancy / min_price) * 100
        else:
            discrepancy_pct = 0.0

        return {
            "min_price": min_price,
            "max_price": max_price,
            "discrepancy": discrepancy,
            "discrepancy_pct": discrepancy_pct,
            "by_site": prices_by_site,
        }

    def get_data_quality_score(self, listing: dict) -> float:
        """
        Score listing by data completeness (0-1).

        Important fields (weighted):
        - price_eur: 0.2
        - sqm_total: 0.15
        - rooms_count: 0.1
        - floor_number: 0.1
        - neighborhood: 0.1
        - description: 0.1
        - has_elevator: 0.05
        - building_type: 0.05
        - image_urls: 0.1
        - Other fields: 0.05 total

        Args:
            listing: Listing dict

        Returns:
            Score 0.0 to 1.0
        """
        lst_dict = self._to_dict(listing)
        score = 0.0

        # Score weighted fields
        for field, weight in self.QUALITY_WEIGHTS.items():
            val = lst_dict.get(field)
            if self._is_non_null(val):
                score += weight

        # Score other fields (split 0.05 among them)
        other_fields = set(lst_dict.keys()) - set(self.QUALITY_WEIGHTS.keys()) - self.EXCLUDE_FIELDS
        if other_fields:
            weight_per_field = self.OTHER_FIELDS_WEIGHT / len(other_fields)
            for field in other_fields:
                val = lst_dict.get(field)
                if self._is_non_null(val):
                    score += weight_per_field

        # Clamp to 0-1
        return min(1.0, max(0.0, score))
