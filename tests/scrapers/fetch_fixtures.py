#!/usr/bin/env python3
"""
Fetch real HTML fixtures from imot.bg and bazar.bg for testing.

This script fetches real HTML pages from both websites and saves them
as test fixtures. The fixtures can be used for offline testing of
scraper extraction logic.

Usage:
    python tests/scrapers/fetch_fixtures.py

Fixtures saved:
    - tests/scrapers/fixtures/imot_search.html
    - tests/scrapers/fixtures/imot_listing.html
    - tests/scrapers/fixtures/bazar_search.html
    - tests/scrapers/fixtures/bazar_listing.html
"""

import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import chardet
import httpx


# Constants
FIXTURES_DIR = Path(__file__).parent / "fixtures"
REQUEST_TIMEOUT = 30

# Headers matching the production scraper
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def detect_encoding(content: bytes, headers: dict = None) -> str:
    """
    Detect encoding from content and headers.

    Args:
        content: Raw bytes from response
        headers: HTTP response headers

    Returns:
        Detected encoding string
    """
    # 1. Check HTTP headers
    if headers:
        content_type = headers.get("content-type", "")
        charset_match = re.search(r"charset=([^\s;]+)", content_type, re.IGNORECASE)
        if charset_match:
            return charset_match.group(1).strip('"\'')

    # 2. Check HTML meta tag (look in first 1024 bytes)
    head_content = content[:1024].decode("ascii", errors="ignore")

    # <meta charset="...">
    meta_match = re.search(r'<meta[^>]+charset=["\']?([^"\'\s>]+)', head_content, re.IGNORECASE)
    if meta_match:
        return meta_match.group(1)

    # <meta http-equiv="Content-Type" content="...; charset=...">
    http_equiv_match = re.search(
        r'<meta[^>]+content=["\'][^"\']*charset=([^"\'\s;]+)',
        head_content,
        re.IGNORECASE
    )
    if http_equiv_match:
        return http_equiv_match.group(1)

    # 3. Auto-detect with chardet
    detected = chardet.detect(content[:10000])
    if detected and detected.get("encoding"):
        confidence = detected.get("confidence", 0)
        if confidence > 0.7:
            return detected["encoding"]

    # 4. Default
    return "utf-8"


def fetch_page(url: str, expected_encoding: str = None) -> str:
    """
    Fetch a page and return its content with proper encoding.

    Args:
        url: URL to fetch
        expected_encoding: Hint for expected encoding (will auto-detect if None)

    Returns:
        HTML content as string
    """
    print(f"  Fetching: {url}")

    with httpx.Client(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    ) as client:
        response = client.get(url, headers=DEFAULT_HEADERS)
        response.raise_for_status()

        # Get raw bytes
        content = response.content

        # Detect encoding (prefer expected, fallback to auto-detect)
        encoding = expected_encoding or detect_encoding(content, dict(response.headers))

        # Decode with fallback
        try:
            html = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Try common Cyrillic encodings
            for enc in ["windows-1251", "utf-8", "iso-8859-5"]:
                try:
                    html = content.decode(enc)
                    print(f"  Fallback encoding used: {enc}")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                html = content.decode("utf-8", errors="replace")

        return html


def save_fixture(filename: str, content: str) -> Path:
    """
    Save HTML content to fixtures directory.

    Args:
        filename: Name of the fixture file
        content: HTML content to save

    Returns:
        Path to saved file
    """
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    filepath = FIXTURES_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  Saved: {filepath}")
    return filepath


def extract_imot_listing_url(html: str) -> str | None:
    """
    Extract a listing URL from imot.bg search results.

    Looks for links matching pattern: //www.imot.bg/obiava-XXX-...

    Args:
        html: HTML content of search results page

    Returns:
        Absolute listing URL or None if not found
    """
    # Pattern: Protocol-relative URLs like //www.imot.bg/obiava-...
    pattern = r'href="(//www\.imot\.bg/obiava-[^"]+)"'
    matches = re.findall(pattern, html)

    if matches:
        # Get first unique listing URL, add https:
        return "https:" + matches[0]

    # Fallback: absolute URLs with https
    pattern2 = r'href="(https://www\.imot\.bg/obiava-[^"]+)"'
    matches = re.findall(pattern2, html)
    if matches:
        return matches[0]

    # Fallback: relative URLs
    pattern3 = r'href="(/obiava-[^"]+)"'
    matches = re.findall(pattern3, html)
    if matches:
        return urljoin("https://www.imot.bg", matches[0])

    return None


def extract_bazar_listing_url(html: str) -> str | None:
    """
    Extract a listing URL from bazar.bg search results.

    Looks for links matching pattern: https://bazar.bg/obiava-XXXX/...
    Filters to only get "prodawa" (sale) listings, not "dawa-pod-naem" (rent).

    Args:
        html: HTML content of search results page

    Returns:
        Absolute listing URL or None if not found
    """
    # Pattern: absolute URLs like https://bazar.bg/obiava-12345678/prodawa-...
    pattern = r'href="(https://bazar\.bg/obiava-\d+/prodawa-[^"]+)"'
    matches = re.findall(pattern, html)

    if matches:
        return matches[0]

    # Fallback: any obiava URL (including rentals)
    pattern2 = r'href="(https://bazar\.bg/obiava-\d+/[^"]+)"'
    matches = re.findall(pattern2, html)
    if matches:
        return matches[0]

    # Fallback: relative URLs
    pattern3 = r'href="(/obiava-\d+/[^"]+)"'
    matches = re.findall(pattern3, html)
    if matches:
        return urljoin("https://bazar.bg", matches[0])

    return None


def fetch_imot_fixtures() -> tuple[bool, bool]:
    """
    Fetch imot.bg search and listing pages.

    Returns:
        Tuple of (search_success, listing_success)
    """
    print("\n=== Fetching imot.bg fixtures ===")

    # Use the correct URL from imot_scraper.py
    search_url = "https://www.imot.bg/obiavi/prodazhbi/grad-sofiya"

    search_success = False
    listing_success = False

    # Fetch search page
    try:
        search_html = fetch_page(search_url, expected_encoding="windows-1251")
        save_fixture("imot_search.html", search_html)
        search_success = True
        print(f"  Search page size: {len(search_html):,} bytes")
    except httpx.HTTPStatusError as e:
        print(f"  ERROR fetching search page: {e}")
        return False, False
    except httpx.RequestError as e:
        print(f"  ERROR fetching search page: {e}")
        return False, False

    # Extract and fetch a listing
    listing_url = extract_imot_listing_url(search_html)
    if listing_url:
        try:
            listing_html = fetch_page(listing_url, expected_encoding="windows-1251")
            save_fixture("imot_listing.html", listing_html)
            listing_success = True
            print(f"  Listing page size: {len(listing_html):,} bytes")
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            print(f"  ERROR fetching listing page: {e}")
    else:
        print("  ERROR: Could not find listing URL in search results")

    return search_success, listing_success


def fetch_bazar_fixtures() -> tuple[bool, bool]:
    """
    Fetch bazar.bg search and listing pages.

    Returns:
        Tuple of (search_success, listing_success)
    """
    print("\n=== Fetching bazar.bg fixtures ===")

    # Use the correct URL from bazar_scraper.py
    search_url = "https://bazar.bg/obiavi/apartamenti/sofia"

    search_success = False
    listing_success = False

    # Fetch search page
    try:
        search_html = fetch_page(search_url, expected_encoding="utf-8")
        save_fixture("bazar_search.html", search_html)
        search_success = True
        print(f"  Search page size: {len(search_html):,} bytes")
    except httpx.HTTPStatusError as e:
        print(f"  ERROR fetching search page: {e}")
        return False, False
    except httpx.RequestError as e:
        print(f"  ERROR fetching search page: {e}")
        return False, False

    # Extract and fetch a listing
    listing_url = extract_bazar_listing_url(search_html)
    if listing_url:
        try:
            listing_html = fetch_page(listing_url, expected_encoding="utf-8")
            save_fixture("bazar_listing.html", listing_html)
            listing_success = True
            print(f"  Listing page size: {len(listing_html):,} bytes")
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            print(f"  ERROR fetching listing page: {e}")
    else:
        print("  ERROR: Could not find listing URL in search results")

    return search_success, listing_success


def main():
    """Main entry point."""
    print("Fetching HTML fixtures for scraper tests")
    print(f"Fixtures directory: {FIXTURES_DIR}")

    # Fetch all fixtures
    imot_search, imot_listing = fetch_imot_fixtures()
    bazar_search, bazar_listing = fetch_bazar_fixtures()

    # Summary
    print("\n=== Summary ===")
    results = [
        ("imot_search.html", imot_search),
        ("imot_listing.html", imot_listing),
        ("bazar_search.html", bazar_search),
        ("bazar_listing.html", bazar_listing),
    ]

    all_success = True
    for name, success in results:
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")
        if not success:
            all_success = False

    if all_success:
        print("\nAll fixtures fetched successfully!")
        return 0
    else:
        print("\nSome fixtures failed to fetch.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
