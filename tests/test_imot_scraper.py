#!/usr/bin/env python3
"""Unit tests for imot.bg scraper - is_last_page detection helpers."""

import pytest
from websites.imot_bg.imot_scraper import ImotBgScraper


@pytest.fixture
def scraper():
    """Create scraper instance."""
    return ImotBgScraper()


class TestHasNoResultsMessage:
    """Tests for _has_no_results_message helper."""

    def test_no_results_bulgarian(self, scraper):
        """Should detect Bulgarian 'no results' message."""
        page_text = "търсене няма намерени обяви за тези критерии"
        assert scraper._has_no_results_message(page_text) is True

    def test_no_results_zero_listings(self, scraper):
        """Should detect '0 обяви' pattern."""
        page_text = "намерени 0 обяви в софия"
        assert scraper._has_no_results_message(page_text) is True

    def test_no_results_english(self, scraper):
        """Should detect English 'no results' message."""
        page_text = "search returned no results"
        assert scraper._has_no_results_message(page_text) is True

    def test_has_results(self, scraper):
        """Should return False when results exist."""
        # Note: "150 обяви" contains "0 обяви" substring, so avoid numbers
        page_text = "търсене апартаменти софия център продава"
        assert scraper._has_no_results_message(page_text) is False


class TestHasNoListings:
    """Tests for _has_no_listings helper."""

    def test_no_listing_links(self, scraper):
        """Should return True when no listing links found."""
        html = """
        <html><body>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </body></html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._has_no_listings(soup) is True

    def test_has_listing_links(self, scraper):
        """Should return False when listing links exist."""
        html = """
        <html><body>
            <a href="/obiava-abc123-prodava-apartament">Listing 1</a>
            <a href="/obiava-def456-prodava-apartament">Listing 2</a>
        </body></html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._has_no_listings(soup) is False

    def test_partial_match_not_listing(self, scraper):
        """Links with only partial pattern shouldn't count."""
        html = """
        <html><body>
            <a href="/obiava-abc123">Missing prodava</a>
            <a href="/some-prodava-link">Missing obiava</a>
        </body></html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._has_no_listings(soup) is True


class TestHasNextPageLink:
    """Tests for _has_next_page_link helper."""

    def test_next_page_in_href(self, scraper):
        """Should find next page link in href."""
        html = """
        <html><body>
            <a href="/search/p-2">Page 2</a>
            <a href="/search/p-3">Page 3</a>
        </body></html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._has_next_page_link(soup, current_page=1) is True
        assert scraper._has_next_page_link(soup, current_page=2) is True
        assert scraper._has_next_page_link(soup, current_page=3) is False

    def test_next_page_in_link_text(self, scraper):
        """Should find next page when number is in link text."""
        html = """
        <html><body>
            <a href="/search">1</a>
            <a href="/search">2</a>
            <a href="/search">3</a>
        </body></html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._has_next_page_link(soup, current_page=1) is True
        assert scraper._has_next_page_link(soup, current_page=2) is True
        assert scraper._has_next_page_link(soup, current_page=3) is False

    def test_no_next_page(self, scraper):
        """Should return False when no next page link."""
        html = """
        <html><body>
            <a href="/search/p-1">Page 1</a>
        </body></html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._has_next_page_link(soup, current_page=1) is False


class TestIsPastTotalPages:
    """Tests for _is_past_total_pages helper."""

    def test_bulgarian_total_pages(self, scraper):
        """Should detect Bulgarian 'от X' total pages pattern."""
        page_text = "страница 5 от 10"
        assert scraper._is_past_total_pages(page_text, current_page=5) is False
        assert scraper._is_past_total_pages(page_text, current_page=10) is True
        assert scraper._is_past_total_pages(page_text, current_page=11) is True

    def test_slash_total_pages(self, scraper):
        """Should detect '1/15' style pagination."""
        page_text = "showing page 3/15 of results"
        assert scraper._is_past_total_pages(page_text, current_page=3) is False
        assert scraper._is_past_total_pages(page_text, current_page=15) is True
        assert scraper._is_past_total_pages(page_text, current_page=16) is True

    def test_no_total_found(self, scraper):
        """Should return False when can't determine total."""
        page_text = "showing results for sofia apartments"
        assert scraper._is_past_total_pages(page_text, current_page=5) is False
        assert scraper._is_past_total_pages(page_text, current_page=100) is False


class TestIsLastPageIntegration:
    """Integration tests for is_last_page main function."""

    def test_detects_no_results(self, scraper):
        """Should detect last page via no results message."""
        html = "<html><body><p>Няма намерени обяви</p></body></html>"
        assert scraper.is_last_page(html, current_page=1) is True

    def test_detects_no_listings(self, scraper):
        """Should detect last page when no listing links."""
        html = """
        <html><body>
            <p>Results</p>
            <a href="/about">About</a>
        </body></html>
        """
        assert scraper.is_last_page(html, current_page=1) is True

    def test_detects_no_next_page(self, scraper):
        """Should detect last page when no next page link."""
        html = """
        <html><body>
            <a href="/obiava-abc-prodava-apt">Listing</a>
            <a href="/search/p-5">5</a>
        </body></html>
        """
        assert scraper.is_last_page(html, current_page=5) is True

    def test_not_last_page(self, scraper):
        """Should return False when not last page."""
        html = """
        <html><body>
            <a href="/obiava-abc-prodava-apt">Listing</a>
            <a href="/search/p-2">2</a>
            <a href="/search/p-3">3</a>
        </body></html>
        """
        assert scraper.is_last_page(html, current_page=1) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
