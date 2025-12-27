"""Retry decorator for SQLite database busy errors."""

import functools
import random
import sqlite3
import time
from typing import Callable

from loguru import logger

# Import settings with fallback defaults
try:
    from config.settings import (
        SQLITE_BUSY_DELAY,
        SQLITE_BUSY_MAX_DELAY,
        SQLITE_BUSY_RETRIES,
    )
except ImportError:
    SQLITE_BUSY_RETRIES = 3
    SQLITE_BUSY_DELAY = 0.5
    SQLITE_BUSY_MAX_DELAY = 5.0


def _calculate_delay(attempt: int, base: float, max_delay: float) -> float:
    """
    Calculate delay with exponential backoff and jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        base: Base delay in seconds
        max_delay: Maximum delay cap in seconds

    Returns:
        Calculated delay in seconds
    """
    # Exponential backoff: base * (2 ** attempt)
    delay = base * (2**attempt)

    # Cap at max_delay
    delay = min(delay, max_delay)

    # Add jitter (0-50% of delay)
    jitter = delay * 0.5 * random.random()

    return delay + jitter


def retry_on_busy(
    max_attempts: int = SQLITE_BUSY_RETRIES,
    base_delay: float = SQLITE_BUSY_DELAY,
    max_delay: float = SQLITE_BUSY_MAX_DELAY,
):
    """
    Retry decorator for SQLite "database is locked" errors.

    Args:
        max_attempts: Maximum retry attempts (default from settings)
        base_delay: Base delay in seconds for backoff
        max_delay: Maximum delay cap in seconds

    Usage:
        @retry_on_busy()
        def save_listing(listing):
            ...
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" not in str(e):
                        raise  # Not a busy error, re-raise immediately

                    last_exception = e

                    if attempt < max_attempts - 1:
                        delay = _calculate_delay(attempt, base_delay, max_delay)
                        logger.warning(
                            f"Database busy, retry {attempt + 1}/{max_attempts} "
                            f"for {func.__name__}: waiting {delay:.2f}s"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: "
                            f"database is locked"
                        )

            raise last_exception

        return wrapper

    return decorator
