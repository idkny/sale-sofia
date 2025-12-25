"""
Unit tests for proxies.quality_checker module.

Tests the QualityChecker class and helper functions for validating
proxy quality against IP check services and target sites.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from proxies.quality_checker import (
    IMOT_BG_INDICATORS,
    IP_CHECK_SERVICES,
    QualityChecker,
    enrich_proxies_batch,
    enrich_proxy_with_quality,
)


# --- Tests for QualityChecker._fetch_ip_from_service ---


@patch("proxies.quality_checker.httpx.Client")
def test_fetch_ip_from_service_json_success(mock_httpx_client_class):
    """Test fetching IP from JSON-based service."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ip": "1.2.3.4"}

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    service = {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"}
    result = checker._fetch_ip_from_service("http://1.2.3.4:8080", service)

    assert result == "1.2.3.4"
    mock_client.get.assert_called_once()


@patch("proxies.quality_checker.httpx.Client")
def test_fetch_ip_from_service_text_success(mock_httpx_client_class):
    """Test fetching IP from text-based service."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "5.6.7.8\n"

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    service = {"url": "https://icanhazip.com", "type": "text"}
    result = checker._fetch_ip_from_service("http://1.2.3.4:8080", service)

    assert result == "5.6.7.8"


@patch("proxies.quality_checker.httpx.Client")
def test_fetch_ip_from_service_non_200_status(mock_httpx_client_class):
    """Test fetching IP returns None on non-200 status."""
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 403

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    service = {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"}
    result = checker._fetch_ip_from_service("http://1.2.3.4:8080", service)

    assert result is None


@patch("proxies.quality_checker.httpx.Client")
def test_fetch_ip_from_service_timeout(mock_httpx_client_class):
    """Test fetching IP returns None on timeout."""
    # Setup mock client to raise timeout
    mock_client = Mock()
    mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    service = {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"}
    result = checker._fetch_ip_from_service("http://1.2.3.4:8080", service)

    assert result is None


@patch("proxies.quality_checker.httpx.Client")
def test_fetch_ip_from_service_proxy_error(mock_httpx_client_class):
    """Test fetching IP returns None on proxy error."""
    # Setup mock client to raise proxy error
    mock_client = Mock()
    mock_client.get.side_effect = httpx.ProxyError("Proxy connection failed")
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    service = {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"}
    result = checker._fetch_ip_from_service("http://1.2.3.4:8080", service)

    assert result is None


@patch("proxies.quality_checker.httpx.Client")
def test_fetch_ip_from_service_json_decode_error(mock_httpx_client_class):
    """Test fetching IP returns None on JSON decode error."""
    # Setup mock response with invalid JSON
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("Invalid JSON")

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    checker = QualityChecker(timeout=10)
    service = {"url": "https://api.ipify.org?format=json", "type": "json", "key": "ip"}
    result = checker._fetch_ip_from_service("http://1.2.3.4:8080", service)

    assert result is None


# --- Tests for QualityChecker._is_valid_proxy_ip ---


@patch("proxies.quality_checker.get_real_ip")
def test_is_valid_proxy_ip_valid(mock_get_real_ip):
    """Test valid IP returns True."""
    mock_get_real_ip.return_value = "10.0.0.1"

    checker = QualityChecker(timeout=10)
    result = checker._is_valid_proxy_ip("1.2.3.4")

    assert result is True


@patch("proxies.quality_checker.get_real_ip")
def test_is_valid_proxy_ip_too_short(mock_get_real_ip):
    """Test too short string returns False."""
    mock_get_real_ip.return_value = "10.0.0.1"

    checker = QualityChecker(timeout=10)
    result = checker._is_valid_proxy_ip("1.2.3")

    assert result is False


@patch("proxies.quality_checker.get_real_ip")
def test_is_valid_proxy_ip_no_dot(mock_get_real_ip):
    """Test string without dot returns False."""
    mock_get_real_ip.return_value = "10.0.0.1"

    checker = QualityChecker(timeout=10)
    result = checker._is_valid_proxy_ip("invalid")

    assert result is False


@patch("proxies.quality_checker.get_real_ip")
def test_is_valid_proxy_ip_empty(mock_get_real_ip):
    """Test empty string returns False."""
    mock_get_real_ip.return_value = "10.0.0.1"

    checker = QualityChecker(timeout=10)
    result = checker._is_valid_proxy_ip("")

    assert result is False


@patch("proxies.quality_checker.get_real_ip")
def test_is_valid_proxy_ip_matches_real_ip_subnet(mock_get_real_ip):
    """Test IP matching real IP subnet returns False."""
    mock_get_real_ip.return_value = "10.0.0.1"

    checker = QualityChecker(timeout=10)
    result = checker._is_valid_proxy_ip("10.0.0.5")

    assert result is False


# --- Tests for QualityChecker.check_ip_service ---


@patch.object(QualityChecker, "_is_valid_proxy_ip")
@patch.object(QualityChecker, "_fetch_ip_from_service")
def test_check_ip_service_first_service_succeeds(mock_fetch, mock_is_valid):
    """Test first service succeeds returns True with IP."""
    mock_fetch.return_value = "1.2.3.4"
    mock_is_valid.return_value = True

    checker = QualityChecker(timeout=10)
    passed, ip = checker.check_ip_service("http://1.2.3.4:8080")

    assert passed is True
    assert ip == "1.2.3.4"
    # Should only call first service
    assert mock_fetch.call_count == 1


@patch.object(QualityChecker, "_is_valid_proxy_ip")
@patch.object(QualityChecker, "_fetch_ip_from_service")
def test_check_ip_service_first_fails_second_succeeds(mock_fetch, mock_is_valid):
    """Test first service fails, second succeeds."""
    # First service returns None, second returns IP
    mock_fetch.side_effect = [None, "5.6.7.8"]
    mock_is_valid.return_value = True

    checker = QualityChecker(timeout=10)
    passed, ip = checker.check_ip_service("http://1.2.3.4:8080")

    assert passed is True
    assert ip == "5.6.7.8"
    assert mock_fetch.call_count == 2


@patch.object(QualityChecker, "_is_valid_proxy_ip")
@patch.object(QualityChecker, "_fetch_ip_from_service")
def test_check_ip_service_all_services_fail(mock_fetch, mock_is_valid):
    """Test all services fail returns False, None."""
    mock_fetch.return_value = None
    mock_is_valid.return_value = True

    checker = QualityChecker(timeout=10)
    passed, ip = checker.check_ip_service("http://1.2.3.4:8080")

    assert passed is False
    assert ip is None
    # Should try all services
    assert mock_fetch.call_count == len(IP_CHECK_SERVICES)


@patch.object(QualityChecker, "_is_valid_proxy_ip")
@patch.object(QualityChecker, "_fetch_ip_from_service")
def test_check_ip_service_invalid_ip_continues(mock_fetch, mock_is_valid):
    """Test invalid IP (matches real IP) continues to next service."""
    # First service returns IP matching real IP, second returns valid IP
    mock_fetch.side_effect = ["10.0.0.5", "1.2.3.4"]
    # First IP invalid (matches real IP), second valid
    mock_is_valid.side_effect = [False, True]

    checker = QualityChecker(timeout=10)
    passed, ip = checker.check_ip_service("http://1.2.3.4:8080")

    assert passed is True
    assert ip == "1.2.3.4"
    assert mock_fetch.call_count == 2
    assert mock_is_valid.call_count == 2


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


@patch.object(QualityChecker, "check_ip_service")
def test_check_all_ip_check_passes(mock_check_ip):
    """Test check_all when IP check passes."""
    mock_check_ip.return_value = (True, "1.2.3.4")

    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results == {
        "ip_check_passed": True,
        "ip_check_exit_ip": "1.2.3.4",
        "target_passed": None,
    }

    mock_check_ip.assert_called_once_with("http://1.2.3.4:8080")


@patch.object(QualityChecker, "check_ip_service")
def test_check_all_ip_check_fails(mock_check_ip):
    """Test check_all when IP check fails."""
    mock_check_ip.return_value = (False, None)

    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results == {
        "ip_check_passed": False,
        "ip_check_exit_ip": None,
        "target_passed": None,
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
        "ip_check_passed": True,
        "ip_check_exit_ip": "1.2.3.4",
        "target_passed": None,
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
    assert enriched["ip_check_passed"] is True
    assert enriched["ip_check_exit_ip"] == "1.2.3.4"
    assert enriched["target_passed"] is None
    assert enriched["quality_checked_at"] == 1703123456.789

    mock_checker_class.assert_called_once_with(timeout=15)
    mock_checker.check_all.assert_called_once_with("http://1.2.3.4:8080")


@patch("proxies.quality_checker.QualityChecker")
@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_default_protocol(mock_time, mock_checker_class):
    """Test proxy enrichment defaults to http protocol."""
    mock_time.return_value = 1703123456.789

    mock_checker = Mock()
    mock_checker.check_all.return_value = {
        "ip_check_passed": True,
        "ip_check_exit_ip": "5.6.7.8",
        "target_passed": None,
    }
    mock_checker_class.return_value = mock_checker

    # Proxy without protocol specified
    proxy = {
        "host": "5.6.7.8",
        "port": 3128,
    }

    enriched = enrich_proxy_with_quality(proxy)

    assert enriched["ip_check_passed"] is True
    assert enriched["ip_check_exit_ip"] == "5.6.7.8"
    assert enriched["target_passed"] is None
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

    assert enriched["ip_check_passed"] is None
    assert enriched["ip_check_exit_ip"] is None
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

    assert enriched["ip_check_passed"] is None
    assert enriched["ip_check_exit_ip"] is None
    assert enriched["target_passed"] is None
    assert enriched["quality_checked_at"] == 1703123456.789


@patch("proxies.quality_checker.QualityChecker")
@patch("proxies.quality_checker.time.time")
def test_enrich_proxy_with_quality_socks5(mock_time, mock_checker_class):
    """Test proxy enrichment with socks5 protocol."""
    mock_time.return_value = 1703123456.789

    mock_checker = Mock()
    mock_checker.check_all.return_value = {
        "ip_check_passed": True,
        "ip_check_exit_ip": "1.2.3.4",
        "target_passed": None,
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
        proxy["ip_check_passed"] = True
        proxy["ip_check_exit_ip"] = proxy["host"]
        proxy["target_passed"] = None
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
        # First proxy passes
        if proxy["port"] == 8080:
            proxy["ip_check_passed"] = True
            proxy["ip_check_exit_ip"] = proxy["host"]
        # Second proxy fails
        elif proxy["port"] == 3128:
            proxy["ip_check_passed"] = False
            proxy["ip_check_exit_ip"] = None
        # Third proxy passes
        else:
            proxy["ip_check_passed"] = True
            proxy["ip_check_exit_ip"] = proxy["host"]

        proxy["target_passed"] = None
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

    # First proxy passed
    assert enriched[0]["ip_check_passed"] is True
    assert enriched[0]["ip_check_exit_ip"] == "1.2.3.4"

    # Second proxy failed
    assert enriched[1]["ip_check_passed"] is False
    assert enriched[1]["ip_check_exit_ip"] is None

    # Third proxy passed
    assert enriched[2]["ip_check_passed"] is True
    assert enriched[2]["ip_check_exit_ip"] == "9.10.11.12"


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
    # Mock IP check response (success)
    ip_response = Mock()
    ip_response.status_code = 200
    ip_response.json.return_value = {"ip": "1.2.3.4"}

    # Setup mock client
    mock_client = Mock()
    mock_client.get.return_value = ip_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    # Create checker and run full check
    checker = QualityChecker(timeout=10)
    results = checker.check_all("http://1.2.3.4:8080")

    assert results["ip_check_passed"] is True
    assert results["ip_check_exit_ip"] == "1.2.3.4"
    assert results["target_passed"] is None
    # Should try at least one IP service
    assert mock_client.get.call_count >= 1


@patch("proxies.quality_checker.httpx.Client")
@patch("proxies.quality_checker.time.time")
@patch("proxies.quality_checker.get_real_ip")
def test_integration_enrich_proxy_workflow(mock_get_real_ip, mock_time, mock_httpx_client_class):
    """Test complete workflow of enriching a proxy dict."""
    mock_time.return_value = 1703123456.789
    mock_get_real_ip.return_value = "10.0.0.1"

    # Mock successful IP check response
    ip_response = Mock()
    ip_response.status_code = 200
    ip_response.json.return_value = {"ip": "1.2.3.4"}

    mock_client = Mock()
    mock_client.get.return_value = ip_response
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
    assert enriched["ip_check_passed"] is True
    assert enriched["ip_check_exit_ip"] == "1.2.3.4"
    assert enriched["target_passed"] is None
    assert enriched["quality_checked_at"] == 1703123456.789


# --- Test Custom Timeout ---


@patch("proxies.quality_checker.httpx.Client")
def test_custom_timeout_configuration(mock_httpx_client_class):
    """Test that custom timeout is properly configured."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "1.2.3.4"

    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_httpx_client_class.return_value.__enter__.return_value = mock_client

    # Create checker with custom timeout
    checker = QualityChecker(timeout=30)
    checker.check_target_site("http://1.2.3.4:8080")

    # Verify timeout was passed to httpx Client
    call_kwargs = mock_httpx_client_class.call_args.kwargs
    assert call_kwargs["timeout"] == 30
