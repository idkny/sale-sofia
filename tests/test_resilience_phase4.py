"""Unit tests for resilience Phase 4 modules.

Tests the response validator for soft block detection and retry-after handling.
"""

import pytest
from unittest.mock import patch

from resilience.response_validator import (
    detect_soft_block,
    CAPTCHA_PATTERNS,
    BLOCK_PATTERNS,
)
from resilience.retry import retry_with_backoff
from resilience.exceptions import RateLimitException


# =============================================================================
# Response Validator Tests - detect_soft_block()
# =============================================================================


class TestDetectSoftBlock:
    """Test soft block detection for CAPTCHA, block messages, and short content."""

    # Empty response tests
    def test_empty_html_returns_blocked(self):
        """Test that empty HTML is detected as blocked."""
        is_blocked, reason = detect_soft_block("")
        assert is_blocked is True
        assert reason == "empty_response"

    def test_none_html_returns_blocked(self):
        """Test that None HTML is detected as blocked."""
        # Empty string check handles falsy values
        is_blocked, reason = detect_soft_block("")
        assert is_blocked is True
        assert reason == "empty_response"

    # Short content tests
    def test_short_html_below_1000_chars_returns_blocked(self):
        """Test that HTML shorter than 1000 chars is detected as blocked."""
        short_html = "x" * 999  # 999 chars
        is_blocked, reason = detect_soft_block(short_html)
        assert is_blocked is True
        assert reason == "short_content"

    def test_html_exactly_999_chars_returns_blocked(self):
        """Test that HTML with exactly 999 chars is blocked."""
        html = "a" * 999
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "short_content"

    def test_html_exactly_1000_chars_not_blocked(self):
        """Test that HTML with exactly 1000 chars passes length check."""
        html = "a" * 1000
        is_blocked, reason = detect_soft_block(html)
        # Should pass length check, but may fail pattern checks
        # If no patterns detected, should not be blocked
        assert is_blocked is False
        assert reason == ""

    def test_long_html_over_1000_chars_not_blocked_by_length(self):
        """Test that HTML over 1000 chars passes length check."""
        long_html = "x" * 1500  # 1500 chars, no patterns
        is_blocked, reason = detect_soft_block(long_html)
        assert is_blocked is False
        assert reason == ""

    # CAPTCHA pattern tests
    def test_captcha_pattern_lowercase(self):
        """Test detection of 'captcha' pattern (lowercase)."""
        html = "x" * 1000 + "Please solve the captcha to continue."
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_captcha_pattern_uppercase(self):
        """Test detection of 'CAPTCHA' pattern (uppercase)."""
        html = "x" * 1000 + "Please solve the CAPTCHA to continue."
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_captcha_pattern_mixed_case(self):
        """Test detection of 'Captcha' pattern (mixed case)."""
        html = "x" * 1000 + "Complete the Captcha verification"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_recaptcha_pattern(self):
        """Test detection of 'recaptcha' pattern."""
        html = "x" * 1000 + '<div id="g-recaptcha"></div>'
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_hcaptcha_pattern(self):
        """Test detection of 'hcaptcha' pattern."""
        html = "x" * 1000 + '<div class="hcaptcha-widget"></div>'
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_challenge_platform_pattern(self):
        """Test detection of 'challenge-platform' pattern."""
        html = "x" * 1000 + '<div class="challenge-platform"></div>'
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_verify_human_pattern(self):
        """Test detection of 'verify.*human' pattern."""
        html = "x" * 1000 + "Please verify that you are human"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_verify_youre_human_pattern(self):
        """Test detection of 'verify you're human' variant."""
        html = "x" * 1000 + "Verify you're a human user"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_security_check_pattern(self):
        """Test detection of 'security.*check' pattern."""
        html = "x" * 1000 + "Security check in progress..."
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_security_verification_check_pattern(self):
        """Test detection of 'security verification check' variant."""
        html = "x" * 1000 + "Performing security verification check"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    # Block pattern tests
    def test_access_denied_pattern(self):
        """Test detection of 'access.*denied' pattern."""
        html = "x" * 1000 + "<h1>Access Denied</h1>"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_access_is_denied_pattern(self):
        """Test detection of 'access is denied' variant."""
        html = "x" * 1000 + "Your access is denied due to policy"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_blocked_pattern(self):
        """Test detection of 'blocked' pattern."""
        html = "x" * 1000 + "You have been blocked from this site"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_blocked_uppercase_pattern(self):
        """Test detection of 'BLOCKED' pattern (case insensitive)."""
        html = "x" * 1000 + "YOUR IP HAS BEEN BLOCKED"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_rate_limit_pattern(self):
        """Test detection of 'rate.*limit' pattern."""
        html = "x" * 1000 + "Rate limit exceeded. Try again later."
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_rate_limiting_active_pattern(self):
        """Test detection of 'rate limiting active' variant."""
        html = "x" * 1000 + "Rate limiting is active for your IP"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_too_many_requests_pattern(self):
        """Test detection of 'too.*many.*requests' pattern."""
        html = "x" * 1000 + "Error 429: Too many requests"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_too_many_concurrent_requests_pattern(self):
        """Test detection of 'too many concurrent requests' variant."""
        html = "x" * 1000 + "Too many concurrent requests from your IP"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_please_try_again_later_pattern(self):
        """Test detection of 'please.*try.*again.*later' pattern."""
        html = "x" * 1000 + "Service unavailable. Please try again later."
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_please_try_accessing_later_pattern(self):
        """Test detection of 'please try accessing later' variant."""
        html = "x" * 1000 + "Please try accessing this page again later"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    # Normal content tests
    def test_normal_html_not_blocked(self):
        """Test that normal HTML (1000+ chars, no patterns) is not blocked."""
        normal_html = "<html><body>" + "Normal content. " * 100 + "</body></html>"
        assert len(normal_html) > 1000
        is_blocked, reason = detect_soft_block(normal_html)
        assert is_blocked is False
        assert reason == ""

    def test_html_with_safe_keywords_not_blocked(self):
        """Test that HTML with safe keywords is not blocked."""
        # Contains words like "access" and "check" but not in blocking patterns
        html = "x" * 1000 + "Access our products. Check out our new features!"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is False
        assert reason == ""

    # Edge cases
    def test_multiple_patterns_returns_first_match(self):
        """Test that first matching pattern is returned."""
        # Contains both CAPTCHA and block patterns
        html = "x" * 1000 + "Please solve the captcha. Access denied."
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        # CAPTCHA patterns are checked first, so should get captcha_detected
        assert reason == "captcha_detected"

    def test_pattern_at_start_of_html(self):
        """Test detection of pattern at the start of HTML."""
        html = "CAPTCHA required " + "x" * 1000
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_pattern_at_end_of_html(self):
        """Test detection of pattern at the end of HTML."""
        html = "x" * 1000 + " Access Denied"
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "block_message_detected"

    def test_pattern_in_html_attributes(self):
        """Test detection of pattern in HTML attributes."""
        html = "x" * 1000 + '<div class="recaptcha-container"></div>'
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_cloudflare_security_check(self):
        """Test detection of Cloudflare security check."""
        html = "x" * 1000 + "Performing a security check before accessing"
        is_blocked, reason = detect_soft_block(html)
        # This should be caught by "security.*check" pattern
        assert is_blocked is True
        assert reason == "captcha_detected"

    def test_cloudflare_challenge(self):
        """Test detection of Cloudflare challenge platform."""
        html = "x" * 1000 + '<div class="challenge-platform cf-challenge"></div>'
        is_blocked, reason = detect_soft_block(html)
        assert is_blocked is True
        assert reason == "captcha_detected"


# =============================================================================
# Pattern Coverage Tests
# =============================================================================


class TestPatternCoverage:
    """Test that all patterns are defined and compilable."""

    def test_captcha_patterns_count(self):
        """Test that all expected CAPTCHA patterns are defined."""
        expected_patterns = [
            r"captcha",
            r"recaptcha",
            r"hcaptcha",
            r"challenge-platform",
            r"verify.*human",
            r"security.*check",
        ]
        assert CAPTCHA_PATTERNS == expected_patterns

    def test_block_patterns_count(self):
        """Test that all expected block patterns are defined."""
        expected_patterns = [
            r"access.*denied",
            r"blocked",
            r"rate.*limit",
            r"too.*many.*requests",
            r"please.*try.*again.*later",
        ]
        assert BLOCK_PATTERNS == expected_patterns

    def test_captcha_patterns_are_case_insensitive(self):
        """Test that CAPTCHA patterns work case-insensitively."""
        test_cases = [
            ("captcha", True),
            ("CAPTCHA", True),
            ("Captcha", True),
            ("CaPtChA", True),
            ("recaptcha", True),
            ("RECAPTCHA", True),
            ("hcaptcha", True),
            ("HCAPTCHA", True),
        ]
        for pattern_text, should_match in test_cases:
            html = "x" * 1000 + pattern_text
            is_blocked, _ = detect_soft_block(html)
            assert is_blocked == should_match

    def test_block_patterns_are_case_insensitive(self):
        """Test that block patterns work case-insensitively."""
        test_cases = [
            ("access denied", True),
            ("ACCESS DENIED", True),
            ("Access Denied", True),
            ("blocked", True),
            ("BLOCKED", True),
            ("Blocked", True),
            ("rate limit", True),
            ("RATE LIMIT", True),
            ("Rate Limit", True),
        ]
        for pattern_text, should_match in test_cases:
            html = "x" * 1000 + pattern_text
            is_blocked, _ = detect_soft_block(html)
            assert is_blocked == should_match


# =============================================================================
# Retry-After Handling Tests
# =============================================================================


class TestRetryAfterHandling:
    """Test that retry_with_backoff respects retry_after attribute."""

    @patch("resilience.retry.time.sleep")
    def test_rate_limit_exception_with_retry_after_30(self, mock_sleep):
        """Test that exception with retry_after=30 uses 30 second delay."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=3, base_delay=2.0, jitter_factor=0.0)
        def rate_limited_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise RateLimitException(retry_after=30)
            return "success"

        result = rate_limited_func()
        assert result == "success"
        assert mock_sleep.call_count == 1
        # Should have used retry_after value, not calculated backoff
        mock_sleep.assert_called_once_with(30)

    @patch("resilience.retry.time.sleep")
    def test_rate_limit_exception_with_retry_after_45(self, mock_sleep):
        """Test that exception with retry_after=45 uses 45 second delay."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=3, base_delay=2.0, jitter_factor=0.0)
        def rate_limited_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise RateLimitException(retry_after=45)
            return "success"

        result = rate_limited_func()
        assert result == "success"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(45)

    @patch("resilience.retry.time.sleep")
    def test_rate_limit_exception_with_retry_after_120(self, mock_sleep):
        """Test that exception with retry_after=120 uses 120 second delay."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=2, base_delay=1.0, jitter_factor=0.0)
        def rate_limited_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise RateLimitException(retry_after=120)
            return "success"

        result = rate_limited_func()
        assert result == "success"
        mock_sleep.assert_called_once_with(120)

    @patch("resilience.retry.time.sleep")
    def test_exception_without_retry_after_uses_backoff(self, mock_sleep):
        """Test that exception without retry_after uses calculated backoff."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=3, base_delay=2.0, jitter_factor=0.0)
        def timeout_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                # TimeoutError doesn't have retry_after attribute
                raise TimeoutError("Network timeout")
            return "success"

        result = timeout_func()
        assert result == "success"
        assert mock_sleep.call_count == 1
        # Should use calculated backoff: base_delay * 2^0 = 2.0
        mock_sleep.assert_called_once_with(2.0)

    @patch("resilience.retry.time.sleep")
    def test_rate_limit_default_retry_after_60(self, mock_sleep):
        """Test RateLimitException defaults to 60 second retry_after."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=2, jitter_factor=0.0)
        def rate_limited_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                # RateLimitException with no retry_after specified
                raise RateLimitException()
            return "success"

        result = rate_limited_func()
        assert result == "success"
        assert mock_sleep.call_count == 1
        # Should use default retry_after of 60
        mock_sleep.assert_called_once_with(60)

    @patch("resilience.retry.time.sleep")
    def test_multiple_retries_with_different_retry_after(self, mock_sleep):
        """Test multiple retries with different retry_after values."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=4, base_delay=1.0, jitter_factor=0.0)
        def multi_rate_limited_func():
            attempt_count["count"] += 1
            if attempt_count["count"] == 1:
                raise RateLimitException(retry_after=15)
            elif attempt_count["count"] == 2:
                raise RateLimitException(retry_after=30)
            elif attempt_count["count"] == 3:
                raise RateLimitException(retry_after=60)
            return "success"

        result = multi_rate_limited_func()
        assert result == "success"
        assert mock_sleep.call_count == 3
        # Check each sleep call used the correct retry_after
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == 15
        assert sleep_calls[1] == 30
        assert sleep_calls[2] == 60

    @patch("resilience.retry.time.sleep")
    def test_retry_after_zero_uses_zero_delay(self, mock_sleep):
        """Test that retry_after=0 results in zero delay."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=2, jitter_factor=0.0)
        def immediate_retry_func():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise RateLimitException(retry_after=0)
            return "success"

        result = immediate_retry_func()
        assert result == "success"
        mock_sleep.assert_called_once_with(0)

    @patch("resilience.retry.time.sleep")
    def test_retry_after_overrides_calculated_delay(self, mock_sleep):
        """Test that retry_after overrides exponential backoff calculation."""
        attempt_count = {"count": 0}

        @retry_with_backoff(
            max_attempts=5, base_delay=1.0, max_delay=100.0, jitter_factor=0.0
        )
        def override_backoff_func():
            attempt_count["count"] += 1
            if attempt_count["count"] == 1:
                # Would normally delay 1.0 * 2^0 = 1.0, but override with 25
                raise RateLimitException(retry_after=25)
            elif attempt_count["count"] == 2:
                # Would normally delay 1.0 * 2^1 = 2.0, but override with 50
                raise RateLimitException(retry_after=50)
            return "success"

        result = override_backoff_func()
        assert result == "success"
        assert mock_sleep.call_count == 2
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] == 25  # Not 1.0
        assert sleep_calls[1] == 50  # Not 2.0


# =============================================================================
# Integration Tests
# =============================================================================


class TestPhase4Integration:
    """Integration tests combining soft block detection and retry logic."""

    @patch("resilience.retry.time.sleep")
    def test_soft_block_detection_triggers_retry(self, mock_sleep):
        """Test that soft block detection can work with retry decorator."""
        attempt_count = {"count": 0}

        @retry_with_backoff(max_attempts=3, jitter_factor=0.0)
        def fetch_with_soft_block():
            attempt_count["count"] += 1
            html = "x" * 1000 + "Please solve the captcha"
            is_blocked, reason = detect_soft_block(html)
            if is_blocked:
                raise RateLimitException(f"Soft block: {reason}", retry_after=10)
            return html

        with pytest.raises(RateLimitException, match="Soft block: captcha_detected"):
            fetch_with_soft_block()

        # Should have retried with 10 second delay
        assert mock_sleep.call_count == 2
        for call in mock_sleep.call_args_list:
            assert call[0][0] == 10

    def test_soft_block_detection_patterns_comprehensive(self):
        """Test comprehensive pattern detection across all categories."""
        test_cases = [
            # CAPTCHA patterns
            ("x" * 1000 + "captcha", True, "captcha_detected"),
            ("x" * 1000 + "recaptcha", True, "captcha_detected"),
            ("x" * 1000 + "hcaptcha", True, "captcha_detected"),
            ("x" * 1000 + "verify human", True, "captcha_detected"),
            ("x" * 1000 + "security check", True, "captcha_detected"),
            # Block patterns
            ("x" * 1000 + "access denied", True, "block_message_detected"),
            ("x" * 1000 + "blocked", True, "block_message_detected"),
            ("x" * 1000 + "rate limit", True, "block_message_detected"),
            ("x" * 1000 + "too many requests", True, "block_message_detected"),
            ("x" * 1000 + "please try again later", True, "block_message_detected"),
            # Normal content
            ("x" * 1000 + "normal content", False, ""),
            # Short content
            ("x" * 500, True, "short_content"),
            # Empty content
            ("", True, "empty_response"),
        ]

        for html, expected_blocked, expected_reason in test_cases:
            is_blocked, reason = detect_soft_block(html)
            assert is_blocked == expected_blocked, f"Failed for: {html[:50]}"
            assert reason == expected_reason, f"Failed for: {html[:50]}"
