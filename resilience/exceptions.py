"""Exception hierarchy for the scraper resilience module."""

try:
    from config.settings import RATE_LIMIT_DEFAULT_RETRY_AFTER
except ImportError:
    RATE_LIMIT_DEFAULT_RETRY_AFTER = 60


class ScraperException(Exception):
    """Base exception for all scraper errors."""

    pass


class NetworkException(ScraperException):
    """Network-level errors (connection, timeout)."""

    pass


class RateLimitException(ScraperException):
    """Rate limit exceeded (429 response)."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = RATE_LIMIT_DEFAULT_RETRY_AFTER):
        super().__init__(message)
        self.retry_after = retry_after


class BlockedException(ScraperException):
    """Blocked by website (403, CAPTCHA)."""

    pass


class ParseException(ScraperException):
    """HTML/data parsing failed."""

    pass


class ProxyException(ScraperException):
    """Proxy-related error."""

    pass


class CircuitOpenException(ScraperException):
    """Circuit breaker is open for this domain."""

    pass
