#!/usr/bin/env python3
"""
Solution F Integration Tests

Tests end-to-end behavior of:
- Proxy selection with X-Proxy-Offset
- Score tracking with actual proxy keys
- Persistence on removal
- Index synchronization after removal
"""

import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from proxies.proxy_scorer import ScoredProxyPool


def create_test_proxy_file(proxies_data: list[dict], temp_dir: Path) -> Path:
    """
    Create a temporary proxy JSON file for testing.

    Args:
        proxies_data: List of proxy dictionaries
        temp_dir: Temporary directory to create file in

    Returns:
        Path to created file
    """
    proxy_file = temp_dir / "test_proxies.json"
    with open(proxy_file, "w") as f:
        json.dump(proxies_data, f, indent=2)
    return proxy_file


def create_test_proxies(count: int, start_index: int = 0) -> list[dict]:
    """
    Create test proxy data.

    Args:
        count: Number of proxies to create
        start_index: Starting index for proxy numbering

    Returns:
        List of proxy dictionaries
    """
    return [
        {
            "protocol": "http",
            "host": f"192.168.{i}.100",
            "port": 8080,
            "timeout": 1.0
        }
        for i in range(start_index, start_index + count)
    ]


def test_mixed_proxy_pool():
    """
    Test 6.2: Mixed Proxy Pool Test

    Test with mix of working/failing proxies.
    - Setup: Create pool with 10 proxies
    - Simulate 7 working, 3 failing
    - Run mock "requests" and record results
    - Verify: scores updated correctly, bad proxies removed
    """
    print("\n" + "="*70)
    print("TEST 6.2: Mixed Proxy Pool Test")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 10 test proxies
        proxies = create_test_proxies(10)
        proxy_file = create_test_proxy_file(proxies, temp_path)

        # Initialize pool
        pool = ScoredProxyPool(proxy_file)

        # Define working proxies (indexes 0-6) and failing proxies (indexes 7-9)
        working_proxy_keys = [f"192.168.{i}.100:8080" for i in range(7)]
        failing_proxy_keys = [f"192.168.{i}.100:8080" for i in range(7, 10)]

        print(f"Initial proxies: {len(pool.proxies)}")
        print(f"Working proxies: {working_proxy_keys}")
        print(f"Failing proxies: {failing_proxy_keys}")

        # Simulate requests - working proxies succeed, failing proxies fail
        print("\nSimulating requests...")
        for _ in range(5):  # 5 rounds of requests
            for proxy_key in working_proxy_keys:
                pool.record_result(proxy_key, success=True)
            for proxy_key in failing_proxy_keys:
                pool.record_result(proxy_key, success=False)

        # Check that working proxies have higher scores
        print("\nScore Analysis:")
        for proxy_key in working_proxy_keys[:3]:  # Show first 3 working
            score_data = pool.scores.get(proxy_key, {})
            print(f"  {proxy_key}: score={score_data.get('score', 0):.3f}, "
                  f"failures={score_data.get('failures', 0)}")

        # Failing proxies should be removed (3 consecutive failures)
        print("\nFailing Proxy Status:")
        for proxy_key in failing_proxy_keys:
            if proxy_key in pool.scores:
                score_data = pool.scores[proxy_key]
                print(f"  {proxy_key}: STILL EXISTS - score={score_data['score']:.3f}, "
                      f"failures={score_data['failures']}")
            else:
                print(f"  {proxy_key}: REMOVED (as expected)")

        # Verify
        remaining_count = len(pool.proxies)
        removed_count = 10 - remaining_count

        print(f"\nResults: {removed_count} proxies removed, {remaining_count} remaining")

        assert remaining_count == 7, f"Expected 7 proxies, got {remaining_count}"
        assert removed_count == 3, f"Expected 3 removed, got {removed_count}"

        for key in failing_proxy_keys:
            assert key not in pool.scores, f"Failing proxy {key} should be removed"

        print("\n✓ Test PASSED: Bad proxies removed, good proxies retained")


def test_persistence_across_sessions():
    """
    Test 6.3: Persistence Across Sessions Test

    Test that removed proxies stay removed when mubeng proxy file is configured.
    - Create pool with 5 proxies
    - Set up mubeng proxy file and proxy order
    - Remove 1 proxy (updates mubeng file)
    - Create NEW pool from the UPDATED mubeng file
    - Verify: removed proxy not in new pool
    """
    print("\n" + "="*70)
    print("TEST 6.3: Persistence Across Sessions Test")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 5 test proxies
        proxies = create_test_proxies(5)
        proxy_file = create_test_proxy_file(proxies, temp_path)

        # Create mubeng proxy file (this is what mubeng reads)
        mubeng_file = temp_path / "mubeng_proxies.txt"

        # Session 1: Create pool and remove a proxy
        print("\nSession 1: Creating pool and removing proxy...")
        pool1 = ScoredProxyPool(proxy_file)
        initial_count = len(pool1.proxies)
        print(f"Initial proxy count: {initial_count}")

        # Set up Solution F features (proxy order and mubeng file)
        proxy_keys = [f"192.168.{i}.100:8080" for i in range(5)]
        pool1.set_proxy_order(proxy_keys)
        pool1.set_mubeng_proxy_file(mubeng_file)

        proxy_to_remove = "192.168.2.100:8080"  # Middle proxy
        print(f"Removing proxy: {proxy_to_remove}")
        removed = pool1.remove_proxy(proxy_to_remove)

        assert removed, f"Failed to remove proxy {proxy_to_remove}"
        assert len(pool1.proxies) == 4, f"Expected 4 proxies, got {len(pool1.proxies)}"

        print(f"Proxy count after removal: {len(pool1.proxies)}")
        print(f"Scores file saved: {pool1.scores_file}")

        # Verify mubeng file was updated
        with open(mubeng_file, 'r') as f:
            mubeng_lines = f.readlines()
        print(f"Mubeng file has {len(mubeng_lines)} proxies")

        # Session 2: Create new pool and manually load from updated mubeng file
        # (simulating what would happen when mubeng reloads)
        print("\nSession 2: Creating new pool from updated mubeng file...")

        # Read remaining proxies from mubeng file
        remaining_keys = [line.strip().replace('http://', '') for line in mubeng_lines]
        print(f"Remaining proxies in mubeng file: {remaining_keys}")

        # Create a new proxy JSON file with only remaining proxies
        remaining_proxies = [p for p in proxies if f"{p['host']}:{p['port']}" in remaining_keys]
        proxy_file2 = create_test_proxy_file(remaining_proxies, temp_path)

        pool2 = ScoredProxyPool(proxy_file2)

        print(f"New pool proxy count: {len(pool2.proxies)}")
        print(f"New pool scores count: {len(pool2.scores)}")

        # Verify removed proxy is NOT in new pool
        proxy_keys_in_pool = [pool2._get_proxy_key(p) for p in pool2.proxies]
        print(f"Proxy keys in new pool: {proxy_keys_in_pool}")

        assert proxy_to_remove not in pool2.scores, \
            f"Removed proxy {proxy_to_remove} should not be in scores"
        assert proxy_to_remove not in proxy_keys_in_pool, \
            f"Removed proxy {proxy_to_remove} should not be in proxy list"

        print("\n✓ Test PASSED: Removed proxy persisted across sessions")


def test_index_synchronization():
    """
    Test 6.4: Index Synchronization Test

    Test that indexes shift after removal.
    - Setup: 5 proxies [a, b, c, d, e] with indexes [0, 1, 2, 3, 4]
    - Remove proxy at index 2 ("c")
    - Verify: get_proxy_index("d") = 2 (was 3)
    - Verify: get_proxy_index("e") = 3 (was 4)
    """
    print("\n" + "="*70)
    print("TEST 6.4: Index Synchronization Test")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 5 test proxies
        proxies = create_test_proxies(5)
        proxy_file = create_test_proxy_file(proxies, temp_path)

        # Initialize pool
        pool = ScoredProxyPool(proxy_file)

        # Set up proxy order: a, b, c, d, e
        proxy_keys = [f"192.168.{i}.100:8080" for i in range(5)]
        pool.set_proxy_order(proxy_keys)

        print("\nInitial proxy order:")
        for i, key in enumerate(proxy_keys):
            index = pool.get_proxy_index(key)
            print(f"  [{i}] {key} -> index {index}")

        # Verify initial indexes
        assert pool.get_proxy_index(proxy_keys[0]) == 0, "Index 0 incorrect"
        assert pool.get_proxy_index(proxy_keys[2]) == 2, "Index 2 incorrect"
        assert pool.get_proxy_index(proxy_keys[3]) == 3, "Index 3 incorrect"
        assert pool.get_proxy_index(proxy_keys[4]) == 4, "Index 4 incorrect"

        # Remove proxy at index 2 (c)
        proxy_to_remove = proxy_keys[2]
        print(f"\nRemoving proxy at index 2: {proxy_to_remove}")
        pool.remove_proxy(proxy_to_remove)

        # Verify indexes shifted
        print("\nProxy order after removal:")
        remaining_keys = [k for k in proxy_keys if k != proxy_to_remove]
        for i, key in enumerate(remaining_keys):
            index = pool.get_proxy_index(key)
            print(f"  [{i}] {key} -> index {index}")

        # d and e should have shifted down
        d_index = pool.get_proxy_index(proxy_keys[3])
        e_index = pool.get_proxy_index(proxy_keys[4])

        print(f"\nIndex verification:")
        print(f"  'd' (was 3): now {d_index} (expected 2)")
        print(f"  'e' (was 4): now {e_index} (expected 3)")

        assert d_index == 2, f"Expected d at index 2, got {d_index}"
        assert e_index == 3, f"Expected e at index 3, got {e_index}"

        # Removed proxy should return None
        removed_index = pool.get_proxy_index(proxy_to_remove)
        assert removed_index is None, f"Removed proxy should return None, got {removed_index}"

        print("\n✓ Test PASSED: Indexes synchronized after removal")


def test_proxy_file_updated_on_removal():
    """
    Test that mubeng proxy file is updated when proxy removed.

    - Setup: Create pool with mubeng proxy file configured
    - Remove a proxy
    - Verify: mubeng file updated with remaining proxies
    """
    print("\n" + "="*70)
    print("TEST: Proxy File Updated on Removal")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 5 test proxies
        proxies = create_test_proxies(5)
        proxy_file = create_test_proxy_file(proxies, temp_path)

        # Create mubeng proxy file
        mubeng_file = temp_path / "mubeng_proxies.txt"

        # Initialize pool
        pool = ScoredProxyPool(proxy_file)

        # Set up proxy order and mubeng file
        proxy_keys = [f"192.168.{i}.100:8080" for i in range(5)]
        pool.set_proxy_order(proxy_keys)
        pool.set_mubeng_proxy_file(mubeng_file)

        # Manually trigger initial save
        pool._save_proxy_file()

        # Verify initial file
        with open(mubeng_file, "r") as f:
            initial_lines = f.readlines()

        print(f"\nInitial mubeng file ({len(initial_lines)} proxies):")
        for line in initial_lines:
            print(f"  {line.strip()}")

        assert len(initial_lines) == 5, f"Expected 5 proxies, got {len(initial_lines)}"

        # Remove a proxy
        proxy_to_remove = proxy_keys[2]
        print(f"\nRemoving proxy: {proxy_to_remove}")
        pool.remove_proxy(proxy_to_remove)

        # Verify file updated
        with open(mubeng_file, "r") as f:
            updated_lines = f.readlines()

        print(f"\nUpdated mubeng file ({len(updated_lines)} proxies):")
        for line in updated_lines:
            print(f"  {line.strip()}")

        assert len(updated_lines) == 4, f"Expected 4 proxies, got {len(updated_lines)}"

        # Verify removed proxy not in file
        removed_url = f"http://{proxy_to_remove}\n"
        assert removed_url not in updated_lines, \
            f"Removed proxy {removed_url.strip()} should not be in file"

        print("\n✓ Test PASSED: Mubeng proxy file updated on removal")


def test_get_proxy_index_with_url():
    """
    Test that get_proxy_index handles both "host:port" and full URL formats.
    """
    print("\n" + "="*70)
    print("TEST: Get Proxy Index with URL Format")
    print("="*70)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 3 test proxies
        proxies = create_test_proxies(3)
        proxy_file = create_test_proxy_file(proxies, temp_path)

        # Initialize pool
        pool = ScoredProxyPool(proxy_file)

        # Set up proxy order
        proxy_keys = [f"192.168.{i}.100:8080" for i in range(3)]
        pool.set_proxy_order(proxy_keys)

        # Test with "host:port" format
        key_format = proxy_keys[1]
        index1 = pool.get_proxy_index(key_format)
        print(f"\nUsing 'host:port' format: {key_format} -> index {index1}")

        # Test with full URL format
        url_format = f"http://{proxy_keys[1]}"
        index2 = pool.get_proxy_index(url_format)
        print(f"Using full URL format: {url_format} -> index {index2}")

        assert index1 == index2 == 1, \
            f"Both formats should return same index, got {index1} and {index2}"

        print("\n✓ Test PASSED: Both URL formats work correctly")


def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("SOLUTION F INTEGRATION TESTS")
    print("="*70)

    tests = [
        ("6.2: Mixed Proxy Pool", test_mixed_proxy_pool),
        ("6.3: Persistence Across Sessions", test_persistence_across_sessions),
        ("6.4: Index Synchronization", test_index_synchronization),
        ("Proxy File Update", test_proxy_file_updated_on_removal),
        ("Get Proxy Index with URL", test_get_proxy_index_with_url),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test ERROR: {test_name}")
            print(f"  Exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*70)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
