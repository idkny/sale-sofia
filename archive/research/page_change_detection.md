# Research: Page Change Detection from ZohoCentral/autobiz

**Date**: 2025-12-26
**Source**: `/home/wow/Documents/ZohoCentral/autobiz`
**Purpose**: Understand how to detect if a listing has changed and needs re-scraping

---

## Summary

The autobiz project uses a **multi-layered change detection system**:

| Layer | Method | Speed | Purpose |
|-------|--------|-------|---------|
| 1 | HTTP 304 | Fastest | No body download if unchanged |
| 2 | SHA256 Hash | Fast | Quick duplicate detection |
| 3 | Difflib Comparison | Thorough | Line-by-line change analysis |
| 4 | Adaptive Scheduling | Smart | Learn change patterns per URL |

---

## 1. Hashing Implementation

**Hash Type**: SHA256
**What's Hashed**: Full HTML content OR specific CSS selectors

```python
# From: tools/scraping/_freshness_checker.py:65-86
import hashlib
from bs4 import BeautifulSoup

def compute_content_hash(html: str, selectors: list[str] | None = None) -> str:
    """Compute SHA256 hash of HTML content."""
    if selectors:
        # Hash only specific elements (e.g., price, description)
        soup = BeautifulSoup(html, "html.parser")
        parts = []
        for selector in selectors:
            for element in soup.select(selector):
                parts.append(element.get_text(strip=True))
        content = "".join(parts)
    else:
        # Hash full page
        content = html
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

**Key Insight**: Selective hashing is powerful - hash only `.price`, `.description` to ignore irrelevant changes (ads, timestamps).

---

## 2. Change Detection with Difflib

**Location**: `tools/intelligence/_competitor_tracker.py:34-119`

```python
import difflib
from typing import Any

SIMILARITY_THRESHOLD = 0.95  # 95% match = no significant change

def detect_changes(old_content: str, new_content: str) -> dict[str, Any]:
    """Detect changes between two versions of content."""

    # Calculate similarity ratio (0.0 to 1.0)
    similarity = difflib.SequenceMatcher(None, old_content, new_content).ratio()

    # Get line-by-line diff
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))

    added = [line[2:] for line in diff if line.startswith("+ ")]
    removed = [line[2:] for line in diff if line.startswith("- ")]

    return {
        "changed": similarity < SIMILARITY_THRESHOLD,
        "similarity": round(similarity, 4),
        "added_lines": len(added),
        "removed_lines": len(removed),
        "added_content": added,
        "removed_content": removed,
        "diff_summary": f"+{len(added)} lines, -{len(removed)} lines"
    }
```

---

## 3. HTTP 304 Not Modified

**Location**: `tools/scraping/_freshness_checker.py:41-60, 91-100`

```python
def build_freshness_headers(url_record) -> dict[str, str]:
    """Build HTTP headers for conditional requests."""
    headers = {}
    if url_record.etag:
        headers["If-None-Match"] = url_record.etag
    if url_record.last_modified:
        headers["If-Modified-Since"] = url_record.last_modified
    return headers

def is_304_response(status_code: int) -> bool:
    """Check if response is HTTP 304 Not Modified."""
    return status_code == 304
```

**Benefit**: If server returns 304, no body download needed - saves 80%+ bandwidth.

---

## 4. Adaptive Scheduling (EMA)

**Location**: `tools/scraping/_freshness_checker.py:135-184`

```python
EMA_ALPHA = 0.3  # Weight for new observation

def calculate_new_frequency_score(current_score: float, changed: bool) -> float:
    """Calculate updated change frequency score using EMA."""
    observation = 1.0 if changed else 0.0
    new_score = EMA_ALPHA * observation + (1 - EMA_ALPHA) * current_score
    return max(0.0, min(1.0, new_score))

def calculate_next_crawl_time(change_frequency_score: float) -> datetime:
    """Calculate next crawl time based on change frequency."""
    if change_frequency_score > 0.7:
        return datetime.now() + timedelta(hours=6)   # High frequency
    elif change_frequency_score > 0.5:
        return datetime.now() + timedelta(hours=24)  # Medium
    else:
        return datetime.now() + timedelta(days=7)    # Low frequency
```

**Key Insight**: URLs that change often get scraped more frequently. Stable URLs get scraped less.

---

## 5. Database Schema

### Scraper DB (Fast Metrics)

```sql
CREATE TABLE scrape_queue (
    url TEXT NOT NULL UNIQUE,
    content_hash TEXT DEFAULT NULL,
    etag TEXT DEFAULT NULL,
    last_modified_header TEXT DEFAULT NULL,
    change_frequency_score REAL DEFAULT 0.5,
    consecutive_no_change INTEGER DEFAULT 0,
    next_crawl_time TEXT DEFAULT NULL
);
```

### Main DB (Historical Analysis)

```sql
CREATE TABLE scraped_content (
    url TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL,
    content_text TEXT,
    similarity_ratio REAL DEFAULT NULL,
    change_summary TEXT DEFAULT NULL,
    last_change_detected_at TIMESTAMP DEFAULT NULL
);
```

---

## 6. Data Flow

```
SCRAPE REQUEST
     ↓
┌────────────────────────────────────────┐
│ 1. Build headers (ETag, Last-Modified) │
│ 2. Send conditional GET request        │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ 3. Check HTTP status                   │
│    ├─ 304 → No change, skip download   │
│    └─ 200 → Download content           │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ 4. Generate SHA256 hash                │
│ 5. Compare with stored hash            │
│    ├─ Same → No change                 │
│    └─ Different → Run difflib analysis │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│ 6. Update frequency score (EMA)        │
│ 7. Calculate next crawl time           │
│ 8. Store results in DB                 │
└────────────────────────────────────────┘
```

---

## 7. Recommendations for sale-sofia

### Phase 1: Immediate (Simple)

1. **Add content_hash to listings table**
   ```sql
   ALTER TABLE listings ADD COLUMN content_hash TEXT;
   ALTER TABLE listings ADD COLUMN last_change_at TIMESTAMP;
   ```

2. **Implement basic hash comparison**
   - SHA256 of listing page HTML
   - Skip scrape if hash unchanged

### Phase 2: Medium-term

1. **Selective element hashing**
   - Hash only price, description, features
   - Ignore ads, timestamps, random elements

2. **HTTP 304 support**
   - Store ETag/Last-Modified from responses
   - Send conditional headers on re-scrape

3. **Difflib change detection**
   - When hash differs, analyze what changed
   - Track price changes specifically

### Phase 3: Advanced

1. **Adaptive scheduling**
   - URLs that change often → scrape daily
   - Stable URLs → scrape weekly

2. **Change alerts**
   - Notify when price drops
   - Notify when listing removed

---

## Files to Reference

| Purpose | autobiz File |
|---------|--------------|
| Hash computation | `tools/scraping/_freshness_checker.py:65-86` |
| Change detection | `tools/intelligence/_competitor_tracker.py:34-119` |
| HTTP 304 headers | `tools/scraping/_freshness_checker.py:41-60` |
| Adaptive scheduling | `tools/scraping/_freshness_checker.py:135-184` |
| DB schema | `core/database/_schema.py`, `core/scraper_database/_migrations.py` |
| Integration tests | `tests/test_change_detection_integration.py` |
