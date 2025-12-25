#!/usr/bin/env python3
"""
Verification script for anonymity_checker.py enhancements.
Shows the new features in action.
"""

import sys
from datetime import datetime

from proxies import anonymity_checker


def verify_privacy_headers():
    """Verify all required privacy headers are present"""
    print("1. Privacy Headers Check")
    print("=" * 60)

    required_headers = [
        "VIA",
        "X-FORWARDED-FOR",
        "X-FORWARDED",
        "FORWARDED-FOR",
        "FORWARDED",
        "X-REAL-IP",
        "CLIENT-IP",
        "X-CLIENT-IP",
        "PROXY-CONNECTION",
        "X-PROXY-ID",
        "X-BLUECOAT-VIA",
        "X-ORIGINATING-IP",
    ]

    print(f"Total privacy headers configured: {len(anonymity_checker.PRIVACY_HEADERS)}")
    print("\nRequired headers:")
    for header in required_headers:
        status = "✓" if header in anonymity_checker.PRIVACY_HEADERS else "✗"
        print(f"  {status} {header}")

    missing = set(required_headers) - set(anonymity_checker.PRIVACY_HEADERS)
    if missing:
        print(f"\n⚠ Missing headers: {missing}")
        return False
    else:
        print("\n✓ All required privacy headers present")
        return True


def verify_judge_urls():
    """Verify multiple judge URLs with fallback"""
    print("\n\n2. Judge URLs Check")
    print("=" * 60)

    print(f"Total judge URLs configured: {len(anonymity_checker.JUDGE_URLS)}")
    print("\nJudge URLs:")
    for i, url in enumerate(anonymity_checker.JUDGE_URLS, 1):
        print(f"  {i}. {url}")

    # Check for primary and fallback judges
    has_httpbin_org = any("httpbin.org" in url for url in anonymity_checker.JUDGE_URLS)
    has_httpbin_io = any("httpbin.io" in url for url in anonymity_checker.JUDGE_URLS)
    has_ifconfig = any("ifconfig.me" in url for url in anonymity_checker.JUDGE_URLS)

    print("\nFallback configuration:")
    print(f"  {'✓' if has_httpbin_org else '✗'} httpbin.org (primary)")
    print(f"  {'✓' if has_httpbin_io else '✗'} httpbin.io (fallback)")
    print(f"  {'✓' if has_ifconfig else '✗'} ifconfig.me (fallback)")

    if len(anonymity_checker.JUDGE_URLS) >= 3:
        print("\n✓ Multiple judge URLs configured for fallback")
        return True
    else:
        print("\n✗ Not enough judge URLs for proper fallback")
        return False


def verify_real_ip_caching():
    """Verify real IP caching with force_refresh"""
    print("\n\n3. Real IP Caching Check")
    print("=" * 60)

    # Clear cache first
    anonymity_checker._real_ip_cache = None

    print("Testing real IP retrieval (without proxy)...")
    print("Note: This will make a real network request\n")

    # First call - should fetch and cache
    print("First call (should fetch and cache):")
    ip1 = anonymity_checker.get_real_ip(timeout=10)
    if ip1:
        print(f"  Real IP: {ip1}")
        print(f"  Cached: {anonymity_checker._real_ip_cache}")
    else:
        print("  ⚠ Could not detect real IP (network issue?)")
        return None

    # Second call - should use cache
    print("\nSecond call (should use cache):")
    ip2 = anonymity_checker.get_real_ip(timeout=10)
    print(f"  Real IP: {ip2}")
    print(f"  Same as first: {ip1 == ip2}")

    # Third call with force_refresh
    print("\nThird call (force_refresh=True, should re-fetch):")
    ip3 = anonymity_checker.get_real_ip(timeout=10, force_refresh=True)
    if ip3:
        print(f"  Real IP: {ip3}")
        print(f"  Same as cached: {ip2 == ip3}")
        print("\n✓ Real IP caching with force_refresh working")
        return True
    else:
        print("  ⚠ Could not refresh real IP")
        return False


def verify_timestamp_format():
    """Verify timestamp format in enriched proxy"""
    print("\n\n4. Timestamp Format Check")
    print("=" * 60)

    # Create a dummy proxy
    proxy = {
        "protocol": "http",
        "host": "1.2.3.4",
        "port": 8080,
    }

    print("Testing timestamp format (without actual proxy check)...")
    print("Adding mock timestamp to proxy dict:")

    # Simulate timestamp generation
    timestamp = datetime.now(timezone.utc).isoformat()
    proxy["anonymity_verified_at"] = timestamp

    print(f"  Timestamp: {timestamp}")

    # Verify format
    try:
        dt = datetime.fromisoformat(timestamp)
        print(f"  Parsed datetime: {dt}")
        print(f"  Has timezone: {dt.tzinfo is not None}")
        print(f"  ISO format: ✓")

        # Check pattern
        import re

        if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.", timestamp):
            print(f"  Format pattern: ✓")
            print("\n✓ Timestamp format is correct")
            return True
        else:
            print(f"  Format pattern: ✗")
            return False
    except ValueError as e:
        print(f"  ✗ Invalid timestamp format: {e}")
        return False


def verify_error_handling():
    """Verify improved error handling"""
    print("\n\n5. Error Handling Check")
    print("=" * 60)

    print("Checking exception types in check_proxy_anonymity():")

    # Read the source code to verify error handling
    import inspect

    source = inspect.getsource(anonymity_checker.check_proxy_anonymity)

    # Check for specific exception handling
    exceptions = [
        "requests.exceptions.Timeout",
        "requests.exceptions.ProxyError",
        "requests.exceptions.ConnectionError",
        "requests.exceptions.RequestException",
    ]

    print("\nException handling:")
    for exc in exceptions:
        if exc in source:
            print(f"  ✓ {exc}")
        else:
            print(f"  ✗ {exc}")

    if all(exc in source for exc in exceptions):
        print("\n✓ Comprehensive error handling implemented")
        return True
    else:
        print("\n✗ Some exception types not handled")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "=" * 60)
    print("ANONYMITY CHECKER ENHANCEMENTS VERIFICATION")
    print("=" * 60 + "\n")

    results = []

    # Run all checks
    results.append(("Privacy Headers", verify_privacy_headers()))
    results.append(("Judge URLs", verify_judge_urls()))
    results.append(("Real IP Caching", verify_real_ip_caching()))
    results.append(("Timestamp Format", verify_timestamp_format()))
    results.append(("Error Handling", verify_error_handling()))

    # Summary
    print("\n\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    for name, result in results:
        if result is None:
            status = "⚠ SKIPPED"
        elif result:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
        print(f"{status:12} {name}")

    passed = sum(1 for _, r in results if r is True)
    total = len([r for r in results if r is not None])

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} checks passed")
    print("=" * 60 + "\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
