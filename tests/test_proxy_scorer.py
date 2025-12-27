"""
Unit tests for the ScoredProxyPool runtime scoring system.

Tests cover:
- Proxy loading and initialization
- Score initialization from response times
- Weighted random selection
- Success/failure recording
- Auto-pruning behavior
- Thread safety
- Score persistence
"""

import json
import tempfile
import threading
import time
from pathlib import Path

import pytest

from proxies.proxy_scorer import (
    MAX_FAILURES,
    MIN_SCORE,
    SCORE_FAILURE_MULTIPLIER,
    SCORE_SUCCESS_MULTIPLIER,
    ScoredProxyPool,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_proxies():
    """Sample proxy data for testing."""
    return [
        {
            "protocol": "http",
            "host": "1.2.3.4",
            "port": 8080,
            "timeout": 0.5,  # Fast proxy
        },
        {
            "protocol": "http",
            "host": "5.6.7.8",
            "port": 3128,
            "timeout": 2.0,  # Slower proxy
        },
        {
            "protocol": "socks5",
            "host": "9.10.11.12",
            "port": 1080,
            "timeout": 1.0,  # Medium speed
        },
    ]


@pytest.fixture
def proxies_file(temp_dir, sample_proxies):
    """Create a temporary live_proxies.json file."""
    file_path = temp_dir / "live_proxies.json"
    with open(file_path, "w") as f:
        json.dump(sample_proxies, f)
    return file_path


@pytest.fixture
def proxy_pool(proxies_file):
    """Create a ScoredProxyPool instance for testing."""
    return ScoredProxyPool(proxies_file)


class TestProxyPoolInitialization:
    """Test proxy pool initialization and loading."""

    def test_load_proxies(self, proxy_pool, sample_proxies):
        """Test that proxies are loaded correctly."""
        assert len(proxy_pool.proxies) == len(sample_proxies)
        assert proxy_pool.proxies[0]["host"] == "1.2.3.4"

    def test_initialize_scores(self, proxy_pool):
        """Test that scores are initialized for all proxies."""
        assert len(proxy_pool.scores) == 3

        # Check score initialization based on response time
        # Fast proxy (0.5s) should have higher initial score than slow (2.0s)
        fast_score = proxy_pool.scores["1.2.3.4:8080"]["score"]
        slow_score = proxy_pool.scores["5.6.7.8:3128"]["score"]
        assert fast_score > slow_score

        # Score should be 1.0 / timeout
        assert fast_score == pytest.approx(1.0 / 0.5, rel=0.01)
        assert slow_score == pytest.approx(1.0 / 2.0, rel=0.01)

    def test_load_nonexistent_file(self, temp_dir):
        """Test handling of non-existent proxies file."""
        pool = ScoredProxyPool(temp_dir / "nonexistent.json")
        assert pool.proxies == []
        assert pool.scores == {}

    def test_load_invalid_json(self, temp_dir):
        """Test handling of invalid JSON file."""
        file_path = temp_dir / "invalid.json"
        with open(file_path, "w") as f:
            f.write("not valid json{")

        pool = ScoredProxyPool(file_path)
        assert pool.proxies == []


class TestProxySelection:
    """Test weighted proxy selection."""

    def test_select_proxy(self, proxy_pool):
        """Test that a proxy is selected."""
        proxy = proxy_pool.select_proxy()
        assert proxy is not None
        assert "host" in proxy
        assert "port" in proxy

    def test_select_proxy_weighted(self, proxy_pool):
        """Test that selection is weighted by score."""
        # Give one proxy a much higher score
        proxy_pool.scores["1.2.3.4:8080"]["score"] = 10.0
        proxy_pool.scores["5.6.7.8:3128"]["score"] = 0.1
        proxy_pool.scores["9.10.11.12:1080"]["score"] = 0.1

        # Select many times and count
        selections = {"1.2.3.4:8080": 0, "5.6.7.8:3128": 0, "9.10.11.12:1080": 0}

        for _ in range(100):
            proxy = proxy_pool.select_proxy()
            key = proxy_pool._get_proxy_key(proxy)
            selections[key] += 1

        # High-score proxy should be selected much more often
        assert selections["1.2.3.4:8080"] > selections["5.6.7.8:3128"]
        assert selections["1.2.3.4:8080"] > selections["9.10.11.12:1080"]

    def test_select_proxy_updates_last_used(self, proxy_pool):
        """Test that selection updates last_used timestamp."""
        before = time.time()
        proxy = proxy_pool.select_proxy()
        after = time.time()

        key = proxy_pool._get_proxy_key(proxy)
        last_used = proxy_pool.scores[key]["last_used"]

        assert last_used is not None
        assert before <= last_used <= after

    def test_get_proxy_url(self, proxy_pool):
        """Test get_proxy_url convenience method."""
        url = proxy_pool.get_proxy_url()
        assert url is not None
        assert "://" in url
        assert url.startswith("http://") or url.startswith("socks5://")


class TestScoreUpdates:
    """Test success/failure score updates."""

    def test_record_success(self, proxy_pool):
        """Test that success increases score and resets failures."""
        key = "1.2.3.4:8080"
        initial_score = proxy_pool.scores[key]["score"]

        proxy_pool.record_result(key, success=True)

        new_score = proxy_pool.scores[key]["score"]
        assert new_score == pytest.approx(initial_score * SCORE_SUCCESS_MULTIPLIER)
        assert proxy_pool.scores[key]["failures"] == 0

    def test_record_failure(self, proxy_pool):
        """Test that failure decreases score and increments failures."""
        key = "1.2.3.4:8080"
        initial_score = proxy_pool.scores[key]["score"]

        proxy_pool.record_result(key, success=False)

        new_score = proxy_pool.scores[key]["score"]
        assert new_score == pytest.approx(initial_score * SCORE_FAILURE_MULTIPLIER)
        assert proxy_pool.scores[key]["failures"] == 1

    def test_success_resets_failures(self, proxy_pool):
        """Test that success resets the failures counter."""
        key = "1.2.3.4:8080"

        # Record some failures
        proxy_pool.record_result(key, success=False)
        proxy_pool.record_result(key, success=False)
        assert proxy_pool.scores[key]["failures"] == 2

        # Success should reset to 0
        proxy_pool.record_result(key, success=True)
        assert proxy_pool.scores[key]["failures"] == 0

    def test_record_result_with_url_format(self, proxy_pool):
        """Test that record_result accepts both key and URL formats."""
        # Test with full URL format
        proxy_pool.record_result("http://1.2.3.4:8080", success=True)
        assert proxy_pool.scores["1.2.3.4:8080"]["failures"] == 0

        # Test with key format
        proxy_pool.record_result("1.2.3.4:8080", success=False)
        assert proxy_pool.scores["1.2.3.4:8080"]["failures"] == 1


class TestAutoPruning:
    """Test automatic proxy removal."""

    def test_auto_prune_on_max_failures(self, proxy_pool):
        """Test that proxy is removed after MAX_FAILURES."""
        key = "1.2.3.4:8080"
        initial_count = len(proxy_pool.proxies)

        # Record failures up to threshold
        for _ in range(MAX_FAILURES):
            proxy_pool.record_result(key, success=False)

        # Proxy should be removed
        assert len(proxy_pool.proxies) == initial_count - 1
        assert key not in proxy_pool.scores

    def test_auto_prune_on_low_score(self, proxy_pool):
        """Test that proxy is removed when score drops below MIN_SCORE."""
        key = "1.2.3.4:8080"
        initial_count = len(proxy_pool.proxies)

        # Set score low enough that after failure multiplier (0.5), it drops BELOW MIN_SCORE
        # 0.019 * 0.5 = 0.0095 < 0.01 (MIN_SCORE)
        proxy_pool.scores[key]["score"] = MIN_SCORE * 1.9

        # One more failure should trigger removal (score drops below MIN_SCORE)
        proxy_pool.record_result(key, success=False)

        # Proxy should be removed
        assert len(proxy_pool.proxies) == initial_count - 1
        assert key not in proxy_pool.scores

    def test_manual_remove_proxy(self, proxy_pool):
        """Test manual proxy removal."""
        key = "1.2.3.4:8080"
        initial_count = len(proxy_pool.proxies)

        removed = proxy_pool.remove_proxy(key)

        assert removed is True
        assert len(proxy_pool.proxies) == initial_count - 1
        assert key not in proxy_pool.scores

    def test_remove_nonexistent_proxy(self, proxy_pool):
        """Test removing a proxy that doesn't exist."""
        initial_count = len(proxy_pool.proxies)

        removed = proxy_pool.remove_proxy("999.999.999.999:9999")

        assert removed is False
        assert len(proxy_pool.proxies) == initial_count

    def test_remove_proxy_with_url_format(self, proxy_pool):
        """Test that remove_proxy accepts URL format."""
        initial_count = len(proxy_pool.proxies)

        removed = proxy_pool.remove_proxy("http://1.2.3.4:8080")

        assert removed is True
        assert len(proxy_pool.proxies) == initial_count - 1


class TestScorePersistence:
    """Test score saving and loading."""

    def test_save_scores(self, proxy_pool):
        """Test that scores are saved to file."""
        proxy_pool.save_scores()

        # Check that file was created
        assert proxy_pool.scores_file.exists()

        # Load and verify
        with open(proxy_pool.scores_file, "r") as f:
            saved_scores = json.load(f)

        assert len(saved_scores) == len(proxy_pool.scores)
        assert "1.2.3.4:8080" in saved_scores

    def test_load_scores(self, proxies_file):
        """Test that scores are loaded from file."""
        # Create a pool and modify scores
        pool1 = ScoredProxyPool(proxies_file)
        pool1.scores["1.2.3.4:8080"]["score"] = 5.5
        pool1.scores["1.2.3.4:8080"]["failures"] = 2
        pool1.save_scores()

        # Create new pool - should load saved scores
        pool2 = ScoredProxyPool(proxies_file)

        assert pool2.scores["1.2.3.4:8080"]["score"] == pytest.approx(5.5)
        assert pool2.scores["1.2.3.4:8080"]["failures"] == 2

    def test_scores_persist_across_updates(self, proxy_pool):
        """Test that score updates are persisted."""
        key = "1.2.3.4:8080"

        # Record success
        proxy_pool.record_result(key, success=True)
        new_score = proxy_pool.scores[key]["score"]

        # Load scores from file
        with open(proxy_pool.scores_file, "r") as f:
            saved_scores = json.load(f)

        assert saved_scores[key]["score"] == pytest.approx(new_score)


class TestThreadSafety:
    """Test thread-safe operations."""

    def test_concurrent_selections(self, proxy_pool):
        """Test that concurrent selections don't cause errors."""
        results = []

        def select_many():
            for _ in range(50):
                proxy = proxy_pool.select_proxy()
                if proxy:
                    results.append(proxy_pool._get_proxy_key(proxy))

        threads = [threading.Thread(target=select_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have selected many proxies without errors
        assert len(results) > 0

    def test_concurrent_updates(self, proxy_pool):
        """Test that concurrent score updates are safe."""
        keys = ["1.2.3.4:8080", "5.6.7.8:3128", "9.10.11.12:1080"]

        def update_many():
            for _ in range(50):
                key = keys[_ % len(keys)]
                success = (_ % 2 == 0)
                proxy_pool.record_result(key, success=success)

        threads = [threading.Thread(target=update_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All proxies should still exist with valid scores
        for key in keys:
            if key in proxy_pool.scores:
                assert proxy_pool.scores[key]["score"] >= 0


class TestUtilityMethods:
    """Test utility methods."""

    def test_get_stats(self, proxy_pool):
        """Test get_stats method."""
        stats = proxy_pool.get_stats()

        assert stats["total_proxies"] == 3
        assert stats["scored_proxies"] == 3
        assert stats["average_score"] > 0
        assert stats["proxies_with_failures"] == 0

        # Record a failure
        proxy_pool.record_result("1.2.3.4:8080", success=False)
        stats = proxy_pool.get_stats()
        assert stats["proxies_with_failures"] == 1

    def test_reload_proxies(self, proxy_pool, proxies_file):
        """Test reloading proxies from file."""
        initial_count = len(proxy_pool.proxies)

        # Modify the file to add a new proxy
        with open(proxies_file, "r") as f:
            proxies = json.load(f)

        proxies.append({
            "protocol": "http",
            "host": "13.14.15.16",
            "port": 8888,
            "timeout": 0.8,
        })

        with open(proxies_file, "w") as f:
            json.dump(proxies, f)

        # Reload
        proxy_pool.reload_proxies()

        assert len(proxy_pool.proxies) == initial_count + 1
        assert "13.14.15.16:8888" in proxy_pool.scores

    def test_get_proxy_key(self, proxy_pool):
        """Test _get_proxy_key method."""
        proxy = {"host": "1.2.3.4", "port": 8080}
        key = proxy_pool._get_proxy_key(proxy)
        assert key == "1.2.3.4:8080"

    def test_get_proxy_url(self, proxy_pool):
        """Test _get_proxy_url method."""
        proxy = {
            "protocol": "http",
            "host": "1.2.3.4",
            "port": 8080,
        }
        url = proxy_pool._get_proxy_url(proxy)
        assert url == "http://1.2.3.4:8080"

        proxy_socks = {
            "protocol": "socks5",
            "host": "5.6.7.8",
            "port": 1080,
        }
        url = proxy_pool._get_proxy_url(proxy_socks)
        assert url == "socks5://5.6.7.8:1080"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_proxy_pool(self, temp_dir):
        """Test behavior with empty proxy pool."""
        file_path = temp_dir / "empty.json"
        with open(file_path, "w") as f:
            json.dump([], f)

        pool = ScoredProxyPool(file_path)

        assert pool.select_proxy() is None
        assert pool.get_proxy_url() is None

    def test_proxy_without_timeout(self, temp_dir):
        """Test proxy without timeout field."""
        proxies = [{"protocol": "http", "host": "1.2.3.4", "port": 8080}]
        file_path = temp_dir / "no_timeout.json"
        with open(file_path, "w") as f:
            json.dump(proxies, f)

        pool = ScoredProxyPool(file_path)

        # Should default to score of 1.0
        assert pool.scores["1.2.3.4:8080"]["score"] == 1.0

    def test_record_result_unknown_proxy(self, proxy_pool):
        """Test recording result for unknown proxy."""
        # Should not raise error, just log warning
        proxy_pool.record_result("999.999.999.999:9999", success=True)

    def test_all_proxies_removed(self, proxy_pool):
        """Test behavior when all proxies are removed."""
        # Remove all proxies
        for proxy in list(proxy_pool.proxies):
            key = proxy_pool._get_proxy_key(proxy)
            proxy_pool.remove_proxy(key)

        assert len(proxy_pool.proxies) == 0
        assert proxy_pool.select_proxy() is None
