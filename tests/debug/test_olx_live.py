#!/usr/bin/env python3
"""
Live test of ConfigScraper with OLX.bg using Camoufox browser.
Fetches fresh data without proxy rotation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from camoufox.sync_api import Camoufox
from scrapling import Adaptor
from websites.generic import ConfigScraper

CONFIG_PATH = "config/sites/olx_bg.yaml"
SEARCH_URL = "https://www.olx.bg/nedvizhimi-imoti/prodazhbi/apartamenti/sofiya/"


def fetch_with_camoufox(url: str) -> str:
    """Fetch page using Camoufox browser."""
    print(f"  Fetching: {url}")

    with Camoufox(
        headless=True,
        humanize=True,
        geoip=True,
        block_webrtc=True,
    ) as browser:
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="networkidle")
        html = page.content()

    print(f"  ✓ Got {len(html):,} bytes")
    return html


def test_live_search():
    """Test live search page extraction."""
    print("=" * 60)
    print("LIVE TEST: Search Page")
    print("=" * 60)

    scraper = ConfigScraper(CONFIG_PATH)
    html = fetch_with_camoufox(SEARCH_URL)

    urls = scraper.extract_search_results(html)
    print(f"\n✓ Found {len(urls)} listing URLs")

    if urls:
        print("\nFirst 3 URLs:")
        for url in urls[:3]:
            print(f"  - {url}")

    return urls


def test_live_listing(listing_url: str):
    """Test live listing extraction."""
    print()
    print("=" * 60)
    print("LIVE TEST: Listing Detail")
    print("=" * 60)

    scraper = ConfigScraper(CONFIG_PATH)

    # Convert relative to absolute URL
    if listing_url.startswith("/"):
        full_url = f"https://www.olx.bg{listing_url}"
    else:
        full_url = listing_url

    html = fetch_with_camoufox(full_url)
    listing = scraper.extract_listing(html, full_url)

    if not listing:
        print("\n✗ Failed to extract listing")
        return False

    print("\n✓ Listing extracted:")
    print(f"  ID:          {listing.external_id}")
    print(f"  Title:       {listing.title[:50]}..." if listing.title else "  Title:       None")
    print(f"  Price:       {listing.price_eur}")
    print(f"  SQM:         {listing.sqm_total}")
    print(f"  Rooms:       {listing.rooms_count}")
    print(f"  Floor:       {listing.floor_number}/{listing.floor_total}")
    print(f"  District:    {listing.district}")
    print(f"  Neighborhood:{listing.neighborhood}")
    print(f"  Images:      {len(listing.image_urls)}")

    return True


def main():
    print()
    print("OLX.bg Live Test (Camoufox, no proxy)")
    print()

    try:
        urls = test_live_search()

        if urls:
            # Test first listing
            test_live_listing(urls[0])

        print()
        print("=" * 60)
        print("LIVE TEST COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
