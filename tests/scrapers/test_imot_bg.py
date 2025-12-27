"""
Tests for imot.bg scraper.

Tests all extraction methods including:
- URL extraction from search results
- Field extraction from listing pages
- Pagination detection and URL building
- Data normalization and schema validation
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from websites.imot_bg.imot_scraper import ImotBgScraper
from websites.base_scraper import ListingData


@pytest.fixture
def scraper():
    """Create an ImotBgScraper instance for testing."""
    return ImotBgScraper()


# =============================================================================
# SEARCH RESULTS EXTRACTION TESTS
# =============================================================================

def test_extract_listing_urls(scraper, imot_search_html):
    """
    Test extraction of listing URLs from search results page.

    Should extract all valid listing URLs and normalize them to absolute URLs.
    """
    urls = scraper.extract_search_results(imot_search_html)

    # Should find listing URLs
    assert len(urls) > 0, "Should extract at least one listing URL"

    # All URLs should be absolute
    for url in urls:
        assert url.startswith("http"), f"URL should be absolute: {url}"

    # URLs should contain listing patterns
    for url in urls:
        assert "/obiava-" in url, f"URL should contain '/obiava-': {url}"


# =============================================================================
# LISTING DATA EXTRACTION TESTS
# =============================================================================

def test_extract_listing_data(scraper, imot_listing_html):
    """
    Test extraction of all fields from a listing page.

    Should extract:
    - Basic fields (ID, title, description)
    - Price and size (EUR, sqm, price per sqm)
    - Layout (rooms, bathrooms, floor)
    - Building info (type, year, act status)
    - Location (district, neighborhood, metro)
    - Features (elevator, balcony, parking, etc.)
    - Media (images)
    - Contact info
    """
    url = "https://www.imot.bg/obiava-123-prodava-tristaen-centar"
    listing = scraper.extract_listing(imot_listing_html, url)

    assert listing is not None, "Should extract listing data"
    assert isinstance(listing, ListingData), "Should return ListingData object"

    # Basic fields
    assert listing.external_id == "123", "Should extract ID from URL"
    assert listing.url == url, "Should set URL"
    assert listing.source_site == "imot.bg", "Should set source site"

    # Required fields should be present
    assert listing.title is not None, "Should extract title"


def test_normalize_to_schema(scraper, imot_listing_html):
    """
    Test that extracted data matches ListingData schema.

    Should:
    - Return ListingData instance
    - Have all required fields
    - Have correct data types
    - Convert values to standard formats
    """
    url = "https://www.imot.bg/obiava-456-prodava-dvustaen-lozenets"
    listing = scraper.extract_listing(imot_listing_html, url)

    assert isinstance(listing, ListingData), "Should return ListingData instance"

    # Required fields should be strings
    assert isinstance(listing.external_id, str), "external_id should be string"
    assert isinstance(listing.url, str), "url should be string"
    assert isinstance(listing.source_site, str), "source_site should be string"

    # Numeric fields should be float or None
    if listing.price_eur is not None:
        assert isinstance(listing.price_eur, float), "price_eur should be float"
    if listing.sqm_total is not None:
        assert isinstance(listing.sqm_total, float), "sqm_total should be float"

    # Integer fields should be int or None
    if listing.rooms_count is not None:
        assert isinstance(listing.rooms_count, int), "rooms_count should be int"
    if listing.floor_number is not None:
        assert isinstance(listing.floor_number, int), "floor_number should be int"

    # Boolean fields should be bool or None
    if listing.has_elevator is not None:
        assert isinstance(listing.has_elevator, bool), "has_elevator should be bool"


# =============================================================================
# PRICE EXTRACTION TESTS
# =============================================================================

def test_price_extraction_eur_with_spaces(scraper):
    """Test extracting EUR price with spaces: '150 000 EUR'"""
    text = "Цена: 150 000 EUR"
    price = scraper._extract_price_eur(text)
    assert price == 150000.0, f"Should extract 150000.0, got {price}"


def test_price_extraction_eur_no_spaces(scraper):
    """Test extracting EUR price without spaces: '150000 EUR'"""
    text = "Цена: 150000 EUR"
    price = scraper._extract_price_eur(text)
    assert price == 150000.0, f"Should extract 150000.0, got {price}"


def test_price_extraction_euro_symbol(scraper):
    """Test extracting EUR price with € symbol: '150000€'"""
    text = "Цена: 150000€"
    price = scraper._extract_price_eur(text)
    assert price == 150000.0, f"Should extract 150000.0, got {price}"


def test_price_extraction_multiple_prices(scraper):
    """Test extracting first EUR price when multiple prices present"""
    text = "Цена: 150 000 EUR (беше 160 000 EUR)"
    price = scraper._extract_price_eur(text)
    assert price == 150000.0, f"Should extract first price 150000.0, got {price}"


# =============================================================================
# SQM EXTRACTION TESTS
# =============================================================================

def test_sqm_extraction_bulgarian(scraper):
    """Test extracting square meters in Bulgarian format: '115 кв.м'"""
    text = "Площ: 115 кв.м"
    sqm = scraper._extract_sqm(text)
    assert sqm == 115.0, f"Should extract 115.0, got {sqm}"


def test_sqm_extraction_decimal(scraper):
    """Test extracting square meters with decimal: '115.5 кв.м'"""
    text = "Площ: 115.5 кв.м"
    sqm = scraper._extract_sqm(text)
    assert sqm == 115.5, f"Should extract 115.5, got {sqm}"


def test_sqm_extraction_m2_symbol(scraper):
    """Test extracting square meters with m² symbol: '115 m²'"""
    text = "Площ: 115 m²"
    sqm = scraper._extract_sqm(text)
    assert sqm == 115.0, f"Should extract 115.0, got {sqm}"


# =============================================================================
# FLOOR EXTRACTION TESTS
# =============================================================================

def test_floor_extraction_full(scraper):
    """Test extracting floor number and total: 'Етаж 3 от 6'"""
    text = "Етаж 3 от 6"
    floor_number, floor_total = scraper._extract_floor_info(text)
    assert floor_number == 3, f"Should extract floor 3, got {floor_number}"
    assert floor_total == 6, f"Should extract total 6, got {floor_total}"


def test_floor_extraction_slash_format(scraper):
    """Test extracting floor with slash format: '3/6'"""
    text = "Етаж: 3/6"
    floor_number, floor_total = scraper._extract_floor_info(text)
    assert floor_number == 3, f"Should extract floor 3, got {floor_number}"
    assert floor_total == 6, f"Should extract total 6, got {floor_total}"


def test_floor_extraction_only_number(scraper):
    """Test extracting floor when only number given: 'Етаж 3'"""
    text = "Етаж 3"
    floor_number, floor_total = scraper._extract_floor_info(text)
    assert floor_number == 3, f"Should extract floor 3, got {floor_number}"
    assert floor_total is None, f"Should return None for total, got {floor_total}"


# =============================================================================
# ROOMS EXTRACTION TESTS
# =============================================================================

def test_rooms_extraction_from_url_tristaen(scraper):
    """Test extracting room count from URL with 'тристаен'"""
    url = "https://www.imot.bg/obiava-123-prodava-tristaen-centar"
    rooms = scraper._extract_rooms_from_url(url)
    assert rooms == 3, f"Should extract 3 rooms from 'tristaen', got {rooms}"


def test_rooms_extraction_from_url_dvustaen(scraper):
    """Test extracting room count from URL with 'двустаен'"""
    url = "https://www.imot.bg/obiava-456-prodava-dvustaen-lozenets"
    rooms = scraper._extract_rooms_from_url(url)
    assert rooms == 2, f"Should extract 2 rooms from 'dvustaen', got {rooms}"


def test_rooms_extraction_from_text_bulgarian(scraper):
    """Test extracting room count from Bulgarian text"""
    text = "Тристаен апартамент в центъра"
    rooms = scraper._parse_rooms(text)
    assert rooms == 3, f"Should extract 3 rooms from text, got {rooms}"


def test_rooms_extraction_from_text_numeric(scraper):
    """Test extracting room count from numeric pattern: '3-стаен'"""
    text = "3-стаен апартамент"
    rooms = scraper._parse_rooms(text)
    assert rooms == 3, f"Should extract 3 rooms from '3-staen', got {rooms}"


# =============================================================================
# PAGINATION DETECTION TESTS
# =============================================================================

def test_pagination_detection_has_next(scraper, imot_search_html):
    """Test is_last_page() returns False when next page exists"""
    is_last = scraper.is_last_page(imot_search_html, current_page=1)
    assert is_last is False, "Should detect next page exists"


def test_pagination_detection_no_results(scraper):
    """Test is_last_page() returns True when no results message present"""
    html = "<html><body>Няма намерени обяви</body></html>"
    is_last = scraper.is_last_page(html, current_page=1)
    assert is_last is True, "Should detect 'no results' message"


def test_pagination_detection_no_listings(scraper):
    """Test is_last_page() returns True when no listing links found"""
    html = "<html><body><div>Nothing here</div></body></html>"
    is_last = scraper.is_last_page(html, current_page=5)
    assert is_last is True, "Should detect no listings on page"


# =============================================================================
# PAGINATION URL BUILDING TESTS
# =============================================================================

def test_pagination_url_build_page_2(scraper):
    """Test building URL for page 2 from page 1"""
    current_url = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya"
    next_url = scraper.get_next_page_url(current_url, current_page=1)
    expected = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/p-2"
    assert next_url == expected, f"Should build page 2 URL, got {next_url}"


def test_pagination_url_build_page_3(scraper):
    """Test building URL for page 3 from page 2"""
    current_url = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/p-2"
    next_url = scraper.get_next_page_url(current_url, current_page=2)
    expected = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/p-3"
    assert next_url == expected, f"Should build page 3 URL, got {next_url}"


def test_pagination_url_build_with_query_params(scraper):
    """Test building pagination URL preserves query parameters"""
    current_url = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya?sort=price"
    next_url = scraper.get_next_page_url(current_url, current_page=1)
    expected = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya/p-2?sort=price"
    assert next_url == expected, f"Should preserve query params, got {next_url}"
