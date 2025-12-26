# Spec 111: Page Change Detection

**Status**: Draft
**Created**: 2025-12-26
**Research**: [page_change_detection.md](../research/page_change_detection.md)

---

## Problem

Currently, every scrape re-downloads and re-processes all listings, even if nothing changed. This wastes:
- Bandwidth (downloading unchanged pages)
- CPU (parsing unchanged HTML)
- Proxy requests (using up proxy pool)

---

## Solution Overview

Add multi-layer change detection:

| Layer | Method | When Used | Savings |
|-------|--------|-----------|---------|
| 1 | Hash comparison | Before full parse | Skip if identical |
| 2 | Difflib similarity | When hash differs | Quantify changes |
| 3 | Price tracking | Always | Alert on price drop |

---

## Architecture Fit

### Where It Lives

```
data/
├── data_store_main.py    # Existing - add migration
├── change_detector.py    # NEW - change detection logic
```

**Why `data/`**: Change detection is data layer concern (storage + comparison).

### Integration Points

```
main.py                    # Integration point
    ↓
scraper.extract_listing()  # Returns ListingData
    ↓
change_detector.check()    # NEW - compare with stored
    ↓
data_store_main.save()     # Update with change info
```

---

## Database Changes

### New Columns (via migration)

```python
# data/data_store_main.py - add to migrate_listings_schema()
new_columns = [
    # Change detection
    ("content_hash", "TEXT"),              # SHA256 of key content
    ("last_change_at", "TIMESTAMP"),       # When content last changed
    ("change_count", "INTEGER DEFAULT 0"), # How many times changed
    ("price_history", "TEXT"),             # JSON: [{"price": 150000, "date": "2025-12-26"}, ...]
    ("consecutive_unchanged", "INTEGER DEFAULT 0"),  # For adaptive scheduling
]
```

### Index

```sql
CREATE INDEX IF NOT EXISTS idx_listings_hash ON listings(content_hash);
```

---

## Implementation

### 1. ChangeDetector Class

**File**: `data/change_detector.py`

```python
"""
Change detection for listings.

Provides:
- compute_hash(): Generate content hash
- has_changed(): Compare with stored hash
- detect_changes(): Detailed diff analysis
- track_price_change(): Price history tracking
"""

import hashlib
import json
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional

from loguru import logger


SIMILARITY_THRESHOLD = 0.95  # <95% = significant change


def compute_hash(listing_data) -> str:
    """Compute SHA256 hash of key listing fields."""
    # Hash only fields that matter for change detection
    # Ignore: scraped_at, image_urls (order may vary)
    key_fields = [
        str(listing_data.price_eur or ""),
        str(listing_data.sqm_total or ""),
        str(listing_data.rooms_count or ""),
        str(listing_data.floor_number or ""),
        listing_data.description or "",
    ]
    content = "|".join(key_fields)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def has_changed(new_hash: str, stored_hash: Optional[str]) -> bool:
    """Quick check if content changed."""
    if stored_hash is None:
        return True  # New listing
    return new_hash != stored_hash


def detect_changes(old_description: str, new_description: str) -> dict:
    """Detailed change analysis using difflib."""
    if not old_description or not new_description:
        return {"changed": True, "similarity": 0.0, "diff_summary": "New content"}

    similarity = SequenceMatcher(None, old_description, new_description).ratio()

    return {
        "changed": similarity < SIMILARITY_THRESHOLD,
        "similarity": round(similarity, 4),
        "diff_summary": f"Similarity: {similarity:.1%}",
    }


def track_price_change(
    current_price: Optional[float],
    stored_price: Optional[float],
    price_history_json: Optional[str]
) -> tuple[bool, str]:
    """Track price changes and update history.

    Returns:
        (changed: bool, updated_history_json: str)
    """
    history = json.loads(price_history_json) if price_history_json else []

    if current_price is None:
        return False, json.dumps(history)

    if stored_price is None or current_price != stored_price:
        # Price changed - add to history
        history.append({
            "price": current_price,
            "date": datetime.utcnow().isoformat(),
        })
        # Keep last 10 entries
        history = history[-10:]
        return True, json.dumps(history)

    return False, json.dumps(history)
```

### 2. Integration in main.py

```python
# main.py - in scraping loop

from data.change_detector import compute_hash, has_changed, track_price_change
from data.data_store_main import get_listing_by_url, save_listing

async def scrape_listing(url: str, scraper, proxy: str):
    # 1. Fetch HTML
    html = await fetch_page(url, proxy)

    # 2. Extract listing
    listing = await scraper.extract_listing(html, url)
    if not listing:
        return None

    # 3. Check for changes
    stored = get_listing_by_url(url)
    new_hash = compute_hash(listing)

    if stored and not has_changed(new_hash, stored["content_hash"]):
        # No change - skip full processing
        logger.debug(f"Unchanged: {url}")
        update_consecutive_unchanged(url)  # Track for adaptive scheduling
        return None

    # 4. Track price change
    price_changed, new_history = track_price_change(
        listing.price_eur,
        stored["price_eur"] if stored else None,
        stored["price_history"] if stored else None,
    )

    if price_changed:
        logger.info(f"Price changed: {url} - {stored['price_eur']} -> {listing.price_eur}")

    # 5. Save with change metadata
    save_listing(listing, content_hash=new_hash, price_history=new_history)

    return listing
```

### 3. Database Migration

```python
# data/data_store_main.py - add to new_columns list

# Change detection columns
("content_hash", "TEXT"),
("last_change_at", "TIMESTAMP"),
("change_count", "INTEGER DEFAULT 0"),
("price_history", "TEXT"),
("consecutive_unchanged", "INTEGER DEFAULT 0"),
```

### 4. Update save_listing()

```python
# data/data_store_main.py - modify save_listing()

def save_listing(listing, content_hash: str = None, price_history: str = None) -> Optional[int]:
    # ... existing code ...

    # Add change tracking to INSERT
    cursor = conn.execute("""
        INSERT INTO listings (
            ...,
            content_hash, price_history
        ) VALUES (..., ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            price_eur = excluded.price_eur,
            content_hash = excluded.content_hash,
            price_history = excluded.price_history,
            last_change_at = CASE
                WHEN content_hash != excluded.content_hash
                THEN CURRENT_TIMESTAMP
                ELSE last_change_at
            END,
            change_count = CASE
                WHEN content_hash != excluded.content_hash
                THEN change_count + 1
                ELSE change_count
            END,
            consecutive_unchanged = CASE
                WHEN content_hash != excluded.content_hash
                THEN 0
                ELSE consecutive_unchanged + 1
            END,
            is_active = 1,
            updated_at = CURRENT_TIMESTAMP
    """, (..., content_hash, price_history))
```

---

## What We Hash

**Include** (affects listing value):
- `price_eur`
- `sqm_total`
- `rooms_count`
- `floor_number`
- `description` (truncated to 1000 chars)

**Exclude** (noise):
- `scraped_at` (always changes)
- `image_urls` (order may vary)
- `updated_at` (always changes)

---

## Phases

### Phase 1: Basic Hash Detection
- [ ] Add columns via migration
- [ ] Create `data/change_detector.py`
- [ ] Implement `compute_hash()` and `has_changed()`
- [ ] Integrate into `main.py`
- [ ] Test: Same listing scraped twice → skipped second time

### Phase 2: Price Tracking
- [ ] Implement `track_price_change()`
- [ ] Add price_history column
- [ ] Log price changes
- [ ] Test: Price drop detected and logged

### Phase 3: Dashboard Integration (Optional)
- [ ] Show price history chart in Streamlit
- [ ] Show "changed since last visit" indicator
- [ ] Filter by "recently changed"

---

## Testing

```python
# tests/test_change_detector.py

def test_compute_hash_deterministic():
    """Same input produces same hash."""
    listing1 = ListingData(external_id="1", url="...", source_site="imot.bg", price_eur=150000)
    listing2 = ListingData(external_id="1", url="...", source_site="imot.bg", price_eur=150000)
    assert compute_hash(listing1) == compute_hash(listing2)

def test_compute_hash_different_price():
    """Different price produces different hash."""
    listing1 = ListingData(external_id="1", url="...", source_site="imot.bg", price_eur=150000)
    listing2 = ListingData(external_id="1", url="...", source_site="imot.bg", price_eur=145000)
    assert compute_hash(listing1) != compute_hash(listing2)

def test_has_changed_new_listing():
    """New listing (no stored hash) returns True."""
    assert has_changed("abc123", None) is True

def test_has_changed_same_hash():
    """Same hash returns False."""
    assert has_changed("abc123", "abc123") is False

def test_track_price_change():
    """Price change updates history."""
    changed, history = track_price_change(145000, 150000, None)
    assert changed is True
    assert "145000" in history
```

---

## Not Included (Future)

| Feature | Why Deferred |
|---------|--------------|
| HTTP 304 (ETag/Last-Modified) | Real estate sites don't support it |
| Adaptive scheduling | Need more data on change frequency first |
| Full difflib analysis | Overkill for v1 - hash is enough |
| Semantic similarity | CPU intensive, not needed yet |

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `data/change_detector.py` | Create |
| `data/data_store_main.py` | Modify (migration + save_listing) |
| `main.py` | Modify (integrate change detection) |
| `tests/test_change_detector.py` | Create |

---

## Acceptance Criteria

- [ ] Unchanged listings are skipped (verified by logs)
- [ ] Changed listings are fully processed
- [ ] Price changes are logged
- [ ] price_history JSON is populated
- [ ] content_hash is stored in DB
- [ ] All tests pass
