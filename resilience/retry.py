"""Retry decorators with exponential backoff for resilience."""

import asyncio
import functools
import random
import time
from typing import Callable, Optional, Tuple, Type

from loguru import logger

from .error_classifier import RecoveryAction, classify_error, get_recovery_info

# Import settings with fallback defaults
try:
    from config.settings import (
        RETRY_BASE_DELAY,
        RETRY_JITTER_FACTOR,
        RETRY_MAX_ATTEMPTS,
        RETRY_MAX_DELAY,
    )
except ImportError:
    RETRY_MAX_ATTEMPTS = 5
    RETRY_BASE_DELAY = 2.0
    RETRY_MAX_DELAY = 60.0
    RETRY_JITTER_FACTOR = 0.5


def _calculate_delay(
    attempt: int, base: float, max_delay: float, jitter: float
) -> float:
    """
    Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base: Base delay in seconds
        max_delay: Maximum delay cap in seconds
        jitter: Jitter factor (0.0 to 1.0)

    Returns:
        Calculated delay in seconds
    """
    # Exponential backoff: base * (2 ** attempt)
    delay = base * (2**attempt)

    # Cap at max_delay
    delay = min(delay, max_delay)

    # Add jitter: delay * jitter * random.random()
    jitter_amount = delay * jitter * random.random()

    return delay + jitter_amount


def retry_with_backoff(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    jitter_factor: float = RETRY_JITTER_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Sync retry decorator with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for backoff calculation
        max_delay: Maximum delay cap in seconds
        jitter_factor: Factor for random jitter (0.0 to 1.0)
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback called on each retry with (attempt, exception)

    Usage:
        @retry_with_backoff(max_attempts=5)
        def fetch_page(url):
            return requests.get(url)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_type = classify_error(e)
                    recovery_action, is_recoverable, _ = get_recovery_info(error_type)

                    # Don't retry non-recoverable error types - raise immediately
                    if not is_recoverable or recovery_action == RecoveryAction.SKIP:
                        raise

                    if attempt < max_attempts - 1:
                        delay = _calculate_delay(
                            attempt, base_delay, max_delay, jitter_factor
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: "
                            f"{error_type.value} - {e}. Waiting {delay:.2f}s"
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator


def retry_with_backoff_async(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    jitter_factor: float = RETRY_JITTER_FACTOR,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Async retry decorator with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for backoff calculation
        max_delay: Maximum delay cap in seconds
        jitter_factor: Factor for random jitter (0.0 to 1.0)
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback called on each retry with (attempt, exception)

    Usage:
        @retry_with_backoff_async(max_attempts=5)
        async def fetch_page(url):
            async with aiohttp.ClientSession() as session:
                return await session.get(url)
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    error_type = classify_error(e)
                    recovery_action, is_recoverable, _ = get_recovery_info(error_type)

                    # Don't retry non-recoverable error types - raise immediately
                    if not is_recoverable or recovery_action == RecoveryAction.SKIP:
                        raise

                    if attempt < max_attempts - 1:
                        delay = _calculate_delay(
                            attempt, base_delay, max_delay, jitter_factor
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: "
                            f"{error_type.value} - {e}. Waiting {delay:.2f}s"
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator
