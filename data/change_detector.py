"""
Change detection for listings.

Provides:
- compute_hash(): Generate content hash from ListingData
- has_changed(): Compare with stored hash
- track_price_change(): Price history tracking
- detect_all_changes(): Compare dicts and record all field changes
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger


def compute_hash(listing_data) -> str:
    """
    Compute SHA256 hash of key listing fields.

    Only hashes fields that affect listing value:
    - price_eur, sqm_total, rooms_count, floor_number, description

    Excludes volatile fields like scraped_at, image_urls.

    Args:
        listing_data: ListingData object from scraper

    Returns:
        SHA256 hex digest (64 characters)
    """
    key_fields = [
        str(listing_data.price_eur or ""),
        str(listing_data.sqm_total or ""),
        str(listing_data.rooms_count or ""),
        str(listing_data.floor_number or ""),
        (listing_data.description or "")[:1000],  # Truncate long descriptions
    ]
    content = "|".join(key_fields)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def has_changed(new_hash: str, stored_hash: Optional[str]) -> bool:
    """
    Quick check if content changed.

    Args:
        new_hash: Hash of newly scraped listing
        stored_hash: Hash from database (None if new listing or old listing without hash)

    Returns:
        True if content changed or no stored hash exists
    """
    if stored_hash is None:
        return True  # New listing or legacy listing without hash
    return new_hash != stored_hash


def track_price_change(
    current_price: Optional[float],
    stored_price: Optional[float],
    price_history_json: Optional[str],
) -> tuple[bool, str, Optional[float]]:
    """
    Track price changes and update history.

    Args:
        current_price: Current listing price in EUR
        stored_price: Previously stored price
        price_history_json: JSON string of price history array

    Returns:
        Tuple of (price_changed: bool, updated_history_json: str, price_diff: Optional[float])
    """
    history = json.loads(price_history_json) if price_history_json else []

    if current_price is None:
        return False, json.dumps(history), None

    price_diff = None
    if stored_price is not None and current_price != stored_price:
        price_diff = current_price - stored_price
        # Price changed - add to history
        history.append(
            {
                "price": current_price,
                "date": datetime.utcnow().isoformat(),
                "previous": stored_price,
            }
        )
        # Keep last 10 entries
        history = history[-10:]

        direction = "dropped" if price_diff < 0 else "increased"
        logger.info(
            f"Price {direction}: {stored_price} -> {current_price} EUR "
            f"(diff: {price_diff:+.0f})"
        )
        return True, json.dumps(history), price_diff

    if stored_price is None and current_price is not None:
        # First time seeing this listing with a price
        history.append(
            {
                "price": current_price,
                "date": datetime.utcnow().isoformat(),
            }
        )
        return False, json.dumps(history), None

    return False, json.dumps(history), None


# Fields to skip when comparing listings (volatile or non-value fields)
SKIP_FIELDS = frozenset({
    "id", "scraped_at", "updated_at", "created_at",
    "content_hash", "last_change_at", "change_count",
    "price_history", "consecutive_unchanged",
})


def detect_all_changes(
    listing_id: int,
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    source_site: str,
) -> List[Dict[str, Any]]:
    """
    Compare two dicts and record all field changes to the database.

    Args:
        listing_id: ID of the listing
        old_data: Previous listing data as dict
        new_data: New listing data as dict
        source_site: Source website name

    Returns:
        List of changes detected: [{"field": str, "old": Any, "new": Any}]
    """
    from data.data_store_main import record_field_change

    changes = []
    all_fields = set(old_data.keys()) | set(new_data.keys())

    for field in all_fields:
        if field in SKIP_FIELDS:
            continue

        old_val = old_data.get(field)
        new_val = new_data.get(field)

        if old_val != new_val:
            changes.append({"field": field, "old": old_val, "new": new_val})
            record_field_change(listing_id, field, old_val, new_val, source_site)

    if changes:
        logger.info(f"Detected {len(changes)} field changes for listing {listing_id}")

    return changes
