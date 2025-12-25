#!/usr/bin/env python3
"""
Test script to verify ScoredProxyPool integration with main.py.

This script performs basic checks without running the full scraper.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported."""
    print("[TEST 1] Testing imports...")
    try:
        from main import scrape_from_start_url, run_auto_mode
        from proxies.proxy_scorer import ScoredProxyPool
        from paths import PROXIES_DIR
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_proxy_pool_initialization():
    """Test that ScoredProxyPool can be initialized."""
    print("\n[TEST 2] Testing ScoredProxyPool initialization...")
    try:
        from proxies.proxy_scorer import ScoredProxyPool
        from paths import PROXIES_DIR

        proxies_file = PROXIES_DIR / "live_proxies.json"
        if not proxies_file.exists():
            print(f"  ⚠ Skipping test: {proxies_file} does not exist")
            return True

        pool = ScoredProxyPool(proxies_file)
        stats = pool.get_stats()
        print(f"  ✓ Proxy pool initialized successfully")
        print(f"    - Total proxies: {stats['total_proxies']}")
        print(f"    - Average score: {stats['average_score']:.2f}")
        print(f"    - Proxies with failures: {stats['proxies_with_failures']}")
        return True
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return False


def test_record_result():
    """Test that record_result works with mubeng URL format."""
    print("\n[TEST 3] Testing record_result with mubeng URL...")
    try:
        from proxies.proxy_scorer import ScoredProxyPool
        from paths import PROXIES_DIR

        proxies_file = PROXIES_DIR / "live_proxies.json"
        if not proxies_file.exists():
            print(f"  ⚠ Skipping test: {proxies_file} does not exist")
            return True

        pool = ScoredProxyPool(proxies_file)

        # Test with mubeng URL format (as used in main.py)
        mubeng_url = "http://localhost:8089"

        # This should work even though mubeng_url is not in the pool
        # (it will log a warning and return gracefully)
        pool.record_result(mubeng_url, success=True)
        pool.record_result(mubeng_url, success=False)

        print(f"  ✓ record_result handles mubeng URL correctly")
        print(f"    Note: Mubeng URL is not tracked in pool (as expected)")
        return True
    except Exception as e:
        print(f"  ✗ record_result failed: {e}")
        return False


def test_function_signature():
    """Test that scrape_from_start_url has correct signature."""
    print("\n[TEST 4] Testing function signature...")
    try:
        import inspect
        from main import scrape_from_start_url

        sig = inspect.signature(scrape_from_start_url)
        params = list(sig.parameters.keys())

        expected_params = ['scraper', 'start_url', 'limit', 'proxy', 'proxy_pool']
        if params == expected_params:
            print(f"  ✓ Function signature is correct: {params}")
            return True
        else:
            print(f"  ✗ Unexpected signature: {params}")
            print(f"    Expected: {expected_params}")
            return False
    except Exception as e:
        print(f"  ✗ Signature check failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING SCOREDPROXYPOOL INTEGRATION")
    print("=" * 60)

    results = []
    results.append(test_imports())
    results.append(test_proxy_pool_initialization())
    results.append(test_record_result())
    results.append(test_function_signature())

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
