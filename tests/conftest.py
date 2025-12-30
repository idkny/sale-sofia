"""Pytest configuration for all tests.

Ensures project root is in sys.path for imports.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to sys.path
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def mock_proxy_functions(request):
    """Auto-mock proxy pool functions for tests that use scraping.tasks.

    This prevents tests from failing due to missing proxy files.
    Tests can still explicitly mock these functions if they need different behavior.
    """
    # Skip if the test explicitly patches these functions already
    markers = request.node.own_markers
    if any(m.name == "no_auto_proxy_mock" for m in markers):
        yield
        return

    # Only apply to test files that use scraping tasks
    test_file = str(request.fspath)
    if not any(name in test_file for name in [
        "test_scraping", "test_parallel_scraping", "test_circuit_breaker_celery",
        "test_site_config"
    ]):
        yield
        return

    # Create mock proxy pool
    mock_pool = MagicMock()
    mock_pool.proxies = []
    mock_pool.select_proxy.return_value = "http://test-proxy:8080"
    mock_pool.record_result = MagicMock()

    with patch("scraping.tasks.get_proxy_pool", return_value=mock_pool):
        with patch("scraping.tasks.get_working_proxy", return_value="http://test-proxy:8080"):
            yield
