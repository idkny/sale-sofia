# Spec 106B: Cross-Site Duplicate Detection & Merging

**Phase**: 3.5 of Crawler Validation
**Status**: Draft
**Author**: Instance 2
**Created**: 2025-12-27

---

## Overview

Identify when the same property is listed on multiple sites (imot.bg, bazar.bg) and provide:
1. Deduplication via fingerprinting
2. Data merging from multiple sources
3. Price discrepancy tracking
4. Cross-site comparison dashboard view

---

## Problem Statement

Same apartment can appear on multiple sites with:
- Different listing IDs
- Slightly different data (one site may have more details)
- Different prices (price discrepancies indicate negotiation room)
- Different update frequencies

**Goal**: Link these listings and provide unified view while preserving source data.

---

## Design

### 1. Fingerprint Generation

Generate consistent fingerprint from property characteristics (not site-specific IDs):

```
fingerprint = SHA256(
    normalize(neighborhood) + "|" +
    round(sqm_total, 0) + "|" +
    rooms_count + "|" +
    floor_number + "|" +
    normalize(building_type)
)[:16]  # First 16 chars of hash
```

**Normalization Rules:**
- Lowercase, strip whitespace
- Remove accents (Cyrillic normalization)
- Round sqm to nearest integer
- `None` values → empty string

**Collision Handling:**
- Same fingerprint = likely same property
- Manual review if >2 sources have same fingerprint
- Allow user override via dashboard

### 2. Database Schema

#### New Table: `listing_sources`

Links listings that represent the same property.

```sql
CREATE TABLE listing_sources (
    id INTEGER PRIMARY KEY,
    property_fingerprint TEXT NOT NULL,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    source_site TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_price_eur REAL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT 0,  -- Primary source for display
    UNIQUE(property_fingerprint, source_site)
);
CREATE INDEX idx_sources_fingerprint ON listing_sources(property_fingerprint);
CREATE INDEX idx_sources_listing ON listing_sources(listing_id);
```

**Note**: We reuse existing `listings` table (no new `properties` table). The `listing_sources` table groups listings by fingerprint.

### 3. Classes

#### PropertyFingerprinter (`data/property_fingerprinter.py`)

```python
class PropertyFingerprinter:
    """Generate fingerprints for cross-site matching."""

    def compute(self, listing: ListingData) -> str:
        """Generate fingerprint from listing data."""

    def normalize_neighborhood(self, name: str) -> str:
        """Normalize neighborhood names across sites."""

    def find_matches(self, fingerprint: str) -> List[Row]:
        """Find existing listings with same fingerprint."""
```

#### PropertyMerger (`data/property_merger.py`)

```python
class PropertyMerger:
    """Merge data from multiple listing sources."""

    def merge(self, listings: List[Row]) -> Dict[str, Any]:
        """Merge multiple listings into best-available data."""

    def get_price_discrepancy(self, listings: List[Row]) -> Optional[Dict]:
        """Calculate price difference across sources."""

    def get_data_quality_score(self, listing: Row) -> float:
        """Score listing by data completeness (0-1)."""
```

**Merge Strategy:**
1. For each field, pick non-null value
2. If multiple non-null values differ:
   - Numeric: use average or most recent
   - Text: use longest (more detail)
   - Boolean: use True if any True (optimistic)
3. Track which source provided each field

### 4. Price Discrepancy Tracking

Store price differences in `listing_changes` (reuse existing table):

```python
def track_cross_site_price(property_fingerprint: str) -> Optional[Dict]:
    """Compare prices across sites for same property."""
    sources = get_sources_by_fingerprint(property_fingerprint)
    if len(sources) < 2:
        return None

    prices = {s.source_site: s.source_price_eur for s in sources}
    return {
        "min_price": min(prices.values()),
        "max_price": max(prices.values()),
        "discrepancy": max - min,
        "discrepancy_pct": (max - min) / min * 100,
        "by_site": prices
    }
```

### 5. Dashboard View

Add to Streamlit dashboard (`app/pages/`):

**Cross-Site Comparison Page:**
- List properties with multiple sources
- Show price discrepancy column
- Highlight >5% price differences
- Link to all source listings
- Filter by: discrepancy %, neighborhood, price range

---

## Implementation Plan

### Task 1: Create `listing_sources` table
- Add table definition to `data/data_store_main.py`
- Add `init_listing_sources_table()` function
- Add CRUD functions: `add_source`, `get_sources_by_fingerprint`, `update_source`

### Task 2: Build PropertyFingerprinter
- Create `data/property_fingerprinter.py`
- Implement `compute()` with normalization
- Implement `find_matches()` for duplicate detection
- Write unit tests

### Task 3: Build PropertyMerger
- Create `data/property_merger.py`
- Implement `merge()` with field-level strategy
- Implement `get_price_discrepancy()`
- Write unit tests

### Task 4: Integrate into scraping pipeline
- Call fingerprinter after extracting listing
- Check for matches and update `listing_sources`
- Log duplicate detections

### Task 5: Dashboard view
- Create `app/pages/cross_site.py`
- Show duplicates with price comparison
- Add filters and sorting

---

## Testing Strategy

### Unit Tests (`tests/test_cross_site.py`)
- Fingerprint generation consistency
- Fingerprint normalization edge cases
- Merge logic for each field type
- Price discrepancy calculation

### Integration Tests
- Save listing → fingerprint generated → sources linked
- Multi-site match detection
- Dashboard data retrieval

---

## Configuration

Add to `config/settings.py`:

```python
# Cross-site deduplication
FINGERPRINT_FIELDS = ["neighborhood", "sqm_total", "rooms_count", "floor_number", "building_type"]
PRICE_DISCREPANCY_THRESHOLD_PCT = 5.0  # Highlight if >5% difference
```

---

## Success Criteria

1. Same property listed on imot.bg and bazar.bg gets same fingerprint
2. Price differences shown in dashboard
3. No false positives (different properties matched incorrectly)
4. <1% false negatives (same property not matched)

---

## Out of Scope

- Address geocoding (future enhancement)
- Image-based deduplication
- Cross-city matching (Sofia only for now)
