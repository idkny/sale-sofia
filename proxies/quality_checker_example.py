"""
Example usage of the quality_checker module.

This script demonstrates how to use the QualityChecker class and helper
functions to validate proxy quality against Google and target sites.
"""

import logging
from proxies.quality_checker import (
    QualityChecker,
    enrich_proxy_with_quality,
    enrich_proxies_batch,
)

# Setup logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def example_basic_checks():
    """Example: Basic individual checks."""
    print("\n=== Example 1: Basic Individual Checks ===")

    checker = QualityChecker(timeout=15)

    # Example proxy URL (replace with actual proxy)
    proxy_url = "http://localhost:8089"

    # Check Google (captcha detection)
    google_ok = checker.check_google(proxy_url)
    print(f"Google check: {'PASS' if google_ok else 'FAIL'}")

    # Check target site (imot.bg)
    target_ok = checker.check_target_site(proxy_url, "https://www.imot.bg")
    print(f"Target site check: {'PASS' if target_ok else 'FAIL'}")


def example_combined_check():
    """Example: Combined quality check."""
    print("\n=== Example 2: Combined Quality Check ===")

    checker = QualityChecker(timeout=15)
    proxy_url = "http://localhost:8089"

    # Run all checks at once
    results = checker.check_all(proxy_url)

    print(f"Combined results: {results}")
    print(f"  - Google passed: {results['google_passed']}")
    print(f"  - Target passed: {results['target_passed']}")

    if results["google_passed"] and results["target_passed"]:
        print("  ✓ Proxy is high quality!")
    else:
        print("  ✗ Proxy has quality issues")


def example_enrich_single_proxy():
    """Example: Enrich a single proxy dict."""
    print("\n=== Example 3: Enrich Single Proxy ===")

    proxy = {
        "host": "1.2.3.4",
        "port": 8080,
        "protocol": "http",
        "country": "BG",
        "anonymity": "Elite",
    }

    print(f"Original proxy: {proxy}")

    # Enrich with quality data
    enriched = enrich_proxy_with_quality(proxy, timeout=15)

    print(f"Enriched proxy: {enriched}")
    print(f"  - Google passed: {enriched.get('google_passed')}")
    print(f"  - Target passed: {enriched.get('target_passed')}")
    print(f"  - Checked at: {enriched.get('quality_checked_at')}")


def example_batch_enrichment():
    """Example: Batch enrich multiple proxies."""
    print("\n=== Example 4: Batch Enrichment ===")

    proxies = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
        {"host": "9.10.11.12", "port": 1080, "protocol": "socks5"},
    ]

    print(f"Checking {len(proxies)} proxies...")

    # Enrich all proxies
    enriched = enrich_proxies_batch(proxies, timeout=10)

    # Filter for high-quality proxies (passed both checks)
    high_quality = [
        p for p in enriched
        if p.get("google_passed") and p.get("target_passed")
    ]

    print(f"\nResults:")
    print(f"  - Total checked: {len(enriched)}")
    print(f"  - High quality: {len(high_quality)}")
    print(f"  - Google passed: {sum(1 for p in enriched if p.get('google_passed'))}")
    print(f"  - Target passed: {sum(1 for p in enriched if p.get('target_passed'))}")


def example_custom_target_site():
    """Example: Check against custom target site."""
    print("\n=== Example 5: Custom Target Site ===")

    checker = QualityChecker(timeout=15)
    proxy_url = "http://localhost:8089"

    # Check against different target sites
    targets = [
        "https://www.imot.bg",
        "https://www.google.com",
        "https://www.example.com",
    ]

    for target in targets:
        result = checker.check_target_site(proxy_url, target)
        print(f"  {target}: {'PASS' if result else 'FAIL'}")


def example_filter_working_proxies():
    """Example: Filter proxies to get only working ones."""
    print("\n=== Example 6: Filter Working Proxies ===")

    # Simulated proxy pool (replace with actual proxies)
    proxy_pool = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
        {"host": "9.10.11.12", "port": 1080, "protocol": "socks5"},
        {"host": "13.14.15.16", "port": 8080, "protocol": "http"},
    ]

    print(f"Starting with {len(proxy_pool)} proxies")

    # Enrich with quality checks
    enriched = enrich_proxies_batch(proxy_pool, timeout=10)

    # Filter for Google-compatible proxies (no captcha)
    google_friendly = [
        p for p in enriched
        if p.get("google_passed", False)
    ]

    # Filter for target site compatible proxies
    target_friendly = [
        p for p in enriched
        if p.get("target_passed", False)
    ]

    # Filter for premium quality (both checks passed)
    premium = [
        p for p in enriched
        if p.get("google_passed", False) and p.get("target_passed", False)
    ]

    print(f"\nFiltered results:")
    print(f"  - Google-friendly: {len(google_friendly)} proxies")
    print(f"  - Target-friendly: {len(target_friendly)} proxies")
    print(f"  - Premium quality: {len(premium)} proxies")

    if premium:
        print(f"\nPremium proxies:")
        for p in premium:
            print(f"  - {p['protocol']}://{p['host']}:{p['port']}")


if __name__ == "__main__":
    print("=" * 60)
    print("Quality Checker Examples")
    print("=" * 60)

    # NOTE: These examples use placeholder proxy URLs
    # Replace with actual working proxies for real testing

    try:
        example_basic_checks()
        example_combined_check()
        example_enrich_single_proxy()
        example_batch_enrichment()
        example_custom_target_site()
        example_filter_working_proxies()

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
