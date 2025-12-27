"""
Tests for change detection tables and functions.

Tests:
- scrape_history table operations
- listing_changes table operations
- detect_all_changes function
"""

import json
import pytest
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.change_detector import compute_hash, has_changed, track_price_change, detect_all_changes, SKIP_FIELDS


# =============================================================================
# COMPUTE HASH TESTS
# =============================================================================

def test_compute_hash_basic():
    """Test hash computation with basic listing data."""
    listing = MagicMock()
    listing.price_eur = 100000
    listing.sqm_total = 80
    listing.rooms_count = 3
    listing.floor_number = 5
    listing.description = "Nice apartment"

    hash1 = compute_hash(listing)

    assert len(hash1) == 64  # SHA256 hex digest
    assert hash1.isalnum()


def test_compute_hash_different_price():
    """Test that different prices produce different hashes."""
    listing1 = MagicMock()
    listing1.price_eur = 100000
    listing1.sqm_total = 80
    listing1.rooms_count = 3
    listing1.floor_number = 5
    listing1.description = "Nice apartment"

    listing2 = MagicMock()
    listing2.price_eur = 95000  # Different price
    listing2.sqm_total = 80
    listing2.rooms_count = 3
    listing2.floor_number = 5
    listing2.description = "Nice apartment"

    assert compute_hash(listing1) != compute_hash(listing2)


def test_compute_hash_same_data():
    """Test that same data produces same hash."""
    listing1 = MagicMock()
    listing1.price_eur = 100000
    listing1.sqm_total = 80
    listing1.rooms_count = 3
    listing1.floor_number = 5
    listing1.description = "Nice apartment"

    listing2 = MagicMock()
    listing2.price_eur = 100000
    listing2.sqm_total = 80
    listing2.rooms_count = 3
    listing2.floor_number = 5
    listing2.description = "Nice apartment"

    assert compute_hash(listing1) == compute_hash(listing2)


def test_compute_hash_handles_none():
    """Test hash computation with None values."""
    listing = MagicMock()
    listing.price_eur = None
    listing.sqm_total = None
    listing.rooms_count = None
    listing.floor_number = None
    listing.description = None

    hash1 = compute_hash(listing)

    assert len(hash1) == 64


# =============================================================================
# HAS CHANGED TESTS
# =============================================================================

def test_has_changed_true_when_different():
    """Test has_changed returns True when hashes differ."""
    assert has_changed("abc123", "def456") is True


def test_has_changed_false_when_same():
    """Test has_changed returns False when hashes match."""
    assert has_changed("abc123", "abc123") is False


def test_has_changed_true_when_stored_none():
    """Test has_changed returns True when no stored hash."""
    assert has_changed("abc123", None) is True


# =============================================================================
# TRACK PRICE CHANGE TESTS
# =============================================================================

def test_track_price_change_no_change():
    """Test tracking when price unchanged."""
    changed, history_json, diff = track_price_change(100000, 100000, None)

    assert changed is False
    assert diff is None


def test_track_price_change_price_dropped():
    """Test tracking when price dropped."""
    changed, history_json, diff = track_price_change(95000, 100000, None)

    assert changed is True
    assert diff == -5000

    history = json.loads(history_json)
    assert len(history) == 1
    assert history[0]["price"] == 95000
    assert history[0]["previous"] == 100000


def test_track_price_change_price_increased():
    """Test tracking when price increased."""
    changed, history_json, diff = track_price_change(110000, 100000, None)

    assert changed is True
    assert diff == 10000


def test_track_price_change_first_price():
    """Test tracking first time price seen."""
    changed, history_json, diff = track_price_change(100000, None, None)

    assert changed is False  # Not a "change", just first observation
    assert diff is None

    history = json.loads(history_json)
    assert len(history) == 1
    assert history[0]["price"] == 100000
    assert "previous" not in history[0]


def test_track_price_change_appends_history():
    """Test that price changes append to existing history."""
    existing = json.dumps([{"price": 100000, "date": "2025-01-01"}])

    changed, history_json, diff = track_price_change(95000, 100000, existing)

    history = json.loads(history_json)
    assert len(history) == 2


def test_track_price_change_limits_history():
    """Test that history is limited to 10 entries."""
    # Create history with 10 entries
    existing = json.dumps([{"price": i * 1000, "date": f"2025-01-{i:02d}"} for i in range(1, 11)])

    changed, history_json, diff = track_price_change(50000, 60000, existing)

    history = json.loads(history_json)
    assert len(history) == 10  # Still 10, oldest dropped


# =============================================================================
# DETECT ALL CHANGES TESTS
# =============================================================================

def test_detect_all_changes_no_changes():
    """Test detect_all_changes with identical data."""
    old_data = {"price_eur": 100000, "title": "Test"}
    new_data = {"price_eur": 100000, "title": "Test"}

    with patch("data.data_store_main.record_field_change") as mock_record:
        changes = detect_all_changes(1, old_data, new_data, "imot.bg")

        assert len(changes) == 0
        mock_record.assert_not_called()


def test_detect_all_changes_with_changes():
    """Test detect_all_changes with different data."""
    old_data = {"price_eur": 100000, "title": "Old Title", "rooms_count": 3}
    new_data = {"price_eur": 95000, "title": "New Title", "rooms_count": 3}

    with patch("data.data_store_main.record_field_change") as mock_record:
        changes = detect_all_changes(1, old_data, new_data, "imot.bg")

        assert len(changes) == 2
        assert {"field": "price_eur", "old": 100000, "new": 95000} in changes
        assert {"field": "title", "old": "Old Title", "new": "New Title"} in changes
        assert mock_record.call_count == 2


def test_detect_all_changes_skips_volatile_fields():
    """Test that volatile fields are skipped."""
    old_data = {"price_eur": 100000, "scraped_at": "2025-01-01", "updated_at": "2025-01-01"}
    new_data = {"price_eur": 100000, "scraped_at": "2025-01-02", "updated_at": "2025-01-02"}

    with patch("data.data_store_main.record_field_change") as mock_record:
        changes = detect_all_changes(1, old_data, new_data, "imot.bg")

        # scraped_at and updated_at should be skipped
        assert len(changes) == 0
        mock_record.assert_not_called()


def test_detect_all_changes_new_field():
    """Test detecting a new field that wasn't in old data."""
    old_data = {"price_eur": 100000}
    new_data = {"price_eur": 100000, "has_elevator": True}

    with patch("data.data_store_main.record_field_change") as mock_record:
        changes = detect_all_changes(1, old_data, new_data, "imot.bg")

        assert len(changes) == 1
        assert changes[0] == {"field": "has_elevator", "old": None, "new": True}


def test_detect_all_changes_removed_field():
    """Test detecting a field that was removed."""
    old_data = {"price_eur": 100000, "has_elevator": True}
    new_data = {"price_eur": 100000}

    with patch("data.data_store_main.record_field_change") as mock_record:
        changes = detect_all_changes(1, old_data, new_data, "imot.bg")

        assert len(changes) == 1
        assert changes[0] == {"field": "has_elevator", "old": True, "new": None}


def test_skip_fields_contains_expected():
    """Test that SKIP_FIELDS contains expected volatile fields."""
    assert "scraped_at" in SKIP_FIELDS
    assert "updated_at" in SKIP_FIELDS
    assert "content_hash" in SKIP_FIELDS
    assert "price_history" in SKIP_FIELDS


# =============================================================================
# DATABASE FUNCTION TESTS (using mocks)
# =============================================================================

def test_upsert_scrape_history_new_url():
    """Test upserting a new URL."""
    from data import data_store_main

    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = None  # No existing record

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.upsert_scrape_history("https://example.com/new", "hash123")

        assert result is True
        # Verify INSERT was called
        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("INSERT INTO scrape_history" in str(c) for c in calls)


def test_upsert_scrape_history_unchanged():
    """Test upserting when content unchanged."""
    from data import data_store_main

    mock_row = {"content_hash": "same_hash"}
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = mock_row

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.upsert_scrape_history("https://example.com", "same_hash")

        assert result is False  # No change


def test_upsert_scrape_history_changed():
    """Test upserting when content changed."""
    from data import data_store_main

    mock_row = {"content_hash": "old_hash"}
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = mock_row

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.upsert_scrape_history("https://example.com", "new_hash")

        assert result is True  # Changed


def test_record_field_change():
    """Test recording a field change."""
    from data import data_store_main

    mock_conn = MagicMock()
    mock_conn.execute.return_value.lastrowid = 42

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.record_field_change(
            listing_id=1,
            field_name="price_eur",
            old_value=100000,
            new_value=95000,
            source_site="imot.bg"
        )

        assert result == 42
        # Verify INSERT was called
        calls = [str(c) for c in mock_conn.execute.call_args_list]
        assert any("INSERT INTO listing_changes" in str(c) for c in calls)


def test_record_field_change_json_serializes():
    """Test that complex values are JSON serialized."""
    from data import data_store_main

    mock_conn = MagicMock()
    mock_conn.execute.return_value.lastrowid = 1

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        data_store_main.record_field_change(
            listing_id=1,
            field_name="image_urls",
            old_value=["a.jpg"],
            new_value=["a.jpg", "b.jpg"],
            source_site="imot.bg"
        )

        # Get the INSERT call arguments
        insert_call = [c for c in mock_conn.execute.call_args_list
                      if "INSERT INTO listing_changes" in str(c)][0]
        args = insert_call[0][1]  # Second positional arg is the tuple of values

        # Check that list values were JSON serialized
        assert '["a.jpg"]' in str(args)
        assert '["a.jpg", "b.jpg"]' in str(args)


def test_mark_url_status_valid():
    """Test marking URL with valid status."""
    from data import data_store_main

    mock_conn = MagicMock()

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.mark_url_status("https://example.com", "removed")

        assert result is True
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called()


def test_mark_url_status_invalid():
    """Test marking URL with invalid status."""
    from data import data_store_main

    result = data_store_main.mark_url_status("https://example.com", "invalid_status")

    assert result is False


def test_get_scrape_history():
    """Test getting scrape history."""
    from data import data_store_main

    mock_row = {"url": "https://example.com", "content_hash": "abc", "scrape_count": 5}
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchone.return_value = mock_row

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.get_scrape_history("https://example.com")

        assert result == mock_row


def test_get_listing_changes():
    """Test getting listing changes."""
    from data import data_store_main

    mock_rows = [
        {"field_name": "price_eur", "old_value": "100000", "new_value": "95000"},
        {"field_name": "title", "old_value": "Old", "new_value": "New"},
    ]
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = mock_rows

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.get_listing_changes(1)

        assert len(result) == 2


def test_get_listing_changes_filtered():
    """Test getting listing changes filtered by field."""
    from data import data_store_main

    mock_rows = [{"field_name": "price_eur", "old_value": "100000", "new_value": "95000"}]
    mock_conn = MagicMock()
    mock_conn.execute.return_value.fetchall.return_value = mock_rows

    with patch.object(data_store_main, "get_db_connection", return_value=mock_conn):
        result = data_store_main.get_listing_changes(1, field="price_eur")

        assert len(result) == 1
        # Verify query included field filter
        call_args = mock_conn.execute.call_args[0]
        assert "field_name = ?" in call_args[0]


def test_get_price_history_from_changes():
    """Test convenience function for price history."""
    from data import data_store_main

    mock_rows = [
        MagicMock(spec=sqlite3.Row),
        MagicMock(spec=sqlite3.Row),
    ]
    mock_rows[0].__getitem__ = lambda self, key: {"old_value": "100000", "new_value": "95000", "changed_at": "2025-01-01"}[key]
    mock_rows[1].__getitem__ = lambda self, key: {"old_value": "95000", "new_value": "90000", "changed_at": "2025-01-02"}[key]

    with patch.object(data_store_main, "get_listing_changes", return_value=mock_rows):
        result = data_store_main.get_price_history_from_changes(1)

        assert len(result) == 2
        assert all("old_value" in h and "new_value" in h and "changed_at" in h for h in result)
