"""Unit tests for resilience Phase 1 modules.

Tests the exception hierarchy, error classifier, and retry decorators.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from resilience.exceptions import (
    ScraperException,
    NetworkException,
    RateLimitException,
    BlockedException,
    ParseException,
    ProxyException,
    CircuitOpenException,
)
from resilience.error_classifier import (
    ErrorType,
    RecoveryAction,
    classify_error,
    get_recovery_info,
    ERROR_RECOVERY_MAP,
)
from resilience.retry import (
    _calculate_delay,
    retry_with_backoff,
    retry_with_backoff_async,
)


# =============================================================================
# Exception Tests
# =============================================================================


class TestScraperExceptions:
    """Test the exception hierarchy."""

    def test_scraper_exception_is_base(self):
        """Test that ScraperException is the base for all others."""
        assert issubclass(NetworkException, ScraperException)
        assert issubclass(RateLimitException, ScraperException)
        assert issubclass(BlockedException, ScraperException)
        assert issubclass(ParseException, ScraperException)
        assert issubclass(ProxyException, ScraperException)
        assert issubclass(CircuitOpenException, ScraperException)

    def test_rate_limit_exception_has_retry_after(self):
        """Test RateLimitException stores retry_after value."""
        exc = RateLimitException(retry_after=120)
        assert exc.retry_after == 120
        assert "Rate limit exceeded" in str(exc)

    def test_rate_limit_exception_default_retry_after(self):
        """Test RateLimitException has default retry_after of 60."""
        exc = RateLimitException()
        assert exc.retry_after == 60

    def test_rate_limit_exception_custom_message(self):
        """Test RateLimitException accepts custom message."""
        exc = RateLimitException(message="Too many requests", retry_after=90)
        assert str(exc) == "Too many requests"
        assert exc.retry_after == 90


# =============================================================================
# Error Classifier Tests
# =============================================================================


class TestErrorClassifier:
    """Test error classification logic."""

    # HTTP status code classification
    def test_classify_http_429(self):
        """Test that HTTP 429 is classified as rate limit."""
        exc = Exception("Rate limited")
        result = classify_error(exc, http_status=429)
        assert result == ErrorType.HTTP_RATE_LIMIT

    def test_classify_http_403(self):
        """Test that HTTP 403 is classified as blocked."""
        exc = Exception("Forbidden")
        result = classify_error(exc, http_status=403)
        assert result == ErrorType.HTTP_BLOCKED

    def test_classify_http_404(self):
        """Test that HTTP 404 is classified as not found."""
        exc = Exception("Not found")
        result = classify_error(exc, http_status=404)
        assert result == ErrorType.NOT_FOUND

    def test_classify_http_500(self):
        """Test that HTTP 5xx is classified as server error."""
        exc = Exception("Server error")
        result = classify_error(exc, http_status=500)
        assert result == ErrorType.HTTP_SERVER_ERROR

    def test_classify_http_503(self):
        """Test that HTTP 503 is classified as server error."""
        exc = Exception("Service unavailable")
        result = classify_error(exc, http_status=503)
        assert result == ErrorType.HTTP_SERVER_ERROR

    def test_classify_http_400(self):
        """Test that HTTP 400 is classified as client error."""
        exc = Exception("Bad request")
        result = classify_error(exc, http_status=400)
        assert result == ErrorType.HTTP_CLIENT_ERROR

    # Timeout errors
    def test_classify_timeout_error(self):
        """Test that TimeoutError is classified as network timeout."""
        exc = TimeoutError("Connection timed out")
        result = classify_error(exc)
        assert result == ErrorType.NETWORK_TIMEOUT

    def test_classify_timeout_by_name(self):
        """Test timeout classification by exception name."""
        # Create custom exception with timeout in name
        class ConnectTimeout(Exception):
            pass

        exc = ConnectTimeout("Timed out")
        result = classify_error(exc)
        assert result == ErrorType.NETWORK_TIMEOUT

    def test_classify_timeout_by_message(self):
        """Test timeout classification by message content."""
        exc = Exception("Request timeout after 30 seconds")
        result = classify_error(exc)
        assert result == ErrorType.NETWORK_TIMEOUT

    # Connection errors
    def test_classify_connection_error(self):
        """Test that ConnectionError is classified as network connection."""
        exc = ConnectionError("Failed to connect")
        result = classify_error(exc)
        assert result == ErrorType.NETWORK_CONNECTION

    def test_classify_connection_refused(self):
        """Test that ConnectionRefusedError is classified correctly."""
        exc = ConnectionRefusedError("Connection refused")
        result = classify_error(exc)
        assert result == ErrorType.NETWORK_CONNECTION

    # Proxy/SSL errors
    def test_classify_ssl_error(self):
        """Test that SSL errors are classified as proxy error."""
        class SSLError(Exception):
            pass

        exc = SSLError("SSL certificate verification failed")
        result = classify_error(exc)
        assert result == ErrorType.PROXY_ERROR

    def test_classify_proxy_error_by_message(self):
        """Test proxy error classification by message."""
        exc = Exception("Proxy connection failed")
        result = classify_error(exc)
        assert result == ErrorType.PROXY_ERROR

    # Parse errors
    def test_classify_json_decode_error(self):
        """Test JSONDecodeError is classified as parse error."""
        import json

        try:
            json.loads("invalid json")
        except json.JSONDecodeError as exc:
            result = classify_error(exc)
            assert result == ErrorType.PARSE_ERROR

    def test_classify_attribute_error(self):
        """Test AttributeError is classified as parse error."""
        exc = AttributeError("'NoneType' object has no attribute 'text'")
        result = classify_error(exc)
        assert result == ErrorType.PARSE_ERROR

    def test_classify_key_error(self):
        """Test KeyError is classified as parse error."""
        exc = KeyError("missing_key")
        result = classify_error(exc)
        assert result == ErrorType.PARSE_ERROR

    # Unknown errors
    def test_classify_unknown(self):
        """Test that unrecognized errors are classified as unknown."""
        exc = ValueError("Some random error")
        result = classify_error(exc)
        assert result == ErrorType.UNKNOWN


class TestRecoveryInfo:
    """Test recovery information lookup."""

    def test_get_recovery_info_timeout(self):
        """Test recovery info for network timeout."""
        action, is_recoverable, max_retries = get_recovery_info(
            ErrorType.NETWORK_TIMEOUT
        )
        assert action == RecoveryAction.RETRY_WITH_BACKOFF
        assert is_recoverable is True
        assert max_retries == 3

    def test_get_recovery_info_not_found(self):
        """Test recovery info for not found error."""
        action, is_recoverable, max_retries = get_recovery_info(ErrorType.NOT_FOUND)
        assert action == RecoveryAction.SKIP
        assert is_recoverable is False
        assert max_retries == 0

    def test_get_recovery_info_rate_limit(self):
        """Test recovery info for rate limit."""
        action, is_recoverable, max_retries = get_recovery_info(
            ErrorType.HTTP_RATE_LIMIT
        )
        assert action == RecoveryAction.RETRY_WITH_BACKOFF
        assert is_recoverable is True
        assert max_retries == 5

    def test_get_recovery_info_blocked(self):
        """Test recovery info for blocked error."""
        action, is_recoverable, max_retries = get_recovery_info(ErrorType.HTTP_BLOCKED)
        assert action == RecoveryAction.CIRCUIT_BREAK
        assert is_recoverable is True
        assert max_retries == 2

    def test_get_recovery_info_proxy(self):
        """Test recovery info for proxy error."""
        action, is_recoverable, max_retries = get_recovery_info(ErrorType.PROXY_ERROR)
        assert action == RecoveryAction.RETRY_WITH_PROXY
        assert is_recoverable is True
        assert max_retries == 5

    def test_get_recovery_info_parse_error(self):
        """Test recovery info for parse error."""
        action, is_recoverable, max_retries = get_recovery_info(ErrorType.PARSE_ERROR)
        assert action == RecoveryAction.MANUAL_REVIEW
        assert is_recoverable is False
        assert max_retries == 0

    def test_get_recovery_info_unknown_defaults(self):
        """Test that unknown error types return conservative defaults."""
        # Create a mock ErrorType that's not in the map
        # Since we can't add to enum, test with UNKNOWN which should be in map
        action, is_recoverable, max_retries = get_recovery_info(ErrorType.UNKNOWN)
        assert action == RecoveryAction.MANUAL_REVIEW
        assert is_recoverable is False
        assert max_retries == 0


# =============================================================================
# Retry Decorator Tests
# =============================================================================


class TestCalculateDelay:
    """Test the delay calculation function."""

    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        # Attempt 0: base * 2^0 = 2 * 1 = 2
        delay = _calculate_delay(attempt=0, base=2.0, max_delay=60.0, jitter=0.0)
        assert delay == 2.0

        # Attempt 1: base * 2^1 = 2 * 2 = 4
        delay = _calculate_delay(attempt=1, base=2.0, max_delay=60.0, jitter=0.0)
        assert delay == 4.0

        # Attempt 2: base * 2^2 = 2 * 4 = 8
        delay = _calculate_delay(attempt=2, base=2.0, max_delay=60.0, jitter=0.0)
        assert delay == 8.0

    def test_calculate_delay_capped(self):
        """Test that delay is capped at max_delay."""
        # Attempt 10: 2 * 2^10 = 2048, should be capped at 60
        delay = _calculate_delay(attempt=10, base=2.0, max_delay=60.0, jitter=0.0)
        assert delay == 60.0

    def test_calculate_delay_has_jitter(self):
        """Test that jitter adds randomness to delay."""
        # With jitter, delay should be between base_delay and base_delay * (1 + jitter)
        delays = [
            _calculate_delay(attempt=0, base=2.0, max_delay=60.0, jitter=0.5)
            for _ in range(10)
        ]

        # All delays should be >= 2.0 (base delay)
        assert all(d >= 2.0 for d in delays)

        # All delays should be <= 2.0 + (2.0 * 0.5) = 3.0
        assert all(d <= 3.0 for d in delays)

        # With 10 samples, at least some should be different
        assert len(set(delays)) > 1


class TestRetryDecorator:
    """Test the sync retry decorator."""

    @patch("resilience.retry.time.sleep")
    def test_retry_success_first_attempt(self, mock_sleep):
        """Test successful execution on first attempt - no retries."""

        @retry_with_backoff(max_attempts=3)
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"
        mock_sleep.assert_not_called()

    @patch("resilience.retry.time.sleep")
    def test_retry_success_after_failures(self, mock_sleep):
        """Test successful execution after some failures."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=5, base_delay=1.0, jitter_factor=0.0)
        def flaky_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise TimeoutError("Timeout")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert attempt_count["count"] == 3
        # Should have slept twice (after 1st and 2nd failure)
        assert mock_sleep.call_count == 2

    @patch("resilience.retry.time.sleep")
    def test_retry_exhausted_raises(self, mock_sleep):
        """Test that exception is raised after all retries exhausted."""

        @retry_with_backoff(max_attempts=3)
        def always_fails():
            raise TimeoutError("Always fails")

        with pytest.raises(TimeoutError, match="Always fails"):
            always_fails()

        # Should have slept twice (after 1st and 2nd failure, not after 3rd)
        assert mock_sleep.call_count == 2

    @patch("resilience.retry.time.sleep")
    def test_retry_skips_non_retryable(self, mock_sleep):
        """Test that non-retryable errors are raised immediately."""

        @retry_with_backoff(max_attempts=5)
        def raises_404():
            # Simulate a 404 which should not be retried
            raise ParseException("Parse failed")

        # ParseException is not recoverable, should raise immediately
        # However, the decorator catches Exception by default
        # We need to check if it classifies it correctly
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=5)
        def raises_non_retryable():
            attempt_count["count"] += 1
            # KeyError is classified as PARSE_ERROR which is not recoverable
            raise KeyError("missing_field")

        with pytest.raises(KeyError):
            raises_non_retryable()

        # Should not retry non-recoverable errors
        assert attempt_count["count"] == 1
        mock_sleep.assert_not_called()

    @patch("resilience.retry.time.sleep")
    def test_retry_with_on_retry_callback(self, mock_sleep):
        """Test that on_retry callback is called."""
        callback_calls = []

        def on_retry_cb(attempt, exception):
            callback_calls.append((attempt, str(exception)))

        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=3, on_retry=on_retry_cb, jitter_factor=0.0)
        def flaky_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise TimeoutError(f"Timeout {attempt_count['count']}")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 0  # First retry
        assert "Timeout 1" in callback_calls[0][1]

    @patch("resilience.retry.time.sleep")
    def test_retry_respects_max_attempts(self, mock_sleep):
        """Test that retry respects max_attempts parameter."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=2)
        def always_fails():
            attempt_count["count"] += 1
            raise TimeoutError("Fail")

        with pytest.raises(TimeoutError):
            always_fails()

        assert attempt_count["count"] == 2
        assert mock_sleep.call_count == 1  # Only one sleep between 2 attempts

    @patch("resilience.retry.time.sleep")
    def test_retry_with_specific_exceptions(self, mock_sleep):
        """Test retry only catches specified exception types."""

        @retry_with_backoff(max_attempts=3, exceptions=(TimeoutError,))
        def raises_value_error():
            raise ValueError("Not a timeout")

        # ValueError is not in the exceptions tuple, should raise immediately
        with pytest.raises(ValueError):
            raises_value_error()

        mock_sleep.assert_not_called()

    @patch("resilience.retry.time.sleep")
    def test_retry_delay_progression(self, mock_sleep):
        """Test that delays follow exponential backoff."""

        @retry_with_backoff(
            max_attempts=4, base_delay=1.0, max_delay=100.0, jitter_factor=0.0
        )
        def always_fails():
            raise TimeoutError("Fail")

        with pytest.raises(TimeoutError):
            always_fails()

        # Check sleep was called with increasing delays
        # Attempt 0: 1.0 * 2^0 = 1.0
        # Attempt 1: 1.0 * 2^1 = 2.0
        # Attempt 2: 1.0 * 2^2 = 4.0
        assert mock_sleep.call_count == 3
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0


class TestRetryDecoratorAsync:
    """Test the async retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_async_works(self):
        """Test async retry decorator works correctly."""

        @retry_with_backoff_async(max_attempts=3, jitter_factor=0.0)
        async def async_func():
            return "async success"

        result = await async_func()
        assert result == "async success"

    @pytest.mark.asyncio
    @patch("resilience.retry.asyncio.sleep", new_callable=lambda: MagicMock())
    async def test_retry_async_retries_on_failure(self, mock_sleep):
        """Test async retry retries on failures."""
        # Make sleep a coroutine
        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep

        attempt_count = {"count": 0}

        @retry_with_backoff_async(max_attempts=3, base_delay=1.0, jitter_factor=0.0)
        async def flaky_async_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise TimeoutError("Async timeout")
            return "success"

        result = await flaky_async_func()
        assert result == "success"
        assert attempt_count["count"] == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("resilience.retry.asyncio.sleep", new_callable=lambda: MagicMock())
    async def test_retry_async_exhausted_raises(self, mock_sleep):
        """Test async retry raises after exhausting attempts."""

        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep

        @retry_with_backoff_async(max_attempts=2)
        async def always_fails_async():
            raise TimeoutError("Always fails")

        with pytest.raises(TimeoutError):
            await always_fails_async()

        assert mock_sleep.call_count == 1

    @pytest.mark.asyncio
    @patch("resilience.retry.asyncio.sleep", new_callable=lambda: MagicMock())
    async def test_retry_async_skips_non_retryable(self, mock_sleep):
        """Test async retry skips non-retryable errors."""

        async def async_sleep(_):
            pass

        mock_sleep.side_effect = async_sleep

        attempt_count = {"count": 0}

        @retry_with_backoff_async(max_attempts=5)
        async def raises_non_retryable_async():
            attempt_count["count"] += 1
            # KeyError is not recoverable
            raise KeyError("missing_field")

        with pytest.raises(KeyError):
            await raises_non_retryable_async()

        assert attempt_count["count"] == 1
        mock_sleep.assert_not_called()


# =============================================================================
# Integration Tests
# =============================================================================


class TestRetryIntegration:
    """Integration tests combining multiple components."""

    @patch("resilience.retry.time.sleep")
    def test_retry_with_rate_limit_exception(self, mock_sleep):
        """Test retry with custom exception that's recoverable."""
        attempt_count = {"count": 0}

        @retry_with_backoff(
            max_attempts=3, exceptions=(Exception,), jitter_factor=0.0
        )
        def rate_limited_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                # TimeoutError is recoverable (classified as NETWORK_TIMEOUT)
                raise TimeoutError("Network timeout")
            return "success"

        result = rate_limited_func()
        assert result == "success"
        assert mock_sleep.call_count == 1

    @patch("resilience.retry.time.sleep")
    def test_error_classification_in_retry(self, mock_sleep):
        """Test that error classification works within retry decorator."""

        @retry_with_backoff(max_attempts=3, jitter_factor=0.0)
        def classified_error_func():
            # ConnectionError should be classified as NETWORK_CONNECTION
            # which is recoverable
            raise ConnectionError("Network failure")

        with pytest.raises(ConnectionError):
            classified_error_func()

        # Should retry recoverable errors
        assert mock_sleep.call_count == 2
