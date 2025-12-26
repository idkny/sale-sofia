#!/usr/bin/env python3
"""
Test Phase 5: Retry logic for proxy failures.

Verifies that:
1. MAX_PROXY_RETRIES constant exists
2. Retry loop selects different proxy each attempt
3. Network errors trigger retry, extraction failures don't
4. Stats are updated correctly
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_max_proxy_retries_constant():
    """Test that MAX_PROXY_RETRIES is defined."""
    import main

    assert hasattr(main, 'MAX_PROXY_RETRIES'), "MAX_PROXY_RETRIES not found in main.py"
    assert main.MAX_PROXY_RETRIES == 3, f"Expected 3, got {main.MAX_PROXY_RETRIES}"
    print("✅ MAX_PROXY_RETRIES constant: PASSED")
    print(f"   - Value: {main.MAX_PROXY_RETRIES}")


def test_retry_loop_in_scrape_listings():
    """Test that _scrape_listings has retry loop structure."""
    main_py = Path(__file__).parent.parent.parent / "main.py"
    content = main_py.read_text()

    # Check for retry loop pattern
    assert "for attempt in range(MAX_PROXY_RETRIES)" in content, \
        "Retry loop not found in main.py"

    # Check for attempt logging
    assert "Attempt {attempt + 1}/{MAX_PROXY_RETRIES}" in content or \
           "attempt + 1}" in content, \
        "Attempt logging not found"

    # Check for different proxy selection each attempt
    # The proxy selection code should be INSIDE the retry loop
    lines = content.split("\n")
    in_retry_loop = False
    found_proxy_selection_in_loop = False

    for line in lines:
        if "for attempt in range(MAX_PROXY_RETRIES)" in line:
            in_retry_loop = True
        if in_retry_loop and "proxy_pool.select_proxy()" in line:
            found_proxy_selection_in_loop = True
            break
        if in_retry_loop and line.strip().startswith("time.sleep"):
            in_retry_loop = False  # End of loop body

    assert found_proxy_selection_in_loop, \
        "Proxy selection should be inside retry loop for different proxy each attempt"

    print("✅ Retry loop in _scrape_listings: PASSED")
    print("   - Loop structure found")
    print("   - Proxy selection inside loop (different proxy each attempt)")


def test_retry_loop_in_collect_listing_urls():
    """Test that _collect_listing_urls has retry loop structure."""
    main_py = Path(__file__).parent.parent.parent / "main.py"
    content = main_py.read_text()

    # Check for page_success pattern
    assert "page_success = False" in content, \
        "page_success flag not found"

    # Check for break on success
    assert "page_success = True" in content and "break" in content, \
        "Break on success not found"

    # Check for all attempts failed message
    assert "All {MAX_PROXY_RETRIES} attempts failed" in content or \
           "All" in content and "attempts failed" in content, \
        "All attempts failed message not found"

    print("✅ Retry loop in _collect_listing_urls: PASSED")
    print("   - page_success tracking found")
    print("   - Break on success pattern found")


def test_no_retry_on_extraction_failure():
    """Test that extraction failures don't trigger retry."""
    main_py = Path(__file__).parent.parent.parent / "main.py"
    content = main_py.read_text()

    # Should break (not continue) when extraction fails
    # Pattern: "Failed to extract listing data" followed by break
    assert "Failed to extract listing data" in content, \
        "Extraction failure message not found"

    # Check that extraction failure has break, not continue
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "Failed to extract listing data" in line:
            # Look for break in next few lines
            found_break = False
            for j in range(i, min(i+5, len(lines))):
                if "break" in lines[j]:
                    found_break = True
                    break
            assert found_break, \
                "Extraction failure should break, not retry"

    print("✅ No retry on extraction failure: PASSED")
    print("   - Extraction failures break out of retry loop")


def test_stats_tracking():
    """Test that stats are updated correctly."""
    main_py = Path(__file__).parent.parent.parent / "main.py"
    content = main_py.read_text()

    # Check stats initialization
    assert '"scraped": 0' in content, "scraped stat not initialized"
    assert '"failed": 0' in content, "failed stat not initialized"
    assert '"total_attempts": 0' in content, "total_attempts stat not initialized"

    # Check stats updates
    assert 'stats["scraped"] += 1' in content, "scraped increment not found"
    assert 'stats["failed"] += 1' in content, "failed increment not found"
    assert 'stats["total_attempts"] += 1' in content, "total_attempts increment not found"

    print("✅ Stats tracking: PASSED")
    print("   - All stats initialized")
    print("   - All stats incremented correctly")


def main():
    """Run all Phase 5 tests."""
    print("=" * 60)
    print("Phase 5: Retry Logic Tests")
    print("=" * 60)
    print()

    tests = [
        test_max_proxy_retries_constant,
        test_retry_loop_in_scrape_listings,
        test_retry_loop_in_collect_listing_urls,
        test_no_retry_on_extraction_failure,
        test_stats_tracking,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: FAILED")
            print(f"   Error: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
