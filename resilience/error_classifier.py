"""Error classification for resilience module.

Classifies exceptions and HTTP status codes into error types,
and provides recovery actions for each type.

Reference: Spec 112 Section 1.2
"""

from enum import Enum
from typing import Optional, Tuple

try:
    from config.settings import (
        ERROR_RETRY_BLOCKED,
        ERROR_RETRY_NETWORK,
        ERROR_RETRY_PROXY,
        ERROR_RETRY_RATE_LIMIT,
        ERROR_RETRY_SERVER,
    )
except ImportError:
    ERROR_RETRY_NETWORK = 3
    ERROR_RETRY_RATE_LIMIT = 5
    ERROR_RETRY_BLOCKED = 2
    ERROR_RETRY_SERVER = 3
    ERROR_RETRY_PROXY = 5


class ErrorType(Enum):
    """Classification of scraper errors.

    Each type has a different retry/recovery strategy.
    Simplified to ~10 essential types for sale-sofia.
    """

    # Network errors - transient, retry with backoff
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_CONNECTION = "network_connection"

    # HTTP errors - classify by status code
    HTTP_RATE_LIMIT = "http_rate_limit"  # 429
    HTTP_BLOCKED = "http_blocked"  # 403, captcha detected
    HTTP_SERVER_ERROR = "http_server_error"  # 5xx
    HTTP_CLIENT_ERROR = "http_client_error"  # 4xx (except 429, 403, 404)

    # Content errors
    PARSE_ERROR = "parse_error"  # HTML/JSON parsing failed
    NOT_FOUND = "not_found"  # 404 - skip permanently

    # Infrastructure errors
    PROXY_ERROR = "proxy_error"  # Proxy-related issues

    # Catch-all
    UNKNOWN = "unknown"


class RecoveryAction(Enum):
    """What to do when an error occurs.

    Orchestrator uses this to decide next steps.
    """

    RETRY_IMMEDIATE = "retry_immediate"  # Retry now (e.g., DNS hiccup)
    RETRY_WITH_BACKOFF = "retry_with_backoff"  # Exponential backoff
    RETRY_WITH_PROXY = "retry_with_proxy"  # Rotate proxy and retry
    SKIP = "skip"  # Don't retry, mark failed
    CIRCUIT_BREAK = "circuit_break"  # Stop requests to domain
    MANUAL_REVIEW = "manual_review"  # Log for human review


# Mapping: ErrorType -> (RecoveryAction, is_recoverable, max_retries)
ERROR_RECOVERY_MAP: dict[ErrorType, Tuple[RecoveryAction, bool, int]] = {
    # Network - recoverable with backoff
    ErrorType.NETWORK_TIMEOUT: (RecoveryAction.RETRY_WITH_BACKOFF, True, ERROR_RETRY_NETWORK),
    ErrorType.NETWORK_CONNECTION: (RecoveryAction.RETRY_WITH_BACKOFF, True, ERROR_RETRY_NETWORK),

    # HTTP - depends on code
    ErrorType.HTTP_RATE_LIMIT: (RecoveryAction.RETRY_WITH_BACKOFF, True, ERROR_RETRY_RATE_LIMIT),
    ErrorType.HTTP_BLOCKED: (RecoveryAction.CIRCUIT_BREAK, True, ERROR_RETRY_BLOCKED),
    ErrorType.HTTP_SERVER_ERROR: (RecoveryAction.RETRY_WITH_BACKOFF, True, ERROR_RETRY_SERVER),
    ErrorType.HTTP_CLIENT_ERROR: (RecoveryAction.SKIP, False, 0),

    # Content - not recoverable by retry
    ErrorType.PARSE_ERROR: (RecoveryAction.MANUAL_REVIEW, False, 0),
    ErrorType.NOT_FOUND: (RecoveryAction.SKIP, False, 0),

    # Proxy - rotate and retry
    ErrorType.PROXY_ERROR: (RecoveryAction.RETRY_WITH_PROXY, True, ERROR_RETRY_PROXY),

    # Unknown - conservative
    ErrorType.UNKNOWN: (RecoveryAction.MANUAL_REVIEW, False, 0),
}


def classify_error(
    exception: Exception,
    http_status: Optional[int] = None,
) -> ErrorType:
    """Classify an exception into an ErrorType.

    Checks HTTP status first (if provided), then exception type.

    Args:
        exception: The exception that was raised
        http_status: HTTP status code if available

    Returns:
        ErrorType indicating how the error should be handled
    """
    # HTTP status takes precedence
    if http_status is not None:
        if http_status == 429:
            return ErrorType.HTTP_RATE_LIMIT
        if http_status == 403:
            return ErrorType.HTTP_BLOCKED
        if http_status == 404:
            return ErrorType.NOT_FOUND
        if 500 <= http_status < 600:
            return ErrorType.HTTP_SERVER_ERROR
        if 400 <= http_status < 500:
            return ErrorType.HTTP_CLIENT_ERROR

    # Exception-based classification
    exc_name = type(exception).__name__

    # Custom exception types (check by name to avoid circular imports)
    if exc_name == "RateLimitException":
        return ErrorType.HTTP_RATE_LIMIT
    if exc_name == "BlockedException":
        return ErrorType.HTTP_BLOCKED
    if exc_name == "NetworkException":
        return ErrorType.NETWORK_CONNECTION
    if exc_name == "ProxyException":
        return ErrorType.PROXY_ERROR
    if exc_name == "ParseException":
        return ErrorType.PARSE_ERROR

    # Timeout errors
    if isinstance(exception, TimeoutError):
        return ErrorType.NETWORK_TIMEOUT
    if exc_name in ("TimeoutError", "ConnectTimeout", "ReadTimeout", "AsyncTimeoutError"):
        return ErrorType.NETWORK_TIMEOUT
    if "timeout" in str(exception).lower():
        return ErrorType.NETWORK_TIMEOUT

    # Connection errors
    if isinstance(exception, ConnectionError):
        return ErrorType.NETWORK_CONNECTION
    if exc_name in ("ConnectionError", "ConnectionRefusedError", "ConnectionResetError"):
        return ErrorType.NETWORK_CONNECTION

    # SSL/Proxy errors
    if "SSL" in exc_name or "ssl" in str(exception).lower():
        return ErrorType.PROXY_ERROR
    if "proxy" in str(exception).lower():
        return ErrorType.PROXY_ERROR

    # Parse errors
    if exc_name == "JSONDecodeError":
        return ErrorType.PARSE_ERROR
    if isinstance(exception, (AttributeError, KeyError)):
        return ErrorType.PARSE_ERROR
    exc_module = type(exception).__module__
    if "lxml" in exc_module or "bs4" in exc_module or "html" in exc_module.lower():
        return ErrorType.PARSE_ERROR

    return ErrorType.UNKNOWN


def get_recovery_info(error_type: ErrorType) -> Tuple[RecoveryAction, bool, int]:
    """Get recovery information for an error type.

    Args:
        error_type: The classified error type

    Returns:
        Tuple of (recovery_action, is_recoverable, max_retries)
    """
    return ERROR_RECOVERY_MAP.get(
        error_type,
        (RecoveryAction.MANUAL_REVIEW, False, 0),
    )
