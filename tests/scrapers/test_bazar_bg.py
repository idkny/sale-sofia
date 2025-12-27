"""
Tests for bazar.bg scraper.

Tests all extraction methods including:
- URL extraction from search results
- Field extraction from listing pages
- Pagination detection and URL building
- Data normalization and schema validation
- BGN to EUR conversion
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from websites.bazar_bg.bazar_scraper import BazarBgScraper
from websites.base_scraper import ListingData


@pytest.fixture
def scraper():
    """Create a BazarBgScraper instance for testing."""
    return BazarBgScraper()


# =============================================================================
# SEARCH RESULTS EXTRACTION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_extract_listing_urls(scraper, bazar_search_html):
    """
    Test extraction of listing URLs from search results page.

    Should extract all valid listing URLs and normalize them to absolute URLs.
    """
    urls = await scraper.extract_search_results(bazar_search_html)

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

@pytest.mark.asyncio
async def test_extract_listing_data(scraper, bazar_listing_html):
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
    url = "https://bazar.bg/obiava-111/tristaen-apartament-centar"
    listing = await scraper.extract_listing(bazar_listing_html, url)

    assert listing is not None, "Should extract listing data"
    assert isinstance(listing, ListingData), "Should return ListingData object"

    # Basic fields
    assert listing.external_id == "111", "Should extract ID from URL"
    assert listing.url == url, "Should set URL"
    assert listing.source_site == "bazar.bg", "Should set source site"

    # Required fields should be present
    assert listing.title is not None, "Should extract title"


@pytest.mark.asyncio
async def test_normalize_to_schema(scraper, bazar_listing_html):
    """
    Test that extracted data matches ListingData schema.

    Should:
    - Return ListingData instance
    - Have all required fields
    - Have correct data types
    - Convert values to standard formats
    """
    url = "https://bazar.bg/obiava-222/dvustaen-apartament-studentski-grad"
    listing = await scraper.extract_listing(bazar_listing_html, url)

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
# PRICE EXTRACTION TESTS (BGN to EUR conversion)
# =============================================================================

def test_price_extraction_bgn_js_variable(scraper):
    """Test extracting BGN price from JavaScript and converting to EUR"""
    html = """
    <html>
    <script>
        var adPrice = "195583";
        var adCurrency = "лв";
    </script>
    <body>Price info</body>
    </html>
    """
    text = "Price info"
    price = scraper._extract_price_eur(html, text)
    # 195583 BGN / 1.95583 = 100000 EUR (approximately)
    assert price is not None, "Should extract price"
    assert 99900 <= price <= 100100, f"Should convert to ~100000 EUR, got {price}"


def test_price_extraction_eur_js_variable(scraper):
    """Test extracting EUR price from JavaScript (no conversion)"""
    html = """
    <html>
    <script>
        var adPrice = "150000";
        var adCurrency = "€";
    </script>
    <body>Price info</body>
    </html>
    """
    text = "Price info"
    price = scraper._extract_price_eur(html, text)
    assert price == 150000.0, f"Should extract 150000.0 EUR, got {price}"


def test_price_extraction_text_fallback(scraper):
    """Test extracting price from text when JS not available"""
    html = "<html><body>Цена: 150000 EUR</body></html>"
    text = "Цена: 150000 EUR"
    price = scraper._extract_price_eur(html, text)
    assert price == 150000.0, f"Should extract 150000.0 EUR from text, got {price}"


# =============================================================================
# SQM EXTRACTION TESTS
# =============================================================================

def test_sqm_extraction_bulgarian(scraper):
    """Test extracting square meters in Bulgarian format: '100 кв.м'"""
    text = "Площ: 100 кв.м"
    sqm = scraper._extract_sqm(text)
    assert sqm == 100.0, f"Should extract 100.0, got {sqm}"


def test_sqm_extraction_decimal(scraper):
    """Test extracting square meters with decimal: '100.5 кв.м'"""
    text = "Площ: 100.5 кв.м"
    sqm = scraper._extract_sqm(text)
    assert sqm == 100.5, f"Should extract 100.5, got {sqm}"


def test_sqm_extraction_m2_symbol(scraper):
    """Test extracting square meters with m² symbol: '100 m²'"""
    text = "Площ: 100 m²"
    sqm = scraper._extract_sqm(text)
    assert sqm == 100.0, f"Should extract 100.0, got {sqm}"


# =============================================================================
# FLOOR EXTRACTION TESTS
# =============================================================================

def test_floor_extraction_full(scraper):
    """Test extracting floor number and total: 'Етаж 4 от 8'"""
    text = "Етаж 4 от 8"
    floor_number, floor_total = scraper._extract_floor_info(text)
    assert floor_number == 4, f"Should extract floor 4, got {floor_number}"
    assert floor_total == 8, f"Should extract total 8, got {floor_total}"


def test_floor_extraction_slash_format(scraper):
    """Test extracting floor with slash format: '4/8'"""
    text = "Етаж: 4/8"
    floor_number, floor_total = scraper._extract_floor_info(text)
    assert floor_number == 4, f"Should extract floor 4, got {floor_number}"
    assert floor_total == 8, f"Should extract total 8, got {floor_total}"


def test_floor_extraction_only_number(scraper):
    """Test extracting floor when only number given: 'Етаж 4'"""
    text = "Етаж 4"
    floor_number, floor_total = scraper._extract_floor_info(text)
    assert floor_number == 4, f"Should extract floor 4, got {floor_number}"
    assert floor_total is None, f"Should return None for total, got {floor_total}"


# =============================================================================
# ROOMS EXTRACTION TESTS
# =============================================================================

def test_rooms_extraction_from_url_tristaen(scraper):
    """Test extracting room count from URL with 'тристаен'"""
    url = "https://bazar.bg/obiava-111/tristaen-apartament-centar"
    rooms = scraper._extract_rooms_from_url(url)
    assert rooms == 3, f"Should extract 3 rooms from 'tristaen', got {rooms}"


def test_rooms_extraction_from_url_dvustaen(scraper):
    """Test extracting room count from URL with 'двустаен'"""
    url = "https://bazar.bg/obiava-222/dvustaen-apartament-studentski-grad"
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

def test_pagination_detection_has_next(scraper, bazar_search_html):
    """Test is_last_page() returns False when next page exists"""
    is_last = scraper.is_last_page(bazar_search_html, current_page=1)
    assert is_last is False, "Should detect next page exists"


def test_pagination_detection_max_page_reached(scraper):
    """Test is_last_page() returns True when current page >= maxPage"""
    html = """
    <html>
    <script>var maxPage = 5;</script>
    <body>
        <a href="/obiava-111/listing">Listing</a>
    </body>
    </html>
    """
    is_last = scraper.is_last_page(html, current_page=5)
    assert is_last is True, "Should detect page 5 is max page"


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
    current_url = "https://bazar.bg/obiavi/apartamenti/sofia"
    next_url = scraper.get_next_page_url(current_url, current_page=1)
    expected = "https://bazar.bg/obiavi/apartamenti/sofia?page=2"
    assert next_url == expected, f"Should build page 2 URL, got {next_url}"


def test_pagination_url_build_page_3(scraper):
    """Test building URL for page 3 from page 2"""
    current_url = "https://bazar.bg/obiavi/apartamenti/sofia?page=2"
    next_url = scraper.get_next_page_url(current_url, current_page=2)
    expected = "https://bazar.bg/obiavi/apartamenti/sofia?page=3"
    assert next_url == expected, f"Should build page 3 URL, got {next_url}"


def test_pagination_url_build_with_other_params(scraper):
    """Test building pagination URL preserves other query parameters"""
    current_url = "https://bazar.bg/obiavi/apartamenti/sofia?sort=price"
    next_url = scraper.get_next_page_url(current_url, current_page=1)
    expected = "https://bazar.bg/obiavi/apartamenti/sofia?sort=price&page=2"
    assert next_url == expected, f"Should preserve other params, got {next_url}"
