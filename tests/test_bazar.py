#!/usr/bin/env python3
"""Quick test for bazar.bg scraper - scrapes 2 listings without proxy infrastructure."""

import asyncio
from loguru import logger

from browsers.browsers_main import create_instance
from websites.bazar_bg.bazar_scraper import BazarBgScraper


async def test_bazar_scraper():
    """Test bazar.bg scraper with 2 listings."""

    # Correct URL format: /obiavi/apartamenti/{type}/sofia
    start_url = "https://bazar.bg/obiavi/apartamenti/tristaini/sofia"

    scraper = BazarBgScraper()
    print(f"\n{'='*60}")
    print("BAZAR.BG SCRAPER TEST")
    print(f"{'='*60}")
    print(f"Start URL: {start_url}")
    print(f"Target: 2 listings")
    print()

    # Create browser (no proxy for quick test)
    print("[1/4] Starting browser...")
    browser = await create_instance(browser_type="chromiumstealth", proxy=None)
    if not browser:
        print("[ERROR] Failed to start browser")
        return

    try:
        page = await browser.new_tab()

        # Load search page
        print("[2/4] Loading search page...")
        await page.goto(start_url, wait_until="domcontentloaded")
        await asyncio.sleep(2)  # Wait for JS to load
        html = await page.content()

        # Extract listing URLs
        print("[3/4] Extracting listing URLs...")
        listing_urls = await scraper.extract_search_results(html)
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

        # Scrape each listing
        print("[4/4] Scraping listings...")
        for i, url in enumerate(urls_to_scrape, 1):
            print(f"\n--- Listing {i}/2 ---")
            print(f"URL: {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                html = await page.content()

                listing = await scraper.extract_listing(html, url)

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

        print(f"\n{'='*60}")
        print("TEST COMPLETE")
        print(f"{'='*60}")

    finally:
        await browser._browser.close()


if __name__ == "__main__":
    asyncio.run(test_bazar_scraper())
