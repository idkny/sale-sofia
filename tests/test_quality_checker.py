"""
Unit tests for proxies.quality_checker module.

Tests the QualityChecker class and helper functions for validating
proxy quality against Google and target sites.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from proxies.quality_checker import (
    GOOGLE_CAPTCHA_INDICATORS,
    IMOT_BG_INDICATORS,
    QualityChecker,
    enrich_proxies_batch,
    enrich_proxy_with_quality,
)


# --- Tests for QualityChecker.check_google ---


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_success(mock_httpx_client_class):
    """Test successful Google check without captcha."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Google Search Results</body></html>"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is True
    mock_client.get.assert_called_once()

    # Verify proxy configuration
    call_kwargs = mock_httpx_client_class.call_args.kwargs
    assert "proxies" in call_kwargs
    assert call_kwargs["proxies"]["http://"] == "http://1.2.3.4:8080"
    assert call_kwargs["proxies"]["https://"] == "http://1.2.3.4:8080"


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_captcha_detected(mock_httpx_client_class):
    """Test Google check fails when captcha is detected."""
    # Setup mock response with captcha indicator
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = (
        "<html><body>We've detected unusual traffic from your network</body></html>"
    )

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_captcha_detected_case_insensitive(mock_httpx_client_class):
    """Test captcha detection is case-insensitive."""
    # Setup mock response with uppercase captcha indicator
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>CAPTCHA verification required</body></html>"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_non_200_status(mock_httpx_client_class):
    """Test Google check fails on non-200 status."""
    # Setup mock response with 403 status
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_timeout(mock_httpx_client_class):
    """Test Google check fails on timeout."""
    # Setup mock client to raise timeout
    mock_client = Mock()
    mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_proxy_error(mock_httpx_client_class):
    """Test Google check fails on proxy error."""
    # Setup mock client to raise proxy error
    mock_client = Mock()
    mock_client.get.side_effect = httpx.ProxyError("Proxy connection failed")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_unexpected_exception(mock_httpx_client_class):
    """Test Google check handles unexpected exceptions gracefully."""
    # Setup mock client to raise unexpected exception
    mock_client = Mock()
    mock_client.get.side_effect = Exception("Unexpected error")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_google("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_google_all_captcha_indicators(mock_httpx_client_class):
    """Test that all captcha indicators are detected."""
    checker = QualityChecker(timeout=10)

    for indicator in GOOGLE_CAPTCHA_INDICATORS:
        # Setup mock response with current indicator
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"<html><body>Some text {indicator} more text</body></html>"

        # Setup mock client
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        result = checker.check_google("http://1.2.3.4:8080")

        assert result is False, f"Failed to detect indicator: {indicator}"


# --- Tests for QualityChecker.check_target_site ---


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_imot_bg_success(mock_httpx_client_class):
    """Test successful target site check for imot.bg."""
    # Setup mock response with imot.bg content
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '<html><body><title>imot.bg - Имоти</title></body></html>'

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_target_site("http://1.2.3.4:8080", "https://www.imot.bg")

    assert result is True
    mock_client.get.assert_called_once()


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_imot_bg_missing_content(mock_httpx_client_class):
    """Test target site check fails when expected content is missing."""
    # Setup mock response without expected content
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Some other website</body></html>"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_target_site("http://1.2.3.4:8080", "https://www.imot.bg")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_imot_bg_all_indicators(mock_httpx_client_class):
    """Test that all imot.bg indicators are recognized."""
    checker = QualityChecker(timeout=10)

    for indicator in IMOT_BG_INDICATORS:
        # Setup mock response with current indicator
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = f"<html><body>{indicator} content</body></html>"

        # Setup mock client
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_httpx_client_class.return_value.__enter__.return_value = mock_client

        result = checker.check_target_site("http://1.2.3.4:8080", "https://www.imot.bg")

        assert result is True, f"Failed to recognize indicator: {indicator}"


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_non_imot_url(mock_httpx_client_class):
    """Test target site check for non-imot.bg URL."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Example site</body></html>"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_target_site("http://1.2.3.4:8080", "https://www.example.com")

    # For non-imot.bg URLs, just 200 status is enough
    assert result is True


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_non_200_status(mock_httpx_client_class):
    """Test target site check fails on non-200 status."""
    # Setup mock response with 404 status
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_target_site("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_timeout(mock_httpx_client_class):
    """Test target site check fails on timeout."""
    # Setup mock client to raise timeout
    mock_client = Mock()
    mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_target_site("http://1.2.3.4:8080")

    assert result is False


@patch("proxies.quality_checker.httpx.Client")
def test_check_target_site_proxy_error(mock_httpx_client_class):
    """Test target site check fails on proxy error."""
    # Setup mock client to raise proxy error
    mock_client = Mock()
    mock_client.get.side_effect = httpx.ProxyError("Proxy connection failed")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    result = checker.check_target_site("http://1.2.3.4:8080")

    assert result is False


# --- Tests for QualityChecker.check_all ---


@patch.object(QualityChecker, "check_google")
@patch.object(QualityChecker, "check_target_site")
def test_check_all_both_pass(mock_check_target, mock_check_google):
    """Test check_all when both checks pass."""
    mock_check_google.return_value = True
    mock_check_target.return_value = True

    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results == {
        "google_passed": True,
        "target_passed": True,
    }

    mock_check_google.assert_called_once_with("http://1.2.3.4:8080")
    mock_check_target.assert_called_once_with("http://1.2.3.4:8080")


@patch.object(QualityChecker, "check_google")
@patch.object(QualityChecker, "check_target_site")
def test_check_all_google_fails(mock_check_target, mock_check_google):
    """Test check_all when Google check fails."""
    mock_check_google.return_value = False
    mock_check_target.return_value = True

    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results == {
        "google_passed": False,
        "target_passed": True,
    }


@patch.object(QualityChecker, "check_google")
@patch.object(QualityChecker, "check_target_site")
def test_check_all_target_fails(mock_check_target, mock_check_google):
    """Test check_all when target check fails."""
    mock_check_google.return_value = True
    mock_check_target.return_value = False

    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results == {
        "google_passed": True,
        "target_passed": False,
    }


@patch.object(QualityChecker, "check_google")
@patch.object(QualityChecker, "check_target_site")
def test_check_all_both_fail(mock_check_target, mock_check_google):
    """Test check_all when both checks fail."""
    mock_check_google.return_value = False
    mock_check_target.return_value = False

    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results == {
        "google_passed": False,
        "target_passed": False,
    }


# --- Tests for enrich_proxy_with_quality ---


@patch("proxies.quality_checker.QualityChecker")
@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_success(mock_time, mock_checker_class):
    """Test successful proxy enrichment with quality data."""
    # Mock time
    mock_time.return_value = 1703123456.789

    # Mock checker
    mock_checker = Mock()
    mock_checker.check_all.return_value = {
        "google_passed": True,
        "target_passed": True,
    }
    mock_checker_class.return_value = mock_checker

    proxy = {
        "host": "1.2.3.4",
        "port": 8080,
        "protocol": "http",
    }

    enriched = enrich_proxy_with_quality(proxy, timeout=15)

    assert enriched["host"] == "1.2.3.4"
    assert enriched["port"] == 8080
    assert enriched["protocol"] == "http"
    assert enriched["google_passed"] is True
    assert enriched["target_passed"] is True
    assert enriched["quality_checked_at"] == 1703123456.789

    mock_checker_class.assert_called_once_with(15)
    mock_checker.check_all.assert_called_once_with("http://1.2.3.4:8080")


@patch("proxies.quality_checker.QualityChecker")
@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_default_protocol(mock_time, mock_checker_class):
    """Test proxy enrichment defaults to http protocol."""
    mock_time.return_value = 1703123456.789

    mock_checker = Mock()
    mock_checker.check_all.return_value = {
        "google_passed": True,
        "target_passed": False,
    }
    mock_checker_class.return_value = mock_checker

    # Proxy without protocol specified
    proxy = {
        "host": "5.6.7.8",
        "port": 3128,
    }

    enriched = enrich_proxy_with_quality(proxy)

    assert enriched["google_passed"] is True
    assert enriched["target_passed"] is False
    mock_checker.check_all.assert_called_once_with("http://5.6.7.8:3128")


@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_missing_host(mock_time):
    """Test proxy enrichment handles missing host gracefully."""
    mock_time.return_value = 1703123456.789

    proxy = {
        "port": 8080,
        "protocol": "http",
    }

    enriched = enrich_proxy_with_quality(proxy)

    assert enriched["google_passed"] is None
    assert enriched["target_passed"] is None
    assert enriched["quality_checked_at"] == 1703123456.789


@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_missing_port(mock_time):
    """Test proxy enrichment handles missing port gracefully."""
    mock_time.return_value = 1703123456.789

    proxy = {
        "host": "1.2.3.4",
        "protocol": "http",
    }

    enriched = enrich_proxy_with_quality(proxy)

    assert enriched["google_passed"] is None
    assert enriched["target_passed"] is None
    assert enriched["quality_checked_at"] == 1703123456.789


@patch("proxies.quality_checker.QualityChecker")
@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_socks5(mock_time, mock_checker_class):
    """Test proxy enrichment with socks5 protocol."""
    mock_time.return_value = 1703123456.789

    mock_checker = Mock()
    mock_checker.check_all.return_value = {
        "google_passed": True,
        "target_passed": True,
    }
    mock_checker_class.return_value = mock_checker

    proxy = {
        "host": "1.2.3.4",
        "port": 1080,
        "protocol": "socks5",
    }

    enriched = enrich_proxy_with_quality(proxy)

    assert enriched["protocol"] == "socks5"
    mock_checker.check_all.assert_called_once_with("socks5://1.2.3.4:1080")


# --- Tests for enrich_proxies_batch ---


@patch("proxies.quality_checker.enrich_proxy_with_quality")
def test_enrich_proxies_batch_success(mock_enrich):
    """Test batch enrichment of multiple proxies."""

    def enrich_side_effect(proxy, timeout=15):
        proxy["google_passed"] = True
        proxy["target_passed"] = True
        proxy["quality_checked_at"] = time.time()
        return proxy

    mock_enrich.side_effect = enrich_side_effect

    proxies = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
    ]

    enriched = enrich_proxies_batch(proxies, timeout=10)

    assert len(enriched) == 2
    assert mock_enrich.call_count == 2

    # Verify each call
    mock_enrich.assert_any_call(proxies[0], timeout=10)
    mock_enrich.assert_any_call(proxies[1], timeout=10)


@patch("proxies.quality_checker.enrich_proxy_with_quality")
def test_enrich_proxies_batch_mixed_results(mock_enrich):
    """Test batch enrichment with mixed pass/fail results."""

    def enrich_side_effect(proxy, timeout=15):
        # First proxy passes both
        if proxy["port"] == 8080:
            proxy["google_passed"] = True
            proxy["target_passed"] = True
        # Second proxy fails target
        elif proxy["port"] == 3128:
            proxy["google_passed"] = True
            proxy["target_passed"] = False
        # Third proxy fails both
        else:
            proxy["google_passed"] = False
            proxy["target_passed"] = False

        proxy["quality_checked_at"] = time.time()
        return proxy

    mock_enrich.side_effect = enrich_side_effect

    proxies = [
        {"host": "1.2.3.4", "port": 8080, "protocol": "http"},
        {"host": "5.6.7.8", "port": 3128, "protocol": "http"},
        {"host": "9.10.11.12", "port": 1080, "protocol": "socks5"},
    ]

    enriched = enrich_proxies_batch(proxies)

    assert len(enriched) == 3
    assert mock_enrich.call_count == 3

    # First proxy passed both
    assert enriched[0]["google_passed"] is True
    assert enriched[0]["target_passed"] is True

    # Second proxy passed Google only
    assert enriched[1]["google_passed"] is True
    assert enriched[1]["target_passed"] is False

    # Third proxy failed both
    assert enriched[2]["google_passed"] is False
    assert enriched[2]["target_passed"] is False


@patch("proxies.quality_checker.enrich_proxy_with_quality")
def test_enrich_proxies_batch_empty_list(mock_enrich):
    """Test batch enrichment with empty proxy list."""
    proxies = []

    enriched = enrich_proxies_batch(proxies)

    assert len(enriched) == 0
    mock_enrich.assert_not_called()


# --- Integration Tests ---


@patch("proxies.quality_checker.httpx.Client")
def test_integration_quality_checker_workflow(mock_httpx_client_class):
    """Test complete workflow of quality checking."""
    # Mock Google check response (success)
    google_response = Mock()
    google_response.status_code = 200
    google_response.text = "<html>Google Search</html>"

    # Mock imot.bg check response (success)
    imot_response = Mock()
    imot_response.status_code = 200
    imot_response.text = '<html><title>imot.bg - Имоти</title></html>'

    # Setup mock client to return different responses
    mock_client = Mock()
    mock_client.get.side_effect = [google_response, imot_response]
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    # Create checker and run full check
    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results["google_passed"] is True
    assert results["target_passed"] is True
    assert mock_client.get.call_count == 2


@patch("proxies.quality_checker.httpx.Client")
@patch("proxies.quality_checker.time.time")
def test_integration_enrich_proxy_workflow(mock_time, mock_httpx_client_class):
    """Test complete workflow of enriching a proxy dict."""
    mock_time.return_value = 1703123456.789

    # Mock successful responses
    google_response = Mock()
    google_response.status_code = 200
    google_response.text = "<html>Google Search</html>"

    imot_response = Mock()
    imot_response.status_code = 200
    imot_response.text = '<html>imot.bg - Имоти</html>'

    mock_client = Mock()
    mock_client.get.side_effect = [google_response, imot_response]
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    # Original proxy dict
    proxy = {
        "host": "1.2.3.4",
        "port": 8080,
        "protocol": "http",
        "country": "BG",  # Extra field should be preserved
    }

    # Enrich proxy
    enriched = enrich_proxy_with_quality(proxy, timeout=15)

    # Verify original fields preserved
    assert enriched["host"] == "1.2.3.4"
    assert enriched["port"] == 8080
    assert enriched["protocol"] == "http"
    assert enriched["country"] == "BG"

    # Verify new fields added
    assert enriched["google_passed"] is True
    assert enriched["target_passed"] is True
    assert enriched["quality_checked_at"] == 1703123456.789


# --- Test Custom Timeout ---


@patch("proxies.quality_checker.httpx.Client")
def test_custom_timeout_configuration(mock_httpx_client_class):
    """Test that custom timeout is properly configured."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html>Google Search</html>"

    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    # Create checker with custom timeout
    checker = QualityChecker(timeout=30)
    checker.check_google("http://1.2.3.4:8080")

    # Verify timeout was passed to httpx Client
    call_kwargs = mock_httpx_client_class.call_args.kwargs
    assert call_kwargs["timeout"] == 30
