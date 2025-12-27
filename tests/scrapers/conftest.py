"""
Shared pytest fixtures for scraper tests.

Provides:
- Sample ListingData objects
- HTML fixtures for testing extractors
- Helper functions for loading fixture files
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from websites.base_scraper import ListingData


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_listing() -> ListingData:
    """
    Create a sample ListingData object for testing.

    Returns:
        Complete ListingData object with all fields populated
    """
    return ListingData(
        external_id="12345",
        url="https://www.imot.bg/obiava-12345-prodava-tristaen-centar",
        source_site="imot.bg",
        title="Тристаен апартамент в Центъра",
        description="Светъл тристаен апартамент с južна ориентация",
        price_eur=150000.0,
        price_per_sqm_eur=1500.0,
        sqm_total=100.0,
        sqm_net=85.0,
        rooms_count=3,
        bathrooms_count=1,
        floor_number=3,
        floor_total=6,
        has_elevator=True,
        building_type="brick",
        construction_year=2010,
        act_status="act16",
        district="София",
        neighborhood="Център",
        metro_station="Сердика",
        metro_distance_m=500,
        orientation="S/E",
        has_balcony=True,
        has_garden=False,
        has_parking=True,
        has_storage=False,
        heating_type="central",
        condition="ready",
        image_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        main_image_url="https://example.com/img1.jpg",
        agency="Sample Agency",
        agent_name="John Doe",
        agent_phone="+359888123456",
        listing_date=datetime(2025, 1, 1),
        scraped_at=datetime(2025, 1, 15),
        features=["elevator", "balcony", "parking"],
        fingerprint="abc123def456",
    )


# =============================================================================
# HTML FIXTURES (IMOT.BG)
# =============================================================================

@pytest.fixture
def imot_search_html() -> str:
    """
    Placeholder HTML for imot.bg search results page.

    Contains minimal structure to test URL extraction and pagination.
    Will be replaced with real HTML fixtures later.
    """
    return """
    <html>
    <body>
        <div class="results">
            <a href="/obiava-123-prodava-tristaen-centar">Тристаен апартамент</a>
            <a href="/obiava-456-prodava-dvustaen-studentski-grad">Двустаен апартамент</a>
            <a href="/obiava-789-prodava-ednostaen-lozenets">Едностаен апартамент</a>
        </div>
        <div class="pagination">
            <a href="/obiavi/prodazhbi/grad-sofiya/p-2">2</a>
            <a href="/obiavi/prodazhbi/grad-sofiya/p-3">3</a>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def imot_listing_html() -> str:
    """
    Placeholder HTML for imot.bg listing page.

    Contains minimal structure to test data extraction patterns.
    Will be replaced with real HTML fixtures later.
    """
    return """
    <html>
    <body>
        <h1>Тристаен апартамент в Център</h1>
        <div class="price">150 000 EUR</div>
        <div class="info">
            <span>115 кв.м</span>
            <span>Етаж 3 от 6</span>
            <span>Тухла</span>
            <span>Южна ориентация</span>
        </div>
        <div class="description">
            Светъл тристаен апартамент с балкон и паркинг.
            Централно отопление. Асансьор.
        </div>
        <img src="https://imot.bg/images/listing123_1.jpg">
        <img src="https://imot.bg/images/listing123_2.jpg">
    </body>
    </html>
    """


# =============================================================================
# HTML FIXTURES (BAZAR.BG)
# =============================================================================

@pytest.fixture
def bazar_search_html() -> str:
    """
    Placeholder HTML for bazar.bg search results page.

    Contains minimal structure to test URL extraction and pagination.
    Will be replaced with real HTML fixtures later.
    """
    return """
    <html>
    <body>
        <div class="listItemContainer listItemContainerV2">
            <a class="listItemLink" href="/obiava-111/tristaen-apartament-centar">Тристаен</a>
        </div>
        <div class="listItemContainer listItemContainerV2">
            <a class="listItemLink" href="/obiava-222/dvustaen-apartament-studentski-grad">Двустаен</a>
        </div>
        <div class="listItemContainer listItemContainerV2">
            <a class="listItemLink" href="/obiava-333/ednostaen-apartament-lozenets">Едностаен</a>
        </div>
        <div class="pagination">
            <a href="?page=2">Следваща »</a>
        </div>
        <script>
            var maxPage = 5;
        </script>
    </body>
    </html>
    """


@pytest.fixture
def bazar_listing_html() -> str:
    """
    Placeholder HTML for bazar.bg listing page.

    Contains minimal structure to test data extraction patterns.
    Will be replaced with real HTML fixtures later.
    """
    return """
    <html>
    <body>
        <h1>Тристаен апартамент - Център</h1>
        <script>
            var adPrice = "293374.5";
            var adCurrency = "лв";
        </script>
        <div class="details">
            <span>Площ: 100 кв.м</span>
            <span>Етаж: 4 от 8</span>
            <span>Панел</span>
            <span>Източна ориентация</span>
        </div>
        <div class="description">
            Двустаен апартамент с тераса. Има лифт и мазе.
            Топлофикация. Година на строителство: 2015.
        </div>
        <img src="https://bazar.bg/img/listing111_1.jpg">
    </body>
    </html>
    """


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_html_fixture(filename: str) -> str:
    """
    Load HTML fixture from the fixtures directory.

    Args:
        filename: Name of the fixture file (e.g., "imot_search_page1.html")

    Returns:
        HTML content as string

    Raises:
        FileNotFoundError: If fixture file doesn't exist

    Example:
        >>> html = load_html_fixture("imot_search_page1.html")
    """
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_path = fixture_dir / filename

    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture file not found: {fixture_path}\n"
            f"Please add the HTML fixture to {fixture_dir}"
        )

    return fixture_path.read_text(encoding="utf-8")


def save_html_fixture(filename: str, html: str) -> Path:
    """
    Save HTML content as a fixture file.

    Useful for capturing real pages during development.

    Args:
        filename: Name for the fixture file (e.g., "imot_search_page1.html")
        html: HTML content to save

    Returns:
        Path to the saved fixture file

    Example:
        >>> path = save_html_fixture("imot_listing_123.html", response.text)
    """
    fixture_dir = Path(__file__).parent / "fixtures"
    fixture_dir.mkdir(exist_ok=True)

    fixture_path = fixture_dir / filename
    fixture_path.write_text(html, encoding="utf-8")

    return fixture_path
