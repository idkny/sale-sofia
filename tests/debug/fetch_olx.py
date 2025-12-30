#!/usr/bin/env python3
"""
Fetch OLX.bg pages for analysis and save locally.
This helps create the YAML config for the generic scraper.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapling import Adaptor

# Output directory
OUTPUT_DIR = Path("/tmp/olx_samples")
OUTPUT_DIR.mkdir(exist_ok=True)

# Correct URL for OLX.bg real estate (sofiya, not sofia)
SEARCH_URL = "https://www.olx.bg/nedvizhimi-imoti/prodazhbi/apartamenti/sofiya/"


def fetch_search_page():
    """Fetch and save search results page using Camoufox browser."""
    print(f"Fetching search page: {SEARCH_URL}")
    print("Using Camoufox browser (no proxy)...")

    try:
        from camoufox.sync_api import Camoufox

        with Camoufox(
            headless=True,
            humanize=True,
            geoip=True,
            block_webrtc=True,
        ) as browser:
            page = browser.new_page()
            print("  Navigating to page...")
            page.goto(SEARCH_URL, timeout=60000, wait_until="networkidle")
            html = page.content()

        output_file = OUTPUT_DIR / "olx_search.html"
        output_file.write_text(html, encoding="utf-8")

        print(f"✓ Saved {len(html):,} bytes to {output_file}")
        return html

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_search_page(html: str):
    """Analyze HTML structure and print selector hints."""
    page = Adaptor(html, auto_match=False)

    print("\n" + "=" * 60)
    print("SEARCH PAGE STRUCTURE ANALYSIS")
    print("=" * 60)

    # Look for common listing card patterns
    card_candidates = [
        "[data-cy='l-card']",
        "[data-testid='listing-card']",
        "div[data-testid='ad-card']",
        ".listing-card",
        ".offer-item",
        "article.offer",
        "div.offer-wrapper",
        "div[data-id]",
        ".css-rc5s2u",  # OLX uses dynamic class names
    ]

    print("\n1. LISTING CARD CONTAINERS:")
    found_card_selector = None
    for selector in card_candidates:
        elements = page.css(selector)
        if elements:
            print(f"   ✓ {selector}: {len(elements)} elements")
            if not found_card_selector:
                found_card_selector = selector

    # Find divs with data-cy attribute (OLX pattern)
    data_cy_elements = page.css("[data-cy]")
    if data_cy_elements:
        print(f"\n   Elements with data-cy: {len(data_cy_elements)}")
        unique_attrs = set()
        for el in data_cy_elements[:50]:  # Sample first 50
            attr = el.attrib.get("data-cy", "")
            unique_attrs.add(attr)
        print(f"   Unique data-cy values: {sorted(unique_attrs)[:10]}")

    # Find all links and look for listing patterns
    print("\n2. LINK PATTERNS:")
    all_links = page.css("a[href]")
    listing_urls = []
    for link in all_links:
        href = link.attrib.get("href", "")
        # OLX listing patterns
        if "/d/ad/" in href or "/d/oferta/" in href:
            if href not in listing_urls:
                listing_urls.append(href)

    if listing_urls:
        print(f"   Found {len(listing_urls)} listing URLs")
        print("   Sample URLs:")
        for url in listing_urls[:5]:
            print(f"   - {url}")

        # Extract ID pattern
        import re
        for url in listing_urls[:3]:
            # Try to find ID in URL
            id_match = re.search(r'-ID([a-zA-Z0-9]+)\.html', url)
            if id_match:
                print(f"\n   ID Pattern: '-ID([a-zA-Z0-9]+)\\.html'")
                print(f"   Example ID: {id_match.group(1)}")
                break
    else:
        # Try alternate patterns
        print("   No /d/ad/ or /d/oferta/ patterns found")
        print("   Looking for alternate patterns...")
        for link in all_links[:100]:
            href = link.attrib.get("href", "")
            if "imoti" in href or "nedvizhimi" in href:
                print(f"   - {href}")

    # Print first few listing cards HTML for manual inspection
    if found_card_selector:
        print(f"\n3. SAMPLE CARD HTML ({found_card_selector}):")
        cards = page.css(found_card_selector)
        for i, card in enumerate(cards[:2]):
            print(f"\n   --- Card {i+1} (first 800 chars) ---")
            html_str = str(card.html)[:800]
            # Prettify a bit
            html_str = html_str.replace("><", ">\n   <")
            print(f"   {html_str}")
    else:
        # Show page structure instead
        print("\n3. PAGE STRUCTURE (no card selector found):")
        print(f"   <body> children: {len(page.css('body > *'))}")
        main = page.css("main")
        if main:
            print(f"   <main> found with {len(main[0].css('*'))} descendants")

        # Look for any repeating structure
        divs = page.css("div")
        print(f"   Total divs: {len(divs)}")


if __name__ == "__main__":
    html = fetch_search_page()
    if html:
        analyze_search_page(html)
