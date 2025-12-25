"""
Integration example: Using quality_checker with existing proxy infrastructure.

This demonstrates how to integrate the quality checker into the existing
proxy validation pipeline alongside ProxyValidator and AnonymityChecker.
"""

import logging
from pathlib import Path

from proxies.anonymity_checker import enrich_proxy_with_anonymity
from proxies.proxy_validator import ProxyValidator
from proxies.quality_checker import enrich_proxy_with_quality, enrich_proxies_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def example_1_complete_validation_pipeline():
    """
    Example 1: Complete validation pipeline.

    Shows the recommended flow:
    1. Basic liveness check (ProxyValidator)
    2. Anonymity check (AnonymityChecker)
    3. Quality check (QualityChecker)
    """
    print("\n" + "=" * 60)
    print("Example 1: Complete Validation Pipeline")
    print("=" * 60)

    proxy = {
        "host": "1.2.3.4",
        "port": 8080,
        "protocol": "http",
    }

    # Step 1: Basic liveness check
    print("\n[Step 1] Basic liveness check...")
    validator = ProxyValidator()
    proxy_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"

    if not validator.check_proxy_liveness(proxy_url, timeout=10):
        print("✗ Proxy failed liveness check. Skipping further validation.")
        return

    print("✓ Proxy passed liveness check")

    # Step 2: Anonymity check
    print("\n[Step 2] Anonymity check...")
    proxy = enrich_proxy_with_anonymity(proxy, timeout=10)
    print(f"✓ Anonymity level: {proxy.get('anonymity', 'Unknown')}")

    # Step 3: Quality check
    print("\n[Step 3] Quality check...")
    proxy = enrich_proxy_with_quality(proxy, timeout=15)

    print(f"  - Google check: {'PASS' if proxy.get('google_passed') else 'FAIL'}")
    print(f"  - Target check: {'PASS' if proxy.get('target_passed') else 'FAIL'}")

    # Final assessment
    print("\n[Final Assessment]")
    print(f"Complete proxy profile:")
    for key, value in proxy.items():
        print(f"  - {key}: {value}")

    # Determine quality tier
    if proxy.get("anonymity") == "Elite" and proxy.get("google_passed") and proxy.get("target_passed"):
        print("\n✓✓✓ PREMIUM QUALITY PROXY - Use for critical scraping")
    elif proxy.get("google_passed") and proxy.get("target_passed"):
        print("\n✓✓ HIGH QUALITY PROXY - Good for most tasks")
    elif proxy.get("target_passed"):
        print("\n✓ MEDIUM QUALITY PROXY - OK for target site")
    else:
        print("\n✗ LOW QUALITY PROXY - Not recommended")


def example_2_batch_processing_with_filtering():
    """
    Example 2: Batch processing with multi-tier filtering.

    Shows how to process multiple proxies and categorize them
    into quality tiers for different use cases.
    """
    print("\n" + "=" * 60)
    print("Example 2: Batch Processing with Filtering")
    print("=" * 60)

    # Simulated proxy pool
    proxy_pool = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
        {"host": "9.10.11.12", "port": 1080, "protocol": "socks5"},
        {"host": "13.14.15.16", "port": 8888, "protocol": "http"},
    ]

    print(f"\nProcessing {len(proxy_pool)} proxies...")

    # Batch quality check
    enriched = enrich_proxies_batch(proxy_pool, timeout=10)

    # Categorize into tiers
    premium_tier = []  # Both Google and target passed
    google_tier = []   # Google passed only
    target_tier = []   # Target passed only
    failed_tier = []   # Both failed

    for proxy in enriched:
        google_ok = proxy.get("google_passed", False)
        target_ok = proxy.get("target_passed", False)

        if google_ok and target_ok:
            premium_tier.append(proxy)
        elif google_ok:
            google_tier.append(proxy)
        elif target_ok:
            target_tier.append(proxy)
        else:
            failed_tier.append(proxy)

    # Display results
    print(f"\n[Results]")
    print(f"  Premium (Google + Target): {len(premium_tier)} proxies")
    print(f"  Google-only: {len(google_tier)} proxies")
    print(f"  Target-only: {len(target_tier)} proxies")
    print(f"  Failed: {len(failed_tier)} proxies")

    # Use case recommendations
    print(f"\n[Use Case Recommendations]")
    print(f"  For Google searches → Use premium or google-only tiers")
    print(f"  For imot.bg scraping → Use premium or target-only tiers")
    print(f"  For general web → Use premium tier only")


def example_3_selective_quality_check():
    """
    Example 3: Selective quality checking.

    Shows how to selectively run quality checks based on proxy
    characteristics (e.g., only check elite anonymous proxies).
    """
    print("\n" + "=" * 60)
    print("Example 3: Selective Quality Checking")
    print("=" * 60)

    # Proxy pool with anonymity already checked
    proxy_pool = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http", "anonymity": "Transparent"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http", "anonymity": "Anonymous"},
        {"host": "9.10.11.12", "port": 1080, "protocol": "socks5", "anonymity": "Elite"},
        {"host": "13.14.15.16", "port": 8888, "protocol": "http", "anonymity": "Elite"},
    ]

    print(f"\nStarting with {len(proxy_pool)} proxies")

    # Only quality-check Elite proxies (save time/resources)
    elite_proxies = [p for p in proxy_pool if p.get("anonymity") == "Elite"]

    print(f"Selectively checking {len(elite_proxies)} Elite proxies...")

    # Quality check only elite proxies
    for proxy in elite_proxies:
        enrich_proxy_with_quality(proxy, timeout=15)

    # Add None values for unchecked proxies
    for proxy in proxy_pool:
        if "google_passed" not in proxy:
            proxy["google_passed"] = None
            proxy["target_passed"] = None

    # Display results
    print(f"\n[Results]")
    for proxy in proxy_pool:
        anonymity = proxy.get("anonymity", "Unknown")
        google = proxy.get("google_passed")
        target = proxy.get("target_passed")

        google_str = "PASS" if google else ("FAIL" if google is False else "SKIP")
        target_str = "PASS" if target else ("FAIL" if target is False else "SKIP")

        print(f"  {proxy['host']}:{proxy['port']}")
        print(f"    Anonymity: {anonymity}")
        print(f"    Google: {google_str}, Target: {target_str}")


def example_4_preflight_check_before_scraping():
    """
    Example 4: Pre-flight quality check before scraping.

    Shows how to use quality checker as a final validation
    step before starting a scraping job.
    """
    print("\n" + "=" * 60)
    print("Example 4: Pre-flight Check Before Scraping")
    print("=" * 60)

    from proxies.quality_checker import QualityChecker

    # Proxy rotator endpoint (e.g., mubeng)
    proxy_rotator_url = "http://localhost:8089"

    print(f"\nPreparing to scrape imot.bg via {proxy_rotator_url}")

    # Step 1: Basic liveness check
    print("\n[Pre-flight 1/3] Checking proxy rotator is alive...")
    validator = ProxyValidator()
    if not validator.check_proxy_liveness(proxy_rotator_url, timeout=5):
        print("✗ Proxy rotator is down. Aborting scrape.")
        return
    print("✓ Proxy rotator is alive")

    # Step 2: Google captcha check
    print("\n[Pre-flight 2/3] Checking for Google captcha...")
    checker = QualityChecker(timeout=10)
    if not checker.check_google(proxy_rotator_url):
        print("⚠ Warning: Proxy triggering Google captcha")
        print("  Consider using different proxy pool")
        # Decide whether to continue
        proceed = input("Continue anyway? (y/n): ").lower() == 'y'
        if not proceed:
            print("Aborting scrape.")
            return

    print("✓ No Google captcha detected")

    # Step 3: Target site check
    print("\n[Pre-flight 3/3] Checking imot.bg accessibility...")
    if not checker.check_target_site(proxy_rotator_url, "https://www.imot.bg"):
        print("✗ Cannot access imot.bg via proxy. Aborting scrape.")
        return

    print("✓ imot.bg is accessible")

    # All checks passed - proceed with scraping
    print("\n✓✓✓ All pre-flight checks passed!")
    print("Starting scrape job...")

    # Here you would start your actual scraping logic
    # start_scrape_job(proxy_url=proxy_rotator_url)


def example_5_quality_monitoring_dashboard():
    """
    Example 5: Quality monitoring for dashboard.

    Shows how to collect quality metrics for display in
    a monitoring dashboard (e.g., Streamlit).
    """
    print("\n" + "=" * 60)
    print("Example 5: Quality Monitoring Dashboard")
    print("=" * 60)

    from proxies.quality_checker import enrich_proxies_batch

    # Simulated proxy pool
    proxy_pool = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http", "country": "BG"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http", "country": "RO"},
        {"host": "9.10.11.12", "port": 1080, "protocol": "socks5", "country": "BG"},
        {"host": "13.14.15.16", "port": 8888, "protocol": "http", "country": "TR"},
    ]

    print(f"\nMonitoring {len(proxy_pool)} proxies...")

    # Enrich with quality data
    enriched = enrich_proxies_batch(proxy_pool, timeout=10)

    # Calculate metrics
    total = len(enriched)
    google_pass_count = sum(1 for p in enriched if p.get("google_passed"))
    target_pass_count = sum(1 for p in enriched if p.get("target_passed"))
    premium_count = sum(
        1 for p in enriched
        if p.get("google_passed") and p.get("target_passed")
    )

    google_pass_rate = (google_pass_count / total * 100) if total > 0 else 0
    target_pass_rate = (target_pass_count / total * 100) if total > 0 else 0
    premium_rate = (premium_count / total * 100) if total > 0 else 0

    # Display dashboard-style metrics
    print(f"\n{'=' * 40}")
    print(f"PROXY QUALITY DASHBOARD")
    print(f"{'=' * 40}")
    print(f"\nOverall Statistics:")
    print(f"  Total proxies: {total}")
    print(f"  Premium quality: {premium_count} ({premium_rate:.1f}%)")
    print(f"\nGoogle Compatibility:")
    print(f"  Passed: {google_pass_count} ({google_pass_rate:.1f}%)")
    print(f"  Failed: {total - google_pass_count} ({100 - google_pass_rate:.1f}%)")
    print(f"\nTarget Site (imot.bg) Compatibility:")
    print(f"  Passed: {target_pass_count} ({target_pass_rate:.1f}%)")
    print(f"  Failed: {total - target_pass_count} ({100 - target_pass_rate:.1f}%)")

    # Country-wise breakdown
    print(f"\nBy Country:")
    countries = {}
    for proxy in enriched:
        country = proxy.get("country", "Unknown")
        if country not in countries:
            countries[country] = {"total": 0, "premium": 0}

        countries[country]["total"] += 1
        if proxy.get("google_passed") and proxy.get("target_passed"):
            countries[country]["premium"] += 1

    for country, stats in countries.items():
        premium_pct = (stats["premium"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {country}: {stats['premium']}/{stats['total']} premium ({premium_pct:.1f}%)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("QUALITY CHECKER INTEGRATION EXAMPLES")
    print("=" * 60)

    print("\nNOTE: These examples use placeholder proxies.")
    print("Replace with actual working proxies for real testing.")

    try:
        # Run all examples
        example_1_complete_validation_pipeline()
        example_2_batch_processing_with_filtering()
        example_3_selective_quality_check()
        # example_4_preflight_check_before_scraping()  # Interactive, skip in batch
        example_5_quality_monitoring_dashboard()

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
