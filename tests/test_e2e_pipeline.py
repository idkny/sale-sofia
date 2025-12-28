"""End-to-End Pipeline Tests: Scrape → Store → Dashboard.

Tests the complete data flow from scraping through storage to dashboard display.
Uses mocks for network calls to ensure fast, reliable tests.

Reference: TASKS.md Phase 5.1
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

# Import the core components
from websites.base_scraper import ListingData


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_listings.db"

    # Patch the DB_PATH to use our temp database
    with patch("data.data_store_main.DB_PATH", db_path):
        from data import data_store_main

        # Initialize the database
        data_store_main.init_db()
        data_store_main.migrate_listings_schema()

        yield db_path, data_store_main


@pytest.fixture
def sample_listing():
    """Create a sample ListingData object for testing."""
    return ListingData(
        external_id="TEST123",
        url="https://example.com/listing/TEST123",
        source_site="example.com",
        title="Beautiful 2-bedroom apartment in Sofia",
        description="Spacious apartment with great views",
        price_eur=150000.0,
        price_per_sqm_eur=1500.0,
        sqm_total=100.0,
        sqm_net=85.0,
        rooms_count=2,
        bathrooms_count=1,
        floor_number=3,
        floor_total=6,
        has_elevator=True,
        building_type="brick",
        construction_year=2010,
        act_status="act16",
        district="Lozenets",
        neighborhood="Center",
        address="ul. Test 123",
        metro_station="NDK",
        metro_distance_m=500,
        orientation="South",
        has_balcony=True,
        has_garden=False,
        has_parking=True,
        has_storage=True,
        heating_type="central",
        condition="ready",
        main_image_url="https://example.com/img1.jpg",
        image_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        agency="Test Agency",
        agent_phone="+359888123456",
        listing_date=datetime(2025, 1, 15),
    )


@pytest.fixture
def sample_listing_2():
    """Create a second sample listing for multi-listing tests."""
    return ListingData(
        external_id="TEST456",
        url="https://example.com/listing/TEST456",
        source_site="example.com",
        title="Cozy studio in Mladost",
        description="Perfect for students",
        price_eur=75000.0,
        price_per_sqm_eur=1875.0,
        sqm_total=40.0,
        sqm_net=35.0,
        rooms_count=1,
        bathrooms_count=1,
        floor_number=5,
        floor_total=8,
        has_elevator=True,
        building_type="panel",
        construction_year=1985,
        district="Mladost",
        neighborhood="Mladost 1",
        has_balcony=True,
        condition="renovation",
    )


@pytest.fixture
def sample_listing_updated(sample_listing):
    """Create an updated version of the sample listing (price change)."""
    return ListingData(
        external_id=sample_listing.external_id,
        url=sample_listing.url,
        source_site=sample_listing.source_site,
        title=sample_listing.title,
        description=sample_listing.description,
        price_eur=145000.0,  # Price dropped!
        price_per_sqm_eur=1450.0,
        sqm_total=sample_listing.sqm_total,
        sqm_net=sample_listing.sqm_net,
        rooms_count=sample_listing.rooms_count,
        bathrooms_count=sample_listing.bathrooms_count,
        floor_number=sample_listing.floor_number,
        floor_total=sample_listing.floor_total,
        has_elevator=sample_listing.has_elevator,
        building_type=sample_listing.building_type,
        construction_year=sample_listing.construction_year,
        district=sample_listing.district,
        neighborhood=sample_listing.neighborhood,
    )


# ============================================================================
# SCRAPE → STORE TESTS
# ============================================================================


class TestScrapeToStore:
    """Test that scraping correctly saves data to the database."""

    def test_save_new_listing(self, temp_db, sample_listing):
        """Test saving a new listing to the database."""
        db_path, data_store = temp_db

        # Save the listing
        listing_id = data_store.save_listing(sample_listing)

        # Verify it was saved
        assert listing_id is not None

        # Retrieve and verify
        stored = data_store.get_listing_by_url(sample_listing.url)
        assert stored is not None
        assert stored["external_id"] == sample_listing.external_id
        assert stored["price_eur"] == sample_listing.price_eur
        assert stored["sqm_total"] == sample_listing.sqm_total
        assert stored["district"] == sample_listing.district

    def test_save_listing_all_fields(self, temp_db, sample_listing):
        """Test that all listing fields are saved correctly."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)
        stored = data_store.get_listing_by_url(sample_listing.url)

        # Verify all main fields
        assert stored["title"] == sample_listing.title
        assert stored["description"] == sample_listing.description
        assert stored["price_eur"] == sample_listing.price_eur
        assert stored["price_per_sqm_eur"] == sample_listing.price_per_sqm_eur
        assert stored["sqm_total"] == sample_listing.sqm_total
        assert stored["sqm_net"] == sample_listing.sqm_net
        assert stored["rooms_count"] == sample_listing.rooms_count
        assert stored["bathrooms_count"] == sample_listing.bathrooms_count
        assert stored["floor_number"] == sample_listing.floor_number
        assert stored["floor_total"] == sample_listing.floor_total
        assert stored["has_elevator"] == sample_listing.has_elevator
        assert stored["building_type"] == sample_listing.building_type
        assert stored["construction_year"] == sample_listing.construction_year
        assert stored["district"] == sample_listing.district
        assert stored["neighborhood"] == sample_listing.neighborhood
        assert stored["has_balcony"] == sample_listing.has_balcony
        assert stored["has_parking"] == sample_listing.has_parking
        assert stored["condition"] == sample_listing.condition

    def test_save_multiple_listings(self, temp_db, sample_listing, sample_listing_2):
        """Test saving multiple listings."""
        db_path, data_store = temp_db

        # Save both listings
        id1 = data_store.save_listing(sample_listing)
        id2 = data_store.save_listing(sample_listing_2)

        # Both should have IDs
        assert id1 is not None
        assert id2 is not None
        assert id1 != id2

        # Count should be 2
        count = data_store.get_listing_count()
        assert count == 2

    def test_update_existing_listing(self, temp_db, sample_listing, sample_listing_updated):
        """Test updating an existing listing (same URL)."""
        db_path, data_store = temp_db

        # Save original
        data_store.save_listing(sample_listing)
        original = data_store.get_listing_by_url(sample_listing.url)
        original_price = original["price_eur"]

        # Save updated (same URL)
        data_store.save_listing(sample_listing_updated)
        updated = data_store.get_listing_by_url(sample_listing.url)

        # Price should be updated
        assert updated["price_eur"] == sample_listing_updated.price_eur
        assert updated["price_eur"] != original_price

        # Should still be only 1 listing
        count = data_store.get_listing_count()
        assert count == 1

    def test_save_listing_with_content_hash(self, temp_db, sample_listing):
        """Test saving with content hash for change detection."""
        db_path, data_store = temp_db

        content_hash = "abc123hash"
        data_store.save_listing(sample_listing, content_hash=content_hash)

        stored = data_store.get_listing_by_url(sample_listing.url)
        assert stored["content_hash"] == content_hash

    def test_save_listing_with_price_history(self, temp_db, sample_listing):
        """Test saving with price history."""
        db_path, data_store = temp_db

        price_history = json.dumps([
            {"price": 160000, "date": "2025-01-01"},
            {"price": 150000, "date": "2025-01-15"}
        ])
        data_store.save_listing(sample_listing, price_history=price_history)

        stored = data_store.get_listing_by_url(sample_listing.url)
        assert stored["price_history"] is not None
        history = json.loads(stored["price_history"])
        assert len(history) == 2

    def test_image_urls_stored_as_json(self, temp_db, sample_listing):
        """Test that image URLs are stored as JSON array."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)
        stored = data_store.get_listing_by_url(sample_listing.url)

        # Image URLs should be stored as JSON
        image_urls = json.loads(stored["image_urls"])
        assert len(image_urls) == 2
        assert image_urls[0] == sample_listing.image_urls[0]


# ============================================================================
# STORE → DASHBOARD TESTS
# ============================================================================


class TestStoreToDashboard:
    """Test that dashboard functions correctly read stored data."""

    def test_get_listings_returns_saved_data(self, temp_db, sample_listing, sample_listing_2):
        """Test get_listings returns all saved listings."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)
        data_store.save_listing(sample_listing_2)

        listings = data_store.get_listings()
        assert len(listings) == 2

    def test_get_listings_with_filters(self, temp_db, sample_listing, sample_listing_2):
        """Test get_listings with district filter."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)  # Lozenets
        data_store.save_listing(sample_listing_2)  # Mladost

        # Filter by district
        listings = data_store.get_listings(district="Lozenets")
        assert len(listings) == 1
        assert listings[0]["district"] == "Lozenets"

    def test_get_listings_with_price_range(self, temp_db, sample_listing, sample_listing_2):
        """Test get_listings with price range filter."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)  # 150000
        data_store.save_listing(sample_listing_2)  # 75000

        # Filter by price range
        listings = data_store.get_listings(min_price=100000)
        assert len(listings) == 1
        assert listings[0]["price_eur"] >= 100000

    def test_get_listings_stats(self, temp_db, sample_listing, sample_listing_2):
        """Test get_listings_stats returns correct statistics."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)
        data_store.save_listing(sample_listing_2)

        stats = data_store.get_listings_stats()

        # Check counts
        assert stats["total_active"] == 2

        # Check price stats (avg of 150000 and 75000 = 112500)
        assert stats["price"]["avg"] == 112500.0
        assert stats["price"]["min"] == 75000.0
        assert stats["price"]["max"] == 150000.0

        # Check district breakdown
        assert len(stats["by_district"]) == 2

    def test_get_listing_by_id(self, temp_db, sample_listing):
        """Test getting a specific listing by ID."""
        db_path, data_store = temp_db

        listing_id = data_store.save_listing(sample_listing)
        stored = data_store.get_listing_by_id(listing_id)

        assert stored is not None
        assert stored["url"] == sample_listing.url

    def test_get_listing_count(self, temp_db, sample_listing, sample_listing_2):
        """Test listing count function."""
        db_path, data_store = temp_db

        assert data_store.get_listing_count() == 0

        data_store.save_listing(sample_listing)
        assert data_store.get_listing_count() == 1

        data_store.save_listing(sample_listing_2)
        assert data_store.get_listing_count() == 2

    def test_limit_works(self, temp_db):
        """Test limit parameter works correctly."""
        db_path, data_store = temp_db

        # Create 10 listings
        for i in range(10):
            listing = ListingData(
                external_id=f"TEST{i:03d}",
                url=f"https://example.com/listing/{i}",
                source_site="example.com",
                price_eur=100000 + (i * 10000),
                sqm_total=50 + i,
            )
            data_store.save_listing(listing)

        # Get with limit
        limited = data_store.get_listings(limit=5)
        assert len(limited) == 5

        # Get all (default limit is 100)
        all_listings = data_store.get_listings()
        assert len(all_listings) == 10


# ============================================================================
# FULL PIPELINE TESTS
# ============================================================================


class TestFullPipeline:
    """Test the complete scrape → store → dashboard pipeline."""

    def test_scrape_save_read_pipeline(self, temp_db, sample_listing):
        """Test complete pipeline: save listing, read via dashboard functions."""
        db_path, data_store = temp_db

        # Step 1: Save (simulating scrape result)
        listing_id = data_store.save_listing(sample_listing)
        assert listing_id is not None

        # Step 2: Read via get_listings (dashboard)
        listings = data_store.get_listings()
        assert len(listings) == 1

        dashboard_listing = listings[0]

        # Step 3: Verify data integrity through pipeline
        assert dashboard_listing["external_id"] == sample_listing.external_id
        assert dashboard_listing["url"] == sample_listing.url
        assert dashboard_listing["price_eur"] == sample_listing.price_eur
        assert dashboard_listing["sqm_total"] == sample_listing.sqm_total
        assert dashboard_listing["district"] == sample_listing.district
        assert dashboard_listing["building_type"] == sample_listing.building_type

        # Step 4: Verify stats calculation
        stats = data_store.get_listings_stats()
        assert stats["total_active"] == 1
        assert stats["price"]["avg"] == sample_listing.price_eur

    def test_multi_listing_pipeline(self, temp_db, sample_listing, sample_listing_2):
        """Test pipeline with multiple listings."""
        db_path, data_store = temp_db

        # Save both listings
        data_store.save_listing(sample_listing)
        data_store.save_listing(sample_listing_2)

        # Read all
        listings = data_store.get_listings()
        assert len(listings) == 2

        # Verify stats aggregate correctly
        stats = data_store.get_listings_stats()
        assert stats["total_active"] == 2

        # Average should be correct
        expected_avg = (sample_listing.price_eur + sample_listing_2.price_eur) / 2
        assert stats["price"]["avg"] == expected_avg

    def test_filter_pipeline(self, temp_db, sample_listing, sample_listing_2):
        """Test pipeline with filtering."""
        db_path, data_store = temp_db

        data_store.save_listing(sample_listing)  # Lozenets, 150k
        data_store.save_listing(sample_listing_2)  # Mladost, 75k

        # Filter by district
        lozenets_listings = data_store.get_listings(district="Lozenets")
        assert len(lozenets_listings) == 1
        assert lozenets_listings[0]["price_eur"] == 150000.0

        # Filter by price
        cheap_listings = data_store.get_listings(max_price=100000)
        assert len(cheap_listings) == 1
        assert cheap_listings[0]["district"] == "Mladost"

    def test_update_pipeline(self, temp_db, sample_listing, sample_listing_updated):
        """Test update detection through pipeline."""
        db_path, data_store = temp_db

        # Save original
        data_store.save_listing(sample_listing, content_hash="hash1")

        original = data_store.get_listings()[0]
        assert original["price_eur"] == 150000.0

        # Update with new price
        data_store.save_listing(sample_listing_updated, content_hash="hash2")

        updated = data_store.get_listings()[0]
        assert updated["price_eur"] == 145000.0

        # Should still be 1 listing
        assert data_store.get_listing_count() == 1


# ============================================================================
# CHANGE DETECTION TESTS
# ============================================================================


class TestChangeDetection:
    """Test change detection integration with pipeline."""

    def test_content_hash_change_detection(self, temp_db, sample_listing):
        """Test that content hash enables change detection."""
        db_path, data_store = temp_db

        # Save with hash
        data_store.save_listing(sample_listing, content_hash="original_hash")
        stored1 = data_store.get_listing_by_url(sample_listing.url)

        # Update with same hash (no change)
        data_store.save_listing(sample_listing, content_hash="original_hash")
        stored2 = data_store.get_listing_by_url(sample_listing.url)

        # Hash should be the same
        assert stored1["content_hash"] == stored2["content_hash"]

    def test_price_history_tracking(self, temp_db, sample_listing):
        """Test price history is tracked correctly."""
        db_path, data_store = temp_db

        # Initial save
        history1 = json.dumps([{"price": 150000, "date": "2025-01-01"}])
        data_store.save_listing(sample_listing, price_history=history1)

        # Verify history stored
        stored = data_store.get_listing_by_url(sample_listing.url)
        history = json.loads(stored["price_history"])
        assert len(history) == 1
        assert history[0]["price"] == 150000


# ============================================================================
# SESSION REPORT TESTS
# ============================================================================


class TestSessionReports:
    """Test session report generation."""

    def test_metrics_collector_integration(self):
        """Test MetricsCollector records data correctly."""
        from scraping.metrics import MetricsCollector, RequestStatus

        metrics = MetricsCollector()

        # Record some requests
        metrics.record_request("http://example.com/1", "example.com")
        metrics.record_response("http://example.com/1", RequestStatus.SUCCESS, 150.0)

        metrics.record_request("http://example.com/2", "example.com")
        metrics.record_response("http://example.com/2", RequestStatus.FAILED, 3000.0, error_type="timeout")

        # End run and check stats
        run_metrics = metrics.end_run()

        assert run_metrics.total_requests == 2
        assert run_metrics.successful == 1
        assert run_metrics.failed == 1

    def test_session_report_generator(self, tmp_path):
        """Test SessionReportGenerator creates reports."""
        from scraping.metrics import MetricsCollector, RequestStatus
        from scraping.session_report import SessionReportGenerator

        # Create metrics
        metrics = MetricsCollector()
        metrics.record_request("http://example.com/1", "example.com")
        metrics.record_response("http://example.com/1", RequestStatus.SUCCESS, 100.0)
        metrics.record_listing_saved("http://example.com/1", "http://example.com/1")
        run_metrics = metrics.end_run()

        # Generate report
        report_gen = SessionReportGenerator(tmp_path)
        report = report_gen.generate(
            metrics=run_metrics,
            proxy_stats={"total_proxies": 10, "average_score": 0.85},
            circuit_states={"example.com": "closed"}
        )

        # Verify report structure (SessionReport is a dataclass)
        assert hasattr(report, "run_id")
        assert hasattr(report, "total_urls")
        assert hasattr(report, "successful")

        # Save and verify file created
        report_path = report_gen.save(report)
        assert report_path.exists()

    def test_report_contains_correct_metrics(self, tmp_path):
        """Test report contains expected metrics."""
        from scraping.metrics import MetricsCollector, RequestStatus
        from scraping.session_report import SessionReportGenerator

        metrics = MetricsCollector()

        # Simulate a scraping session
        for i in range(5):
            url = f"http://example.com/{i}"
            metrics.record_request(url, "example.com")
            if i < 4:  # 4 success, 1 fail
                metrics.record_response(url, RequestStatus.SUCCESS, 100.0)
                metrics.record_listing_saved(url, url)
            else:
                metrics.record_response(url, RequestStatus.FAILED, 3000.0)

        run_metrics = metrics.end_run()

        # Generate report (SessionReport is a dataclass)
        report_gen = SessionReportGenerator(tmp_path)
        report = report_gen.generate(metrics=run_metrics)

        # Verify metrics (accessing dataclass attributes)
        assert report.total_urls == 5
        assert report.successful == 4
        assert report.failed == 1


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_database(self, temp_db):
        """Test operations on empty database."""
        db_path, data_store = temp_db

        # All these should work on empty DB
        assert data_store.get_listing_count() == 0
        assert data_store.get_listings() == []

        stats = data_store.get_listings_stats()
        assert stats["total_active"] == 0

    def test_listing_with_minimal_fields(self, temp_db):
        """Test saving listing with only required fields."""
        db_path, data_store = temp_db

        minimal_listing = ListingData(
            external_id="MIN001",
            url="https://example.com/minimal",
            source_site="example.com",
        )

        listing_id = data_store.save_listing(minimal_listing)
        assert listing_id is not None

        stored = data_store.get_listing_by_url(minimal_listing.url)
        assert stored is not None
        assert stored["external_id"] == "MIN001"

    def test_listing_with_unicode(self, temp_db):
        """Test saving listing with Bulgarian text."""
        db_path, data_store = temp_db

        bulgarian_listing = ListingData(
            external_id="BG001",
            url="https://example.com/bulgarian",
            source_site="example.com",
            title="Тристаен апартамент в София",
            description="Просторен апартамент с красива гледка",
            district="Лозенец",
            neighborhood="Център",
        )

        data_store.save_listing(bulgarian_listing)
        stored = data_store.get_listing_by_url(bulgarian_listing.url)

        assert stored["title"] == "Тристаен апартамент в София"
        assert stored["district"] == "Лозенец"

    def test_listing_with_special_characters_in_url(self, temp_db):
        """Test URL with query parameters."""
        db_path, data_store = temp_db

        listing = ListingData(
            external_id="URL001",
            url="https://example.com/listing?id=123&view=full",
            source_site="example.com",
        )

        data_store.save_listing(listing)
        stored = data_store.get_listing_by_url(listing.url)

        assert stored is not None
        assert stored["url"] == listing.url

    def test_large_description(self, temp_db):
        """Test saving listing with large description."""
        db_path, data_store = temp_db

        large_description = "A" * 10000  # 10KB description

        listing = ListingData(
            external_id="LARGE001",
            url="https://example.com/large",
            source_site="example.com",
            description=large_description,
        )

        data_store.save_listing(listing)
        stored = data_store.get_listing_by_url(listing.url)

        assert len(stored["description"]) == 10000

    def test_nonexistent_listing(self, temp_db):
        """Test getting nonexistent listing returns None."""
        db_path, data_store = temp_db

        result = data_store.get_listing_by_url("https://nonexistent.com/fake")
        assert result is None

        result = data_store.get_listing_by_id(99999)
        assert result is None


# ============================================================================
# DATA INTEGRITY TESTS
# ============================================================================


class TestDataIntegrity:
    """Test data integrity through the pipeline."""

    def test_boolean_fields_preserved(self, temp_db):
        """Test boolean fields are preserved correctly."""
        db_path, data_store = temp_db

        listing = ListingData(
            external_id="BOOL001",
            url="https://example.com/bool",
            source_site="example.com",
            has_elevator=True,
            has_balcony=True,
            has_garden=False,
            has_parking=False,
        )

        data_store.save_listing(listing)
        stored = data_store.get_listing_by_url(listing.url)

        assert stored["has_elevator"] == True
        assert stored["has_balcony"] == True
        assert stored["has_garden"] == False
        assert stored["has_parking"] == False

    def test_numeric_precision(self, temp_db):
        """Test numeric values preserve precision."""
        db_path, data_store = temp_db

        listing = ListingData(
            external_id="NUM001",
            url="https://example.com/num",
            source_site="example.com",
            price_eur=123456.78,
            price_per_sqm_eur=1234.56,
            sqm_total=99.5,
            sqm_net=85.25,
        )

        data_store.save_listing(listing)
        stored = data_store.get_listing_by_url(listing.url)

        assert stored["price_eur"] == 123456.78
        assert stored["price_per_sqm_eur"] == 1234.56
        assert stored["sqm_total"] == 99.5
        assert stored["sqm_net"] == 85.25

    def test_null_fields_handled(self, temp_db):
        """Test None values are stored as NULL."""
        db_path, data_store = temp_db

        listing = ListingData(
            external_id="NULL001",
            url="https://example.com/null",
            source_site="example.com",
            # All optional fields are None by default
        )

        data_store.save_listing(listing)
        stored = data_store.get_listing_by_url(listing.url)

        assert stored["price_eur"] is None
        assert stored["district"] is None
        assert stored["has_elevator"] is None
