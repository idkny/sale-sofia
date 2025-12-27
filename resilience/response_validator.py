"""Response validation for soft block detection (CAPTCHA, block messages, short content)."""

import re

from loguru import logger

try:
    from config.settings import MIN_CONTENT_LENGTH
except ImportError:
    MIN_CONTENT_LENGTH = 1000

# Regex patterns for CAPTCHA detection (case-insensitive)
CAPTCHA_PATTERNS = [
    r"captcha",
    r"recaptcha",
    r"hcaptcha",
    r"challenge-platform",
    r"verify.*human",
    r"security.*check",
]

# Regex patterns for block messages (case-insensitive)
BLOCK_PATTERNS = [
    r"access.*denied",
    r"blocked",
    r"rate.*limit",
    r"too.*many.*requests",
    r"please.*try.*again.*later",
]

# Compile patterns for performance
_COMPILED_CAPTCHA = [re.compile(p, re.IGNORECASE) for p in CAPTCHA_PATTERNS]
_COMPILED_BLOCK = [re.compile(p, re.IGNORECASE) for p in BLOCK_PATTERNS]


def detect_soft_block(html: str) -> tuple[bool, str]:
    """
    Check HTML for signs of being soft-blocked.

    Detects:
    - CAPTCHA challenges
    - Block/access denied messages
    - Suspiciously short content

    Args:
        html: The HTML content to check.

    Returns:
        Tuple of (is_blocked, reason). If not blocked, reason is empty string.
    """
    if not html:
        return True, "empty_response"

    # Check content length first (fast check)
    if len(html) < MIN_CONTENT_LENGTH:
        logger.debug(f"Suspiciously short content: {len(html)} bytes")
        return True, "short_content"

    # Check for CAPTCHA patterns
    for pattern in _COMPILED_CAPTCHA:
        if pattern.search(html):
            logger.debug(f"CAPTCHA pattern detected: {pattern.pattern}")
            return True, "captcha_detected"

    # Check for block patterns
    for pattern in _COMPILED_BLOCK:
        if pattern.search(html):
            logger.debug(f"Block pattern detected: {pattern.pattern}")
            return True, "block_message_detected"

    return False, ""
