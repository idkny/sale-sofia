"""
Unit tests for the change detection system.

Tests cover:
- Hash computation determinism
- Hash changes with different fields
- has_changed logic with edge cases
- Price tracking and history
"""

import json

import pytest

from data.change_detector import compute_hash, has_changed, track_price_change
from websites.base_scraper import ListingData


@pytest.fixture
def sample_listing():
    """Create a sample ListingData for testing."""
    return ListingData(
        external_id="12345",
        url="https://example.com/listing/12345",
        source_site="test.bg",
        price_eur=150000,
        sqm_total=85.5,
        rooms_count=3,
        floor_number=4,
        description="Nice apartment in the center",
    )


class TestComputeHash:
    """Test hash computation."""

    def test_deterministic(self, sample_listing):
        """Same input produces same hash."""
        hash1 = compute_hash(sample_listing)
        hash2 = compute_hash(sample_listing)
        assert hash1 == hash2

    def test_hash_length(self, sample_listing):
        """Hash is SHA256 hex (64 chars)."""
        h = compute_hash(sample_listing)
        assert len(h) == 64

    def test_different_price(self, sample_listing):
        """Different price produces different hash."""
        hash1 = compute_hash(sample_listing)
        sample_listing.price_eur = 145000
        hash2 = compute_hash(sample_listing)
        assert hash1 != hash2

    def test_different_sqm(self, sample_listing):
        """Different sqm produces different hash."""
        hash1 = compute_hash(sample_listing)
        sample_listing.sqm_total = 90.0
        hash2 = compute_hash(sample_listing)
        assert hash1 != hash2

    def test_different_rooms(self, sample_listing):
        """Different rooms count produces different hash."""
        hash1 = compute_hash(sample_listing)
        sample_listing.rooms_count = 4
        hash2 = compute_hash(sample_listing)
        assert hash1 != hash2

    def test_different_floor(self, sample_listing):
        """Different floor produces different hash."""
        hash1 = compute_hash(sample_listing)
        sample_listing.floor_number = 5
        hash2 = compute_hash(sample_listing)
        assert hash1 != hash2

    def test_different_description(self, sample_listing):
        """Different description produces different hash."""
        hash1 = compute_hash(sample_listing)
        sample_listing.description = "Updated description text"
        hash2 = compute_hash(sample_listing)
        assert hash1 != hash2

    def test_none_fields(self):
        """None fields are handled gracefully."""
        listing = ListingData(
            external_id="1",
            url="https://example.com/1",
            source_site="test.bg",
        )
        h = compute_hash(listing)
        assert h is not None
        assert len(h) == 64

    def test_long_description_truncated(self, sample_listing):
        """Long descriptions are truncated before hashing."""
        sample_listing.description = "x" * 2000
        hash1 = compute_hash(sample_listing)

        # Different content beyond 1000 chars shouldn't change hash
        sample_listing.description = "x" * 1000 + "y" * 1000
        hash2 = compute_hash(sample_listing)

        # Both should hash the same (first 1000 chars)
        assert hash1 == hash2

    def test_same_url_different_sites(self):
        """Same data on different sites produces same hash."""
        listing1 = ListingData(
            external_id="1",
            url="https://site1.com/1",
            source_site="site1.bg",
            price_eur=100000,
        )
        listing2 = ListingData(
            external_id="1",
            url="https://site2.com/1",
            source_site="site2.bg",
            price_eur=100000,
        )
        # URL and source_site not hashed - only price, sqm, rooms, floor, description
        assert compute_hash(listing1) == compute_hash(listing2)


class TestHasChanged:
    """Test change detection."""

    def test_new_listing(self):
        """New listing (no stored hash) returns True."""
        assert has_changed("abc123", None) is True

    def test_same_hash(self):
        """Same hash returns False."""
        assert has_changed("abc123", "abc123") is False

    def test_different_hash(self):
        """Different hash returns True."""
        assert has_changed("abc123", "def456") is True

    def test_empty_string_stored(self):
        """Empty string stored hash returns True."""
        assert has_changed("abc123", "") is True

    def test_empty_string_new(self):
        """Empty string new hash compared to non-empty returns True."""
        assert has_changed("", "abc123") is True


class TestTrackPriceChange:
    """Test price change tracking."""

    def test_price_unchanged(self):
        """Same price returns no change."""
        changed, history, diff = track_price_change(150000, 150000, None)
        assert changed is False
        assert diff is None

    def test_price_drop(self):
        """Price drop is detected."""
        changed, history, diff = track_price_change(145000, 150000, None)
        assert changed is True
        assert diff == -5000

        history_data = json.loads(history)
        assert len(history_data) == 1
        assert history_data[0]["price"] == 145000
        assert history_data[0]["previous"] == 150000

    def test_price_increase(self):
        """Price increase is detected."""
        changed, history, diff = track_price_change(160000, 150000, None)
        assert changed is True
        assert diff == 10000

        history_data = json.loads(history)
        assert len(history_data) == 1
        assert history_data[0]["price"] == 160000
        assert history_data[0]["previous"] == 150000

    def test_history_appended(self):
        """New price is appended to existing history."""
        existing = json.dumps([{"price": 160000, "date": "2025-01-01"}])
        changed, history, diff = track_price_change(155000, 160000, existing)

        history_data = json.loads(history)
        assert len(history_data) == 2
        assert history_data[0]["price"] == 160000  # Old entry
        assert history_data[1]["price"] == 155000  # New entry

    def test_history_limit(self):
        """History is limited to 10 entries."""
        existing = json.dumps(
            [{"price": i * 1000, "date": f"2025-01-{i:02d}"} for i in range(1, 11)]
        )
        changed, history, diff = track_price_change(50000, 10000, existing)

        history_data = json.loads(history)
        assert len(history_data) == 10
        assert history_data[-1]["price"] == 50000  # Newest
        assert history_data[0]["price"] == 2000  # Oldest kept (first one dropped)

    def test_first_price(self):
        """First price for new listing."""
        changed, history, diff = track_price_change(150000, None, None)
        assert changed is False  # Not a "change" - just first recording
        assert diff is None

        history_data = json.loads(history)
        assert len(history_data) == 1
        assert history_data[0]["price"] == 150000
        assert "previous" not in history_data[0]

    def test_none_current_price(self):
        """None current price is handled."""
        changed, history, diff = track_price_change(None, 150000, None)
        assert changed is False
        assert diff is None
        assert history == "[]"

    def test_none_both_prices(self):
        """Both prices None is handled."""
        changed, history, diff = track_price_change(None, None, None)
        assert changed is False
        assert diff is None
        assert history == "[]"

    def test_price_change_date_recorded(self):
        """Price change records ISO date."""
        changed, history, diff = track_price_change(145000, 150000, None)
        history_data = json.loads(history)

        assert "date" in history_data[0]
        # Should be ISO format like "2025-12-26T10:30:00.123456"
        assert "T" in history_data[0]["date"]
