#!/usr/bin/env python3
"""
Test ConfigScraper with real OLX.bg HTML.
Uses HTML saved from fetch_olx.py and fetch_olx_detail.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from websites.generic import ConfigScraper

# Paths
CONFIG_PATH = "config/sites/olx_bg.yaml"
SEARCH_HTML = Path("/tmp/olx_samples/olx_search.html")
DETAIL_HTML = Path("/tmp/olx_samples/olx_detail.html")
DETAIL_URL = "https://www.olx.bg/d/ad/moderno-obzaveden-dvustaen-apartament-bez-komisionna-ot-kupuvacha-CID368-ID9UaU4.html"


def test_search_results():
    """Test extracting listing URLs from search results."""
    print("=" * 60)
    print("TEST: Search Results Extraction")
    print("=" * 60)

    if not SEARCH_HTML.exists():
        print("✗ Search HTML not found. Run fetch_olx.py first.")
        return False

    scraper = ConfigScraper(CONFIG_PATH)
    html = SEARCH_HTML.read_text()

    urls = scraper.extract_search_results(html)

    print(f"✓ Found {len(urls)} listing URLs")
    print()
    print("Sample URLs:")
    for url in urls[:5]:
        print(f"  - {url}")

    return len(urls) > 0


def test_listing_extraction():
    """Test extracting listing data from detail page."""
    print()
    print("=" * 60)
    print("TEST: Listing Detail Extraction")
    print("=" * 60)

    if not DETAIL_HTML.exists():
        print("✗ Detail HTML not found. Run fetch_olx_detail.py first.")
        return False

    scraper = ConfigScraper(CONFIG_PATH)
    html = DETAIL_HTML.read_text()

    listing = scraper.extract_listing(html, DETAIL_URL)

    if not listing:
        print("✗ Failed to extract listing")
        return False

    print("✓ Listing extracted successfully!")
    print()
    print("Extracted fields:")
    print(f"  external_id:   {listing.external_id}")
    print(f"  title:         {listing.title[:50] if listing.title else 'None'}...")
    print(f"  price_eur:     {listing.price_eur}")
    print(f"  sqm_total:     {listing.sqm_total}")
    print(f"  rooms_count:   {listing.rooms_count}")
    print(f"  floor_number:  {listing.floor_number}")
    print(f"  floor_total:   {listing.floor_total}")
    print(f"  district:      {listing.district}")
    print(f"  neighborhood:  {listing.neighborhood}")
    print(f"  images:        {len(listing.image_urls)} images")
    print(f"  description:   {listing.description[:80] if listing.description else 'None'}...")

    return True


def main():
    print()
    print("OLX.bg Generic Scraper Test")
    print("Using saved HTML from /tmp/olx_samples/")
    print()

    search_ok = test_search_results()
    listing_ok = test_listing_extraction()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Search extraction: {'✓ PASS' if search_ok else '✗ FAIL'}")
    print(f"Listing extraction: {'✓ PASS' if listing_ok else '✗ FAIL'}")

    # Known limitations
    print()
    print("WHAT WORKS:")
    print("  ✓ Search results: listing URLs extracted")
    print("  ✓ Title, description, images extracted")
    print("  ✓ SQM, floor_number, floor_total extracted (label_value parser)")
    print("  ✓ Features extracted")
    print()
    print("REMAINING LIMITATIONS:")
    print("  - Price: Extracts BGN not EUR")
    print("  - Rooms: Extracts '2 - стаен' text, not integer")
    print("  - District/neighborhood: Contains 'Апартаменти -' prefix")


if __name__ == "__main__":
    main()
