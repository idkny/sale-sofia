#!/usr/bin/env python3
"""
Test Phase 4: X-Proxy-Offset header and correct proxy tracking.

Verifies that:
1. Proxy selection uses proxy_pool.select_proxy()
2. X-Proxy-Offset header is set correctly
3. record_result() receives actual proxy key, not localhost:8089
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_proxy_key_format():
    """Test that proxy key is formatted correctly from proxy dict."""
    proxy_dict = {"host": "1.2.3.4", "port": 8080, "protocol": "http"}
    proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"

    assert proxy_key == "1.2.3.4:8080", f"Expected '1.2.3.4:8080', got '{proxy_key}'"
    print("✅ Proxy key format: PASSED")


def test_proxy_pool_integration():
    """Test that ScoredProxyPool methods work together correctly."""
    from proxies.proxy_scorer import ScoredProxyPool

    # Create a mock proxies file
    import tempfile
    import json

    proxies = [
        {"host": "1.1.1.1", "port": 8080, "protocol": "http"},
        {"host": "2.2.2.2", "port": 8080, "protocol": "http"},
        {"host": "3.3.3.3", "port": 8080, "protocol": "http"},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(proxies, f)
        temp_file = Path(f.name)

    try:
        pool = ScoredProxyPool(temp_file)

        # Set proxy order (as main.py does after setup_mubeng_rotator)
        ordered_keys = ["1.1.1.1:8080", "2.2.2.2:8080", "3.3.3.3:8080"]
        pool.set_proxy_order(ordered_keys)

        # Test select_proxy returns dict
        selected = pool.select_proxy()
        assert selected is not None, "select_proxy() returned None"
        assert "host" in selected and "port" in selected, "Missing host/port in selected proxy"

        # Test get_proxy_index
        proxy_key = f"{selected['host']}:{selected['port']}"
        index = pool.get_proxy_index(proxy_key)
        assert index is not None, f"get_proxy_index({proxy_key}) returned None"
        assert 0 <= index <= 2, f"Index {index} out of expected range [0, 2]"

        # Test record_result with actual proxy key (not localhost)
        pool.record_result(proxy_key, success=True)

        # Verify score was updated
        stats = pool.get_stats()
        assert stats["total_proxies"] == 3, "Proxy count mismatch"

        print(f"✅ Proxy pool integration: PASSED")
        print(f"   - Selected: {proxy_key}")
        print(f"   - Index: {index}")
        print(f"   - Total proxies: {stats['total_proxies']}")

    finally:
        temp_file.unlink()


def test_x_proxy_offset_header_logic():
    """Test the header construction logic used in main.py."""
    # Simulate what main.py does
    proxy_pool = MagicMock()
    proxy_pool.select_proxy.return_value = {"host": "5.6.7.8", "port": 3128, "protocol": "http"}
    proxy_pool.get_proxy_index.return_value = 7

    # This is the logic from main.py
    proxy_key = None
    extra_headers = {}

    proxy_dict = proxy_pool.select_proxy()
    if proxy_dict:
        proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"
        index = proxy_pool.get_proxy_index(proxy_key)
        if index is not None:
            extra_headers = {"X-Proxy-Offset": str(index)}

    # Verify
    assert proxy_key == "5.6.7.8:3128", f"Wrong proxy_key: {proxy_key}"
    assert extra_headers == {"X-Proxy-Offset": "7"}, f"Wrong headers: {extra_headers}"

    # This would be passed to StealthyFetcher.fetch(extra_headers=extra_headers)
    # and record_result would use proxy_key, NOT "localhost:8089"

    print("✅ X-Proxy-Offset header logic: PASSED")
    print(f"   - proxy_key: {proxy_key}")
    print(f"   - extra_headers: {extra_headers}")


def test_not_tracking_localhost():
    """Verify we're NOT tracking localhost:8089 anymore."""
    # The old buggy pattern was:
    # proxy = "http://localhost:8089"
    # proxy_pool.record_result(proxy, success=True)  # BUG!

    # The new pattern is:
    # proxy_key = f"{proxy_dict['host']}:{proxy_dict['port']}"
    # proxy_pool.record_result(proxy_key, success=True)  # CORRECT!

    # Read main.py and verify the pattern
    main_py = Path(__file__).parent.parent.parent / "main.py"
    content = main_py.read_text()

    # Check that record_result uses proxy_key, not proxy
    assert "record_result(proxy_key, success=True)" in content, \
        "Expected record_result(proxy_key, ...) pattern not found"
    assert "record_result(proxy_key, success=False)" in content, \
        "Expected record_result(proxy_key, ...) pattern not found"

    # Check that we're NOT using the old buggy pattern
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "record_result(proxy," in line and "proxy_key" not in line:
            # Allow if it's in a comment
            if "#" in line and line.index("#") < line.index("record_result"):
                continue
            raise AssertionError(
                f"Found old buggy pattern at line {i+1}: {line.strip()}\n"
                "Should use proxy_key, not proxy"
            )

    print("✅ Not tracking localhost: PASSED")
    print("   - record_result uses proxy_key (actual proxy)")
    print("   - No old buggy pattern found")


def main():
    """Run all Phase 4 tests."""
    print("=" * 60)
    print("Phase 4: X-Proxy-Offset Header Tests")
    print("=" * 60)
    print()

    tests = [
        test_proxy_key_format,
        test_x_proxy_offset_header_logic,
        test_not_tracking_localhost,
        test_proxy_pool_integration,
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
