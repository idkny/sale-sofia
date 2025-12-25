"""
Unit tests for anonymity_checker.py
"""

import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from proxies import anonymity_checker


class TestGetRealIP:
    """Tests for get_real_ip function"""

    @patch("proxies.anonymity_checker.requests.get")
    def test_get_real_ip_success(self, mock_get):
        """Test successful real IP detection"""
        # Reset cache
        anonymity_checker._real_ip_cache = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "1.2.3.4\n"
        mock_get.return_value = mock_response

        ip = anonymity_checker.get_real_ip()

        assert ip == "1.2.3.4"
        assert anonymity_checker._real_ip_cache == "1.2.3.4"
        mock_get.assert_called_once()

    @patch("proxies.anonymity_checker.requests.get")
    def test_get_real_ip_cached(self, mock_get):
        """Test that real IP is cached and not fetched again"""
        anonymity_checker._real_ip_cache = "1.2.3.4"

        ip = anonymity_checker.get_real_ip()

        assert ip == "1.2.3.4"
        mock_get.assert_not_called()

    @patch("proxies.anonymity_checker.requests.get")
    def test_get_real_ip_force_refresh(self, mock_get):
        """Test force refresh bypasses cache"""
        anonymity_checker._real_ip_cache = "1.2.3.4"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "5.6.7.8"
        mock_get.return_value = mock_response

        ip = anonymity_checker.get_real_ip(force_refresh=True)

        assert ip == "5.6.7.8"
        assert anonymity_checker._real_ip_cache == "5.6.7.8"
        mock_get.assert_called_once()

    @patch("proxies.anonymity_checker.requests.get")
    def test_get_real_ip_fallback(self, mock_get):
        """Test fallback to next URL on failure"""
        anonymity_checker._real_ip_cache = None

        # First URL fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = "1.2.3.4"

        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            mock_response_success,
        ]

        ip = anonymity_checker.get_real_ip()

        assert ip == "1.2.3.4"
        assert mock_get.call_count == 2

    @patch("proxies.anonymity_checker.requests.get")
    def test_get_real_ip_all_fail(self, mock_get):
        """Test when all URLs fail"""
        anonymity_checker._real_ip_cache = None

        mock_get.side_effect = requests.exceptions.ConnectionError()

        ip = anonymity_checker.get_real_ip()

        assert ip is None
        assert mock_get.call_count == len(anonymity_checker.REAL_IP_URLS)

    @patch("proxies.anonymity_checker.requests.get")
    def test_get_real_ip_invalid_format(self, mock_get):
        """Test rejection of invalid IP format"""
        anonymity_checker._real_ip_cache = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "not-an-ip"
        mock_get.return_value = mock_response

        ip = anonymity_checker.get_real_ip()

        assert ip is None


class TestParseAnonymity:
    """Tests for parse_anonymity function"""

    def test_transparent_proxy(self):
        """Test detection of transparent proxy (real IP in response)"""
        response = '{"headers": {"X-Real-IP": "1.2.3.4"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Transparent"

    def test_anonymous_proxy_via_header(self):
        """Test detection of anonymous proxy via VIA header"""
        response = '{"headers": {"VIA": "1.1 proxy.example.com"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Anonymous"

    def test_anonymous_proxy_x_forwarded_for(self):
        """Test detection of anonymous proxy via X-Forwarded-For header"""
        response = '{"headers": {"X-Forwarded-For": "5.6.7.8"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Anonymous"

    def test_anonymous_proxy_x_client_ip(self):
        """Test detection of anonymous proxy via X-Client-IP header"""
        response = '{"headers": {"X-Client-IP": "5.6.7.8"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Anonymous"

    def test_anonymous_proxy_x_bluecoat_via(self):
        """Test detection of anonymous proxy via X-Bluecoat-Via header"""
        response = '{"headers": {"X-Bluecoat-Via": "proxy"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Anonymous"

    def test_elite_proxy(self):
        """Test detection of elite proxy (no privacy headers)"""
        response = '{"headers": {"User-Agent": "Mozilla/5.0"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Elite"

    def test_case_insensitive_header_check(self):
        """Test that header checking is case-insensitive"""
        response = '{"headers": {"via": "proxy", "x-forwarded-for": "5.6.7.8"}}'
        real_ip = "1.2.3.4"

        result = anonymity_checker.parse_anonymity(response, real_ip)

        assert result == "Anonymous"


class TestCheckProxyAnonymity:
    """Tests for check_proxy_anonymity function"""

    @patch("proxies.anonymity_checker.requests.get")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_check_proxy_anonymity_elite(self, mock_get_real_ip, mock_get):
        """Test checking elite proxy"""
        mock_get_real_ip.return_value = "1.2.3.4"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"headers": {"User-Agent": "Mozilla/5.0"}}'
        mock_get.return_value = mock_response

        result = anonymity_checker.check_proxy_anonymity("http://proxy:8080")

        assert result == "Elite"
        mock_get_real_ip.assert_called_once()

    @patch("proxies.anonymity_checker.requests.get")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_check_proxy_anonymity_transparent(self, mock_get_real_ip, mock_get):
        """Test checking transparent proxy"""
        mock_get_real_ip.return_value = "1.2.3.4"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"headers": {"X-Real-IP": "1.2.3.4"}}'
        mock_get.return_value = mock_response

        result = anonymity_checker.check_proxy_anonymity("http://proxy:8080")

        assert result == "Transparent"

    @patch("proxies.anonymity_checker.requests.get")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_check_proxy_anonymity_with_real_ip_provided(
        self, mock_get_real_ip, mock_get
    ):
        """Test when real IP is provided (should not fetch)"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"headers": {"User-Agent": "Mozilla/5.0"}}'
        mock_get.return_value = mock_response

        result = anonymity_checker.check_proxy_anonymity(
            "http://proxy:8080", real_ip="1.2.3.4"
        )

        assert result == "Elite"
        mock_get_real_ip.assert_not_called()

    @patch("proxies.anonymity_checker.requests.get")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_check_proxy_anonymity_no_real_ip(self, mock_get_real_ip, mock_get):
        """Test when real IP cannot be determined"""
        mock_get_real_ip.return_value = None

        result = anonymity_checker.check_proxy_anonymity("http://proxy:8080")

        assert result == "Anonymous"
        mock_get.assert_not_called()

    @patch("proxies.anonymity_checker.requests.get")
    def test_check_proxy_anonymity_judge_timeout(self, mock_get):
        """Test timeout handling with judge fallback"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"headers": {"User-Agent": "Mozilla/5.0"}}'

        # First judge times out, second succeeds
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            mock_response,
        ]

        result = anonymity_checker.check_proxy_anonymity(
            "http://proxy:8080", real_ip="1.2.3.4"
        )

        assert result == "Elite"
        assert mock_get.call_count == 2

    @patch("proxies.anonymity_checker.requests.get")
    def test_check_proxy_anonymity_proxy_error(self, mock_get):
        """Test proxy error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"headers": {"User-Agent": "Mozilla/5.0"}}'

        # First judge has proxy error, second succeeds
        mock_get.side_effect = [
            requests.exceptions.ProxyError(),
            mock_response,
        ]

        result = anonymity_checker.check_proxy_anonymity(
            "http://proxy:8080", real_ip="1.2.3.4"
        )

        assert result == "Elite"
        assert mock_get.call_count == 2

    @patch("proxies.anonymity_checker.requests.get")
    def test_check_proxy_anonymity_connection_error(self, mock_get):
        """Test connection error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"headers": {"User-Agent": "Mozilla/5.0"}}'

        # First judge has connection error, second succeeds
        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            mock_response,
        ]

        result = anonymity_checker.check_proxy_anonymity(
            "http://proxy:8080", real_ip="1.2.3.4"
        )

        assert result == "Elite"
        assert mock_get.call_count == 2

    @patch("proxies.anonymity_checker.requests.get")
    def test_check_proxy_anonymity_all_judges_fail(self, mock_get):
        """Test when all judge URLs fail"""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = anonymity_checker.check_proxy_anonymity(
            "http://proxy:8080", real_ip="1.2.3.4"
        )

        assert result is None
        assert mock_get.call_count == len(anonymity_checker.JUDGE_URLS)


class TestEnrichProxyWithAnonymity:
    """Tests for enrich_proxy_with_anonymity function"""

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    def test_enrich_proxy_with_anonymity_success(self, mock_check):
        """Test successful enrichment"""
        mock_check.return_value = "Elite"

        proxy = {
            "protocol": "http",
            "host": "1.2.3.4",
            "port": 8080,
        }

        result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

        assert result["anonymity"] == "Elite"
        assert "anonymity_verified_at" in result
        # Verify timestamp is ISO format
        datetime.fromisoformat(result["anonymity_verified_at"])

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    def test_enrich_proxy_missing_host(self, mock_check):
        """Test enrichment with missing host"""
        proxy = {
            "protocol": "http",
            "port": 8080,
        }

        result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

        assert result["anonymity"] is None
        assert result["anonymity_verified_at"] is None
        mock_check.assert_not_called()

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    def test_enrich_proxy_missing_port(self, mock_check):
        """Test enrichment with missing port"""
        proxy = {
            "protocol": "http",
            "host": "1.2.3.4",
        }

        result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

        assert result["anonymity"] is None
        assert result["anonymity_verified_at"] is None
        mock_check.assert_not_called()

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    def test_enrich_proxy_check_fails_with_exit_ip(self, mock_check):
        """Test fallback to exit_ip when check fails"""
        mock_check.return_value = None

        proxy = {
            "protocol": "http",
            "host": "1.2.3.4",
            "port": 8080,
            "exit_ip": "5.6.7.8",
        }

        result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

        assert result["anonymity"] == "Anonymous"
        assert "anonymity_verified_at" in result

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    def test_enrich_proxy_check_fails_same_exit_ip(self, mock_check):
        """Test fallback when exit_ip equals host"""
        mock_check.return_value = None

        proxy = {
            "protocol": "http",
            "host": "1.2.3.4",
            "port": 8080,
            "exit_ip": "1.2.3.4",
        }

        result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

        assert result["anonymity"] == "Transparent"
        assert "anonymity_verified_at" in result

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    def test_enrich_proxy_check_fails_no_exit_ip(self, mock_check):
        """Test fallback when no exit_ip available"""
        mock_check.return_value = None

        proxy = {
            "protocol": "http",
            "host": "1.2.3.4",
            "port": 8080,
        }

        result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

        assert result["anonymity"] == "Transparent"
        assert "anonymity_verified_at" in result

    def test_enrich_proxy_timestamp_format(self):
        """Test that timestamp is in correct ISO format with timezone"""
        with patch("proxies.anonymity_checker.check_proxy_anonymity") as mock_check:
            mock_check.return_value = "Elite"

            proxy = {
                "protocol": "http",
                "host": "1.2.3.4",
                "port": 8080,
            }

            result = anonymity_checker.enrich_proxy_with_anonymity(proxy)

            timestamp = result["anonymity_verified_at"]
            # Should be valid ISO format with timezone
            dt = datetime.fromisoformat(timestamp)
            assert dt.tzinfo is not None
            # Should match ISO format pattern
            assert re.match(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}", timestamp
            )


class TestCheckProxyAnonymityBatch:
    """Tests for check_proxy_anonymity_batch function"""

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_batch_check_success(self, mock_get_real_ip, mock_check):
        """Test batch anonymity checking"""
        mock_get_real_ip.return_value = "1.2.3.4"
        mock_check.side_effect = ["Elite", "Anonymous", "Transparent"]

        proxies = [
            {"protocol": "http", "host": "1.1.1.1", "port": 8080},
            {"protocol": "http", "host": "2.2.2.2", "port": 8080},
            {"protocol": "http", "host": "3.3.3.3", "port": 8080},
        ]

        result = anonymity_checker.check_proxy_anonymity_batch(proxies)

        assert result[0]["anonymity"] == "Elite"
        assert result[1]["anonymity"] == "Anonymous"
        assert result[2]["anonymity"] == "Transparent"
        mock_get_real_ip.assert_called_once()

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_batch_check_with_missing_data(self, mock_get_real_ip, mock_check):
        """Test batch checking with missing proxy data"""
        mock_get_real_ip.return_value = "1.2.3.4"

        proxies = [
            {"protocol": "http", "port": 8080},  # Missing host
            {"protocol": "http", "host": "2.2.2.2"},  # Missing port
        ]

        result = anonymity_checker.check_proxy_anonymity_batch(proxies)

        assert result[0]["anonymity"] is None
        assert result[1]["anonymity"] is None
        mock_check.assert_not_called()

    @patch("proxies.anonymity_checker.check_proxy_anonymity")
    @patch("proxies.anonymity_checker.get_real_ip")
    def test_batch_check_with_failures(self, mock_get_real_ip, mock_check):
        """Test batch checking with some failures"""
        mock_get_real_ip.return_value = "1.2.3.4"
        mock_check.side_effect = ["Elite", None]

        proxies = [
            {"protocol": "http", "host": "1.1.1.1", "port": 8080},
            {
                "protocol": "http",
                "host": "2.2.2.2",
                "port": 8080,
                "exit_ip": "5.6.7.8",
            },
        ]

        result = anonymity_checker.check_proxy_anonymity_batch(proxies)

        assert result[0]["anonymity"] == "Elite"
        # Second failed check, fallback to exit_ip comparison
        assert result[1]["anonymity"] == "Anonymous"


class TestPrivacyHeaders:
    """Tests for PRIVACY_HEADERS constant"""

    def test_all_privacy_headers_present(self):
        """Test that all required privacy headers are defined"""
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

        for header in required_headers:
            assert (
                header in anonymity_checker.PRIVACY_HEADERS
            ), f"Header {header} missing from PRIVACY_HEADERS"

    def test_privacy_headers_uppercase(self):
        """Test that all privacy headers are uppercase"""
        for header in anonymity_checker.PRIVACY_HEADERS:
            assert header == header.upper(), f"Header {header} should be uppercase"


class TestJudgeUrls:
    """Tests for JUDGE_URLS constant"""

    def test_multiple_judge_urls(self):
        """Test that multiple judge URLs are configured for fallback"""
        assert len(anonymity_checker.JUDGE_URLS) >= 3, "Should have at least 3 judge URLs for reliability"

    def test_judge_urls_include_primary_and_fallbacks(self):
        """Test that primary and fallback judges are present"""
        # Should have httpbin.org as primary
        assert any(
            "httpbin.org" in url for url in anonymity_checker.JUDGE_URLS
        ), "Should include httpbin.org"

        # Should have httpbin.io as fallback
        assert any(
            "httpbin.io" in url for url in anonymity_checker.JUDGE_URLS
        ), "Should include httpbin.io"

        # Should have ifconfig.me as fallback
        assert any(
            "ifconfig.me" in url for url in anonymity_checker.JUDGE_URLS
        ), "Should include ifconfig.me"
