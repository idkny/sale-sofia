#!/usr/bin/env python3
"""Quick test for bazar.bg scraper - scrapes 2 listings using Scrapling."""

import time

from scrapling.fetchers import Fetcher, StealthyFetcher

from websites.bazar_bg.bazar_scraper import BazarBgScraper


def test_bazar_scraper():
    """Test bazar.bg scraper with 2 listings."""

    # Correct URL format: /obiavi/apartamenti/{type}/sofia
    start_url = "https://bazar.bg/obiavi/apartamenti/tristaini/sofia"

    scraper = BazarBgScraper()
    print(f"\n{'='*60}")
    print("BAZAR.BG SCRAPER TEST (Scrapling)")
    print(f"{'='*60}")
    print(f"Start URL: {start_url}")
    print(f"Target: 2 listings")
    print()

    # Load search page with fast Fetcher
    print("[1/3] Loading search page...")
    try:
        response = Fetcher.fetch(url=start_url, timeout=15000)
        html = response.html_content
    except Exception as e:
        print(f"[ERROR] Failed to load search page: {e}")
        return

    # Extract listing URLs
    print("[2/3] Extracting listing URLs...")
    listing_urls = scraper.extract_search_results(html)
    print(f"      Found {len(listing_urls)} listings on page")

    if not listing_urls:
        print("[ERROR] No listings found! Saving HTML for debug...")
        with open("/tmp/bazar_search_debug.html", "w") as f:
            f.write(html)
        print("      Saved to /tmp/bazar_search_debug.html")
        return

    # Take first 2
    urls_to_scrape = listing_urls[:2]
    print(f"      Will scrape: {urls_to_scrape}")
    print()

    # Scrape each listing with StealthyFetcher
    print("[3/3] Scraping listings...")
    for i, url in enumerate(urls_to_scrape, 1):
        print(f"\n--- Listing {i}/2 ---")
        print(f"URL: {url}")

        try:
            response = StealthyFetcher.fetch(
                url=url,
                humanize=True,
                block_webrtc=True,
                network_idle=True,
                timeout=30000
            )
            html = response.html_content

            listing = scraper.extract_listing(html, url)

            if listing:
                print(f"  ID: {listing.external_id}")
                print(f"  Price: {listing.price_eur} EUR")
                print(f"  Size: {listing.sqm_total} sqm")
                print(f"  Rooms: {listing.rooms_count}")
                print(f"  Floor: {listing.floor_number}/{listing.floor_total}")
                print(f"  Building: {listing.building_type}")
                print(f"  Location: {listing.neighborhood}")
                print(f"  Elevator: {listing.has_elevator}")
                print(f"  Balcony: {listing.has_balcony}")
            else:
                print("  [ERROR] Failed to extract listing data")
                # Save HTML for debugging
                with open(f"/tmp/bazar_listing_{i}_debug.html", "w") as f:
                    f.write(html)
                print(f"  Saved HTML to /tmp/bazar_listing_{i}_debug.html")

        except Exception as e:
            print(f"  [ERROR] {e}")

        # Small delay between requests
        if i < len(urls_to_scrape):
            time.sleep(2)

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_bazar_scraper()
