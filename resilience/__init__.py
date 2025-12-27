"""
Resilience module for scraper error handling and recovery.

This module provides:
- Exception hierarchy for scraper errors
- Error classification and recovery strategies
- Retry decorators with exponential backoff
- Circuit breaker for domain protection
- Rate limiting per domain
- Checkpoint/recovery for crash resilience
- Soft block detection

Spec: docs/specs/112_SCRAPER_RESILIENCE.md
"""

# Phase 1: Foundation (exceptions, error classifier, retry)
from .exceptions import (
    ScraperException,
    NetworkException,
    RateLimitException,
    BlockedException,
    ParseException,
    ProxyException,
    CircuitOpenException,
)

from .error_classifier import (
    ErrorType,
    RecoveryAction,
    ERROR_RECOVERY_MAP,
    classify_error,
    get_recovery_info,
)

# from .retry import (
#     retry_with_backoff,
#     retry_with_backoff_async,
# )

# Phase 2: Domain Protection (circuit breaker, rate limiter)
from .circuit_breaker import (
    CircuitState,
    DomainCircuitStatus,
    DomainCircuitBreaker,
    get_circuit_breaker,
)

from .rate_limiter import (
    DomainRateLimiter,
    get_rate_limiter,
)

# Phase 3: Session Recovery (checkpoint)
from .checkpoint import (
    CheckpointManager,
)

# Phase 4: Detection (response validator)
from .response_validator import (
    detect_soft_block,
    CAPTCHA_PATTERNS,
    BLOCK_PATTERNS,
)

__all__ = [
    # Exceptions
    "ScraperException",
    "NetworkException",
    "RateLimitException",
    "BlockedException",
    "ParseException",
    "ProxyException",
    "CircuitOpenException",
    # Error classifier
    "ErrorType",
    "RecoveryAction",
    "ERROR_RECOVERY_MAP",
    "classify_error",
    "get_recovery_info",
    # Retry decorators
    # "retry_with_backoff",
    # "retry_with_backoff_async",
    # Circuit breaker
    "CircuitState",
    "DomainCircuitStatus",
    "DomainCircuitBreaker",
    "get_circuit_breaker",
    # Rate limiter
    "DomainRateLimiter",
    "get_rate_limiter",
    # Checkpoint
    "CheckpointManager",
    # Response validator
    "detect_soft_block",
    "CAPTCHA_PATTERNS",
    "BLOCK_PATTERNS",
]
