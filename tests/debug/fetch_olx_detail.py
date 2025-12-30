#!/usr/bin/env python3
"""
Fetch OLX.bg listing detail page for analysis.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapling import Adaptor

OUTPUT_DIR = Path("/tmp/olx_samples")
OUTPUT_DIR.mkdir(exist_ok=True)

# Get first listing URL from search results
def get_listing_url():
    search_html = (OUTPUT_DIR / "olx_search.html").read_text()
    page = Adaptor(search_html, auto_match=False)
    links = page.css("a[href*='/d/ad/']")
    if links:
        href = links[0].attrib.get("href", "")
        if href.startswith("/"):
            return f"https://www.olx.bg{href}"
        return href
    return None


def fetch_detail_page(url: str):
    """Fetch listing detail page."""
    print(f"Fetching detail page: {url}")
    print("Using Camoufox browser...")

    try:
        from camoufox.sync_api import Camoufox

        with Camoufox(
            headless=True,
            humanize=True,
            geoip=True,
            block_webrtc=True,
        ) as browser:
            page = browser.new_page()
            print("  Navigating...")
            page.goto(url, timeout=60000, wait_until="networkidle")
            html = page.content()

        output_file = OUTPUT_DIR / "olx_detail.html"
        output_file.write_text(html, encoding="utf-8")

        print(f"✓ Saved {len(html):,} bytes to {output_file}")
        return html

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_detail_page(html: str):
    """Analyze detail page structure."""
    page = Adaptor(html, auto_match=False)

    print("\n" + "=" * 60)
    print("DETAIL PAGE STRUCTURE ANALYSIS")
    print("=" * 60)

    # Look for common field selectors
    selectors_to_try = {
        "title": ["h1", "[data-cy='ad_title']", "h1[data-testid='ad_title']", ".ad-title"],
        "price": [
            "[data-testid='ad-price-container']",
            "[data-cy='ad-price']",
            "h3.css-price",
            "[data-testid='ad-price']",
        ],
        "description": [
            "[data-cy='ad_description']",
            "[data-testid='ad_description']",
            ".description",
        ],
    }

    print("\n1. LOOKING FOR FIELD SELECTORS:")
    for field, candidates in selectors_to_try.items():
        print(f"\n   {field.upper()}:")
        for selector in candidates:
            els = page.css(selector)
            if els:
                text = els[0].text or ""
                text = text[:60].replace("\n", " ").strip()
                print(f"   ✓ {selector}: \"{text}\"")
                break
        else:
            print(f"   ✗ None of the candidates found")

    # Look for data-cy attributes
    print("\n2. ALL DATA-CY ATTRIBUTES ON PAGE:")
    data_cy_els = page.css("[data-cy]")
    unique_attrs = {}
    for el in data_cy_els:
        attr = el.attrib.get("data-cy", "")
        if attr not in unique_attrs:
            text = (el.text or "")[:40].replace("\n", " ").strip()
            unique_attrs[attr] = text

    for attr, text in sorted(unique_attrs.items())[:20]:
        print(f"   {attr}: \"{text}\"")

    # Look for data-testid attributes
    print("\n3. ALL DATA-TESTID ATTRIBUTES ON PAGE:")
    data_testid_els = page.css("[data-testid]")
    unique_testids = {}
    for el in data_testid_els:
        attr = el.attrib.get("data-testid", "")
        if attr not in unique_testids:
            text = (el.text or "")[:40].replace("\n", " ").strip()
            unique_testids[attr] = text

    for attr, text in sorted(unique_testids.items())[:25]:
        print(f"   {attr}: \"{text}\"")

    # Look for structured data (JSON-LD)
    print("\n4. STRUCTURED DATA (JSON-LD):")
    scripts = page.css('script[type="application/ld+json"]')
    if scripts:
        import json
        for i, script in enumerate(scripts[:2]):
            try:
                data = json.loads(script.text or "{}")
                print(f"   Schema {i+1}: {data.get('@type', 'unknown')}")
                if "name" in data:
                    print(f"     name: {data['name'][:50]}")
                if "price" in data:
                    print(f"     price: {data['price']}")
            except:
                pass
    else:
        print("   No JSON-LD found")


if __name__ == "__main__":
    url = get_listing_url()
    if not url:
        print("Could not find listing URL from search results")
        sys.exit(1)

    html = fetch_detail_page(url)
    if html:
        analyze_detail_page(html)
